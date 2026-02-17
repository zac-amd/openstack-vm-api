"""VM service layer containing business logic."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import VMNotFoundException, VMStateException
from app.core.openstack_client import BaseOpenStackClient, get_openstack_client
from app.models.vm import VM, VMState
from app.schemas.vm import (
    PaginationParams,
    VMCreate,
    VMUpdate,
    VMResponse,
    VMListResponse,
    VMActionResponse,
    RebootType,
)

logger = logging.getLogger(__name__)


class VMService:
    """Service class for VM lifecycle operations."""

    def __init__(
        self,
        session: AsyncSession,
        openstack_client: Optional[BaseOpenStackClient] = None,
    ) -> None:
        """Initialize VM service.

        Args:
            session: Database session
            openstack_client: OpenStack client (uses default if not provided)
        """
        self.session = session
        self.openstack = openstack_client or get_openstack_client()

    async def create_vm(self, vm_data: VMCreate) -> VMResponse:
        """Create a new VM.

        Args:
            vm_data: VM creation data

        Returns:
            Created VM details
        """
        # Validate flavor and image exist
        flavor = await self.openstack.get_flavor(vm_data.flavor_id)
        await self.openstack.get_image(vm_data.image_id)

        # Create VM in database first (in BUILDING state)
        vm = VM(
            name=vm_data.name,
            flavor_id=vm_data.flavor_id,
            image_id=vm_data.image_id,
            description=vm_data.description,
            key_name=vm_data.key_name,
            user_data=vm_data.user_data,
            state=VMState.BUILDING,
            vcpus=flavor.get("vcpus"),
            memory_mb=flavor.get("memory_mb"),
            disk_gb=flavor.get("disk_gb"),
        )
        self.session.add(vm)
        await self.session.flush()

        try:
            # Create VM in OpenStack
            os_server = await self.openstack.create_server(
                name=vm_data.name,
                flavor_id=vm_data.flavor_id,
                image_id=vm_data.image_id,
                network_id=vm_data.network_id,
                key_name=vm_data.key_name,
                user_data=vm_data.user_data,
                security_groups=vm_data.security_groups,
                availability_zone=vm_data.availability_zone,
                metadata=vm_data.metadata,
            )

            # Update VM with OpenStack details
            vm.openstack_id = os_server["id"]
            vm.state = VMState.ACTIVE
            vm.ip_address = os_server.get("ip_address")
            vm.floating_ip = os_server.get("floating_ip")
            vm.launched_at = datetime.utcnow()

            logger.info(f"Created VM {vm.uuid} ({vm.name})")

        except Exception as e:
            # Mark VM as error state if OpenStack creation fails
            vm.state = VMState.ERROR
            vm.state_description = str(e)
            logger.error(f"Failed to create VM in OpenStack: {e}")
            raise

        await self.session.commit()
        await self.session.refresh(vm)

        return VMResponse.model_validate(vm)

    async def get_vm(self, vm_uuid: str) -> VMResponse:
        """Get VM by UUID.

        Args:
            vm_uuid: VM UUID

        Returns:
            VM details

        Raises:
            VMNotFoundException: If VM not found
        """
        vm = await self._get_vm_by_uuid(vm_uuid)
        return VMResponse.model_validate(vm)

    async def list_vms(
        self,
        pagination: PaginationParams,
        state: Optional[VMState] = None,
        name_filter: Optional[str] = None,
    ) -> VMListResponse:
        """List VMs with pagination and filtering.

        Args:
            pagination: Pagination parameters
            state: Filter by VM state
            name_filter: Filter by name (contains)

        Returns:
            Paginated list of VMs
        """
        # Build query
        query = select(VM).where(VM.state != VMState.DELETED)

        if state:
            query = query.where(VM.state == state)

        if name_filter:
            query = query.where(VM.name.ilike(f"%{name_filter}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query) or 0

        # Apply pagination
        query = (
            query.order_by(VM.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )

        result = await self.session.execute(query)
        vms = result.scalars().all()

        # Calculate total pages
        pages = (total + pagination.page_size - 1) // pagination.page_size

        return VMListResponse(
            items=[VMResponse.model_validate(vm) for vm in vms],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )

    async def update_vm(self, vm_uuid: str, vm_data: VMUpdate) -> VMResponse:
        """Update VM details.

        Args:
            vm_uuid: VM UUID
            vm_data: Update data

        Returns:
            Updated VM details
        """
        vm = await self._get_vm_by_uuid(vm_uuid)

        if vm_data.name is not None:
            vm.name = vm_data.name

        if vm_data.description is not None:
            vm.description = vm_data.description

        await self.session.commit()
        await self.session.refresh(vm)

        logger.info(f"Updated VM {vm.uuid}")
        return VMResponse.model_validate(vm)

    async def delete_vm(self, vm_uuid: str) -> VMActionResponse:
        """Delete/terminate a VM.

        Args:
            vm_uuid: VM UUID

        Returns:
            Action response
        """
        vm = await self._get_vm_by_uuid(vm_uuid)
        previous_state = vm.state

        if not vm.can_delete:
            raise VMStateException(
                vm_id=vm_uuid,
                current_state=vm.state.value,
                action="delete",
            )

        # Delete from OpenStack if it exists there
        if vm.openstack_id:
            try:
                await self.openstack.delete_server(vm.openstack_id)
            except Exception as e:
                logger.warning(f"Failed to delete VM from OpenStack: {e}")
                # Continue with local deletion even if OpenStack fails

        # Mark as deleted
        vm.state = VMState.DELETED
        vm.terminated_at = datetime.utcnow()

        await self.session.commit()
        logger.info(f"Deleted VM {vm.uuid}")

        return VMActionResponse(
            vm_uuid=vm_uuid,
            action="delete",
            status="success",
            message=f"VM {vm.name} has been deleted",
            previous_state=previous_state,
            current_state=vm.state,
        )

    async def start_vm(self, vm_uuid: str) -> VMActionResponse:
        """Start a stopped VM.

        Args:
            vm_uuid: VM UUID

        Returns:
            Action response
        """
        vm = await self._get_vm_by_uuid(vm_uuid)
        previous_state = vm.state

        if not vm.can_start:
            raise VMStateException(
                vm_id=vm_uuid,
                current_state=vm.state.value,
                action="start",
                message=f"VM must be in stopped state to start (current: {vm.state.value})",
            )

        # Start in OpenStack
        if vm.openstack_id:
            await self.openstack.start_server(vm.openstack_id)

        vm.state = VMState.ACTIVE
        await self.session.commit()

        logger.info(f"Started VM {vm.uuid}")

        return VMActionResponse(
            vm_uuid=vm_uuid,
            action="start",
            status="success",
            message=f"VM {vm.name} has been started",
            previous_state=previous_state,
            current_state=vm.state,
        )

    async def stop_vm(self, vm_uuid: str) -> VMActionResponse:
        """Stop a running VM.

        Args:
            vm_uuid: VM UUID

        Returns:
            Action response
        """
        vm = await self._get_vm_by_uuid(vm_uuid)
        previous_state = vm.state

        if not vm.can_stop:
            raise VMStateException(
                vm_id=vm_uuid,
                current_state=vm.state.value,
                action="stop",
                message=f"VM must be running to stop (current: {vm.state.value})",
            )

        # Stop in OpenStack
        if vm.openstack_id:
            await self.openstack.stop_server(vm.openstack_id)

        vm.state = VMState.SHUTOFF
        await self.session.commit()

        logger.info(f"Stopped VM {vm.uuid}")

        return VMActionResponse(
            vm_uuid=vm_uuid,
            action="stop",
            status="success",
            message=f"VM {vm.name} has been stopped",
            previous_state=previous_state,
            current_state=vm.state,
        )

    async def reboot_vm(
        self, vm_uuid: str, reboot_type: RebootType = RebootType.SOFT
    ) -> VMActionResponse:
        """Reboot a running VM.

        Args:
            vm_uuid: VM UUID
            reboot_type: SOFT or HARD reboot

        Returns:
            Action response
        """
        vm = await self._get_vm_by_uuid(vm_uuid)
        previous_state = vm.state

        if not vm.can_reboot:
            raise VMStateException(
                vm_id=vm_uuid,
                current_state=vm.state.value,
                action="reboot",
                message=f"VM must be running to reboot (current: {vm.state.value})",
            )

        # Set transitional state
        vm.state = VMState.REBOOT if reboot_type == RebootType.SOFT else VMState.HARD_REBOOT
        await self.session.commit()

        # Reboot in OpenStack
        if vm.openstack_id:
            await self.openstack.reboot_server(vm.openstack_id, reboot_type.value)

        # Set back to active
        vm.state = VMState.ACTIVE
        await self.session.commit()

        logger.info(f"Rebooted VM {vm.uuid} ({reboot_type.value})")

        return VMActionResponse(
            vm_uuid=vm_uuid,
            action=f"reboot_{reboot_type.value.lower()}",
            status="success",
            message=f"VM {vm.name} has been rebooted ({reboot_type.value})",
            previous_state=previous_state,
            current_state=vm.state,
        )

    async def sync_vm_state(self, vm_uuid: str) -> VMResponse:
        """Sync VM state from OpenStack.

        Args:
            vm_uuid: VM UUID

        Returns:
            Updated VM details
        """
        vm = await self._get_vm_by_uuid(vm_uuid)

        if not vm.openstack_id:
            logger.warning(f"VM {vm_uuid} has no OpenStack ID, cannot sync")
            return VMResponse.model_validate(vm)

        try:
            os_server = await self.openstack.get_server(vm.openstack_id)

            # Map OpenStack status to VMState
            status_mapping = {
                "ACTIVE": VMState.ACTIVE,
                "SHUTOFF": VMState.SHUTOFF,
                "BUILDING": VMState.BUILDING,
                "ERROR": VMState.ERROR,
                "PAUSED": VMState.PAUSED,
                "SUSPENDED": VMState.SUSPENDED,
                "REBOOT": VMState.REBOOT,
                "HARD_REBOOT": VMState.HARD_REBOOT,
                "RESIZE": VMState.RESIZE,
                "VERIFY_RESIZE": VMState.VERIFY_RESIZE,
                "DELETED": VMState.DELETED,
                "SOFT_DELETED": VMState.SOFT_DELETED,
            }

            os_status = os_server.get("status", "").upper()
            new_state = status_mapping.get(os_status, VMState.ERROR)

            vm.state = new_state
            vm.ip_address = os_server.get("ip_address")
            vm.floating_ip = os_server.get("floating_ip")

            await self.session.commit()
            await self.session.refresh(vm)

            logger.info(f"Synced VM {vm_uuid} state: {new_state.value}")

        except Exception as e:
            logger.error(f"Failed to sync VM {vm_uuid} state: {e}")
            raise

        return VMResponse.model_validate(vm)

    async def _get_vm_by_uuid(self, vm_uuid: str) -> VM:
        """Get VM by UUID from database.

        Args:
            vm_uuid: VM UUID

        Returns:
            VM model instance

        Raises:
            VMNotFoundException: If VM not found
        """
        query = select(VM).where(
            VM.uuid == vm_uuid,
            VM.state != VMState.DELETED,
        )
        result = await self.session.execute(query)
        vm = result.scalar_one_or_none()

        if vm is None:
            raise VMNotFoundException(vm_uuid)

        return vm


def get_vm_service(session: AsyncSession) -> VMService:
    """Factory function to create VM service."""
    return VMService(session=session)
