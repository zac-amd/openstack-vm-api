"""VM lifecycle management endpoints."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_api_key
from app.database import get_session
from app.models.vm import VMState
from app.schemas.vm import (
    VMCreate,
    VMUpdate,
    VMResponse,
    VMListResponse,
    VMActionResponse,
    VMRebootRequest,
    PaginationParams,
    RebootType,
)
from app.services.vm_service import VMService

router = APIRouter()

# Type aliases for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_session)]
APIKeyDep = Annotated[str, Depends(verify_api_key)]


def get_vm_service(session: SessionDep) -> VMService:
    """Dependency to get VM service."""
    return VMService(session=session)


VMServiceDep = Annotated[VMService, Depends(get_vm_service)]


@router.post(
    "",
    response_model=VMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new VM",
    description="Create a new virtual machine with the specified configuration.",
)
async def create_vm(
    vm_data: VMCreate,
    service: VMServiceDep,
    api_key: APIKeyDep,
) -> VMResponse:
    """Create a new virtual machine.

    - **name**: VM name (required)
    - **flavor_id**: Size/flavor ID (required)
    - **image_id**: OS image ID (required)
    - **description**: Optional description
    - **key_name**: SSH key pair name
    - **network_id**: Network to attach
    - **security_groups**: List of security groups
    """
    return await service.create_vm(vm_data)


@router.get(
    "",
    response_model=VMListResponse,
    summary="List all VMs",
    description="Get a paginated list of all virtual machines.",
)
async def list_vms(
    service: VMServiceDep,
    api_key: APIKeyDep,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    state: Optional[VMState] = Query(default=None, description="Filter by state"),
    name: Optional[str] = Query(default=None, description="Filter by name (contains)"),
) -> VMListResponse:
    """List all virtual machines with pagination and optional filtering.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **state**: Filter by VM state (optional)
    - **name**: Filter by name containing this string (optional)
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await service.list_vms(
        pagination=pagination,
        state=state,
        name_filter=name,
    )


@router.get(
    "/{vm_uuid}",
    response_model=VMResponse,
    summary="Get VM details",
    description="Get detailed information about a specific VM.",
)
async def get_vm(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMResponse:
    """Get details of a specific virtual machine by UUID."""
    return await service.get_vm(vm_uuid)


@router.patch(
    "/{vm_uuid}",
    response_model=VMResponse,
    summary="Update VM",
    description="Update VM details (name, description).",
)
async def update_vm(
    vm_data: VMUpdate,
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMResponse:
    """Update VM details.

    - **name**: New VM name (optional)
    - **description**: New description (optional)
    """
    return await service.update_vm(vm_uuid, vm_data)


@router.delete(
    "/{vm_uuid}",
    response_model=VMActionResponse,
    summary="Delete VM",
    description="Delete/terminate a virtual machine.",
)
async def delete_vm(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMActionResponse:
    """Delete a virtual machine.

    This action is irreversible. The VM will be terminated and removed.
    """
    return await service.delete_vm(vm_uuid)


@router.post(
    "/{vm_uuid}/start",
    response_model=VMActionResponse,
    summary="Start VM",
    description="Start a stopped virtual machine.",
)
async def start_vm(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMActionResponse:
    """Start a stopped virtual machine.

    The VM must be in STOPPED or SHUTOFF state.
    """
    return await service.start_vm(vm_uuid)


@router.post(
    "/{vm_uuid}/stop",
    response_model=VMActionResponse,
    summary="Stop VM",
    description="Stop a running virtual machine.",
)
async def stop_vm(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMActionResponse:
    """Stop a running virtual machine.

    The VM must be in ACTIVE or RUNNING state.
    """
    return await service.stop_vm(vm_uuid)


@router.post(
    "/{vm_uuid}/reboot",
    response_model=VMActionResponse,
    summary="Reboot VM",
    description="Reboot a running virtual machine.",
)
async def reboot_vm(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
    reboot_request: VMRebootRequest = None,
) -> VMActionResponse:
    """Reboot a running virtual machine.

    - **reboot_type**: SOFT (graceful) or HARD (force) reboot
    """
    reboot_type = RebootType.SOFT
    if reboot_request and reboot_request.reboot_type:
        reboot_type = reboot_request.reboot_type

    return await service.reboot_vm(vm_uuid, reboot_type)


@router.post(
    "/{vm_uuid}/sync",
    response_model=VMResponse,
    summary="Sync VM state",
    description="Synchronize VM state from OpenStack.",
)
async def sync_vm_state(
    service: VMServiceDep,
    api_key: APIKeyDep,
    vm_uuid: str = Path(..., description="VM UUID"),
) -> VMResponse:
    """Synchronize VM state from OpenStack.

    This fetches the current state from OpenStack and updates the local database.
    """
    return await service.sync_vm_state(vm_uuid)
