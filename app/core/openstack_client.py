"""OpenStack client wrapper with mock support."""

import logging
import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

from app.config import Settings, get_settings
from app.core.exceptions import (
    OpenStackConnectionException,
    OpenStackException,
    ResourceNotFoundException,
)

logger = logging.getLogger(__name__)


class BaseOpenStackClient(ABC):
    """Abstract base class for OpenStack client."""

    @abstractmethod
    async def create_server(
        self,
        name: str,
        flavor_id: str,
        image_id: str,
        network_id: Optional[str] = None,
        key_name: Optional[str] = None,
        user_data: Optional[str] = None,
        security_groups: Optional[list[str]] = None,
        availability_zone: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a new server/VM."""
        pass

    @abstractmethod
    async def get_server(self, server_id: str) -> dict[str, Any]:
        """Get server details."""
        pass

    @abstractmethod
    async def delete_server(self, server_id: str) -> bool:
        """Delete a server."""
        pass

    @abstractmethod
    async def start_server(self, server_id: str) -> bool:
        """Start a stopped server."""
        pass

    @abstractmethod
    async def stop_server(self, server_id: str) -> bool:
        """Stop a running server."""
        pass

    @abstractmethod
    async def reboot_server(self, server_id: str, reboot_type: str = "SOFT") -> bool:
        """Reboot a server."""
        pass

    @abstractmethod
    async def list_flavors(self) -> list[dict[str, Any]]:
        """List available flavors."""
        pass

    @abstractmethod
    async def get_flavor(self, flavor_id: str) -> dict[str, Any]:
        """Get flavor details."""
        pass

    @abstractmethod
    async def list_images(self) -> list[dict[str, Any]]:
        """List available images."""
        pass

    @abstractmethod
    async def get_image(self, image_id: str) -> dict[str, Any]:
        """Get image details."""
        pass

    @abstractmethod
    async def check_connection(self) -> bool:
        """Check if connection to OpenStack is working."""
        pass


class MockOpenStackClient(BaseOpenStackClient):
    """Mock OpenStack client for testing without real OpenStack."""

    # Mock data storage
    _servers: dict[str, dict[str, Any]] = {}

    # Predefined mock flavors
    MOCK_FLAVORS = [
        {
            "id": "m1.tiny",
            "name": "Tiny",
            "vcpus": 1,
            "memory_mb": 512,
            "disk_gb": 1,
            "ephemeral_gb": 0,
            "swap_mb": 0,
            "is_public": True,
            "description": "Tiny instance for testing",
        },
        {
            "id": "m1.small",
            "name": "Small",
            "vcpus": 1,
            "memory_mb": 2048,
            "disk_gb": 20,
            "ephemeral_gb": 0,
            "swap_mb": 0,
            "is_public": True,
            "description": "Small instance for light workloads",
        },
        {
            "id": "m1.medium",
            "name": "Medium",
            "vcpus": 2,
            "memory_mb": 4096,
            "disk_gb": 40,
            "ephemeral_gb": 0,
            "swap_mb": 0,
            "is_public": True,
            "description": "Medium instance for general workloads",
        },
        {
            "id": "m1.large",
            "name": "Large",
            "vcpus": 4,
            "memory_mb": 8192,
            "disk_gb": 80,
            "ephemeral_gb": 0,
            "swap_mb": 0,
            "is_public": True,
            "description": "Large instance for demanding workloads",
        },
        {
            "id": "m1.xlarge",
            "name": "Extra Large",
            "vcpus": 8,
            "memory_mb": 16384,
            "disk_gb": 160,
            "ephemeral_gb": 0,
            "swap_mb": 0,
            "is_public": True,
            "description": "Extra large instance for heavy workloads",
        },
    ]

    # Predefined mock images
    MOCK_IMAGES = [
        {
            "id": "ubuntu-22.04",
            "name": "Ubuntu 22.04 LTS",
            "status": "active",
            "size_bytes": 2361393152,
            "min_disk_gb": 8,
            "min_memory_mb": 512,
            "os_distro": "ubuntu",
            "os_version": "22.04",
            "architecture": "x86_64",
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
            "description": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
        },
        {
            "id": "ubuntu-20.04",
            "name": "Ubuntu 20.04 LTS",
            "status": "active",
            "size_bytes": 2147483648,
            "min_disk_gb": 8,
            "min_memory_mb": 512,
            "os_distro": "ubuntu",
            "os_version": "20.04",
            "architecture": "x86_64",
            "created_at": datetime(2023, 6, 1, 8, 0, 0),
            "description": "Ubuntu 20.04 LTS (Focal Fossa)",
        },
        {
            "id": "centos-9",
            "name": "CentOS Stream 9",
            "status": "active",
            "size_bytes": 1932735283,
            "min_disk_gb": 10,
            "min_memory_mb": 1024,
            "os_distro": "centos",
            "os_version": "9",
            "architecture": "x86_64",
            "created_at": datetime(2024, 2, 1, 12, 0, 0),
            "description": "CentOS Stream 9",
        },
        {
            "id": "debian-12",
            "name": "Debian 12 (Bookworm)",
            "status": "active",
            "size_bytes": 2048000000,
            "min_disk_gb": 8,
            "min_memory_mb": 512,
            "os_distro": "debian",
            "os_version": "12",
            "architecture": "x86_64",
            "created_at": datetime(2024, 1, 20, 14, 0, 0),
            "description": "Debian 12 (Bookworm) stable",
        },
        {
            "id": "windows-2022",
            "name": "Windows Server 2022",
            "status": "active",
            "size_bytes": 15032385536,
            "min_disk_gb": 40,
            "min_memory_mb": 2048,
            "os_distro": "windows",
            "os_version": "2022",
            "architecture": "x86_64",
            "created_at": datetime(2024, 1, 10, 9, 0, 0),
            "description": "Windows Server 2022 Datacenter",
        },
    ]

    def _generate_ip(self) -> str:
        """Generate a random private IP address."""
        return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"

    async def create_server(
        self,
        name: str,
        flavor_id: str,
        image_id: str,
        network_id: Optional[str] = None,
        key_name: Optional[str] = None,
        user_data: Optional[str] = None,
        security_groups: Optional[list[str]] = None,
        availability_zone: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a mock server."""
        # Validate flavor exists
        flavor = await self.get_flavor(flavor_id)

        # Validate image exists
        await self.get_image(image_id)

        server_id = str(uuid.uuid4())
        now = datetime.utcnow()

        server = {
            "id": server_id,
            "name": name,
            "status": "ACTIVE",
            "flavor_id": flavor_id,
            "image_id": image_id,
            "vcpus": flavor["vcpus"],
            "memory_mb": flavor["memory_mb"],
            "disk_gb": flavor["disk_gb"],
            "ip_address": self._generate_ip(),
            "floating_ip": None,
            "key_name": key_name,
            "created_at": now,
            "updated_at": now,
            "launched_at": now,
            "metadata": metadata or {},
        }

        self._servers[server_id] = server
        logger.info(f"Mock: Created server {server_id} ({name})")
        return server

    async def get_server(self, server_id: str) -> dict[str, Any]:
        """Get mock server details."""
        if server_id not in self._servers:
            raise ResourceNotFoundException("Server", server_id)
        return self._servers[server_id]

    async def delete_server(self, server_id: str) -> bool:
        """Delete a mock server."""
        if server_id not in self._servers:
            raise ResourceNotFoundException("Server", server_id)

        del self._servers[server_id]
        logger.info(f"Mock: Deleted server {server_id}")
        return True

    async def start_server(self, server_id: str) -> bool:
        """Start a mock server."""
        server = await self.get_server(server_id)
        server["status"] = "ACTIVE"
        server["updated_at"] = datetime.utcnow()
        logger.info(f"Mock: Started server {server_id}")
        return True

    async def stop_server(self, server_id: str) -> bool:
        """Stop a mock server."""
        server = await self.get_server(server_id)
        server["status"] = "SHUTOFF"
        server["updated_at"] = datetime.utcnow()
        logger.info(f"Mock: Stopped server {server_id}")
        return True

    async def reboot_server(self, server_id: str, reboot_type: str = "SOFT") -> bool:
        """Reboot a mock server."""
        server = await self.get_server(server_id)
        server["status"] = "ACTIVE"
        server["updated_at"] = datetime.utcnow()
        logger.info(f"Mock: Rebooted server {server_id} ({reboot_type})")
        return True

    async def list_flavors(self) -> list[dict[str, Any]]:
        """List mock flavors."""
        return self.MOCK_FLAVORS.copy()

    async def get_flavor(self, flavor_id: str) -> dict[str, Any]:
        """Get mock flavor details."""
        for flavor in self.MOCK_FLAVORS:
            if flavor["id"] == flavor_id:
                return flavor
        raise ResourceNotFoundException("Flavor", flavor_id)

    async def list_images(self) -> list[dict[str, Any]]:
        """List mock images."""
        return self.MOCK_IMAGES.copy()

    async def get_image(self, image_id: str) -> dict[str, Any]:
        """Get mock image details."""
        for image in self.MOCK_IMAGES:
            if image["id"] == image_id:
                return image
        raise ResourceNotFoundException("Image", image_id)

    async def check_connection(self) -> bool:
        """Mock connection check always succeeds."""
        return True


class RealOpenStackClient(BaseOpenStackClient):
    """Real OpenStack client using openstacksdk."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the real OpenStack client."""
        self.settings = settings
        self._connection = None

    def _get_connection(self) -> Any:
        """Get or create OpenStack connection."""
        if self._connection is None:
            try:
                import openstack

                # Configure connection from settings
                if self.settings.os_application_credential_id:
                    # Use application credentials
                    self._connection = openstack.connect(
                        auth_url=self.settings.os_auth_url,
                        application_credential_id=self.settings.os_application_credential_id,
                        application_credential_secret=self.settings.os_application_credential_secret,
                        region_name=self.settings.os_region_name,
                    )
                else:
                    # Use username/password
                    self._connection = openstack.connect(
                        auth_url=self.settings.os_auth_url,
                        project_name=self.settings.os_project_name,
                        project_domain_name=self.settings.os_project_domain_name,
                        username=self.settings.os_username,
                        password=self.settings.os_password,
                        user_domain_name=self.settings.os_user_domain_name,
                        region_name=self.settings.os_region_name,
                    )
            except Exception as e:
                logger.error(f"Failed to connect to OpenStack: {e}")
                raise OpenStackConnectionException(
                    message=f"Failed to connect to OpenStack: {str(e)}"
                )

        return self._connection

    def _server_to_dict(self, server: Any) -> dict[str, Any]:
        """Convert OpenStack server object to dictionary."""
        return {
            "id": server.id,
            "name": server.name,
            "status": server.status,
            "flavor_id": server.flavor.get("id") if server.flavor else None,
            "image_id": server.image.get("id") if server.image else None,
            "ip_address": self._get_server_ip(server),
            "floating_ip": self._get_floating_ip(server),
            "key_name": server.key_name,
            "created_at": server.created_at,
            "updated_at": server.updated_at,
            "launched_at": server.launched_at,
            "metadata": server.metadata or {},
        }

    def _get_server_ip(self, server: Any) -> Optional[str]:
        """Extract private IP from server addresses."""
        if server.addresses:
            for network, addresses in server.addresses.items():
                for addr in addresses:
                    if addr.get("OS-EXT-IPS:type") == "fixed":
                        return addr.get("addr")
        return None

    def _get_floating_ip(self, server: Any) -> Optional[str]:
        """Extract floating IP from server addresses."""
        if server.addresses:
            for network, addresses in server.addresses.items():
                for addr in addresses:
                    if addr.get("OS-EXT-IPS:type") == "floating":
                        return addr.get("addr")
        return None

    async def create_server(
        self,
        name: str,
        flavor_id: str,
        image_id: str,
        network_id: Optional[str] = None,
        key_name: Optional[str] = None,
        user_data: Optional[str] = None,
        security_groups: Optional[list[str]] = None,
        availability_zone: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """Create a server in OpenStack."""
        try:
            conn = self._get_connection()

            # Build server creation kwargs
            kwargs: dict[str, Any] = {
                "name": name,
                "flavor": flavor_id,
                "image": image_id,
                "wait": True,
                "timeout": 300,
            }

            if network_id:
                kwargs["network"] = network_id
            if key_name:
                kwargs["key_name"] = key_name
            if user_data:
                kwargs["userdata"] = user_data
            if security_groups:
                kwargs["security_groups"] = security_groups
            if availability_zone:
                kwargs["availability_zone"] = availability_zone
            if metadata:
                kwargs["meta"] = metadata

            server = conn.compute.create_server(**kwargs)
            server = conn.compute.wait_for_server(server)

            logger.info(f"OpenStack: Created server {server.id} ({name})")
            return self._server_to_dict(server)

        except Exception as e:
            logger.error(f"Failed to create server: {e}")
            raise OpenStackException(
                message=f"Failed to create server: {str(e)}",
                openstack_error=str(e),
            )

    async def get_server(self, server_id: str) -> dict[str, Any]:
        """Get server details from OpenStack."""
        try:
            conn = self._get_connection()
            server = conn.compute.get_server(server_id)
            if server is None:
                raise ResourceNotFoundException("Server", server_id)
            return self._server_to_dict(server)
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get server {server_id}: {e}")
            raise OpenStackException(
                message=f"Failed to get server: {str(e)}",
                openstack_error=str(e),
            )

    async def delete_server(self, server_id: str) -> bool:
        """Delete a server from OpenStack."""
        try:
            conn = self._get_connection()
            conn.compute.delete_server(server_id)
            logger.info(f"OpenStack: Deleted server {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete server {server_id}: {e}")
            raise OpenStackException(
                message=f"Failed to delete server: {str(e)}",
                openstack_error=str(e),
            )

    async def start_server(self, server_id: str) -> bool:
        """Start a server in OpenStack."""
        try:
            conn = self._get_connection()
            conn.compute.start_server(server_id)
            logger.info(f"OpenStack: Started server {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to start server {server_id}: {e}")
            raise OpenStackException(
                message=f"Failed to start server: {str(e)}",
                openstack_error=str(e),
            )

    async def stop_server(self, server_id: str) -> bool:
        """Stop a server in OpenStack."""
        try:
            conn = self._get_connection()
            conn.compute.stop_server(server_id)
            logger.info(f"OpenStack: Stopped server {server_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop server {server_id}: {e}")
            raise OpenStackException(
                message=f"Failed to stop server: {str(e)}",
                openstack_error=str(e),
            )

    async def reboot_server(self, server_id: str, reboot_type: str = "SOFT") -> bool:
        """Reboot a server in OpenStack."""
        try:
            conn = self._get_connection()
            conn.compute.reboot_server(server_id, reboot_type)
            logger.info(f"OpenStack: Rebooted server {server_id} ({reboot_type})")
            return True
        except Exception as e:
            logger.error(f"Failed to reboot server {server_id}: {e}")
            raise OpenStackException(
                message=f"Failed to reboot server: {str(e)}",
                openstack_error=str(e),
            )

    async def list_flavors(self) -> list[dict[str, Any]]:
        """List flavors from OpenStack."""
        try:
            conn = self._get_connection()
            flavors = []
            for flavor in conn.compute.flavors():
                flavors.append({
                    "id": flavor.id,
                    "name": flavor.name,
                    "vcpus": flavor.vcpus,
                    "memory_mb": flavor.ram,
                    "disk_gb": flavor.disk,
                    "ephemeral_gb": flavor.ephemeral,
                    "swap_mb": flavor.swap or 0,
                    "is_public": flavor.is_public,
                    "description": flavor.description,
                })
            return flavors
        except Exception as e:
            logger.error(f"Failed to list flavors: {e}")
            raise OpenStackException(
                message=f"Failed to list flavors: {str(e)}",
                openstack_error=str(e),
            )

    async def get_flavor(self, flavor_id: str) -> dict[str, Any]:
        """Get flavor details from OpenStack."""
        try:
            conn = self._get_connection()
            flavor = conn.compute.find_flavor(flavor_id)
            if flavor is None:
                raise ResourceNotFoundException("Flavor", flavor_id)
            return {
                "id": flavor.id,
                "name": flavor.name,
                "vcpus": flavor.vcpus,
                "memory_mb": flavor.ram,
                "disk_gb": flavor.disk,
                "ephemeral_gb": flavor.ephemeral,
                "swap_mb": flavor.swap or 0,
                "is_public": flavor.is_public,
                "description": flavor.description,
            }
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get flavor {flavor_id}: {e}")
            raise OpenStackException(
                message=f"Failed to get flavor: {str(e)}",
                openstack_error=str(e),
            )

    async def list_images(self) -> list[dict[str, Any]]:
        """List images from OpenStack."""
        try:
            conn = self._get_connection()
            images = []
            for image in conn.image.images():
                images.append({
                    "id": image.id,
                    "name": image.name,
                    "status": image.status,
                    "size_bytes": image.size,
                    "min_disk_gb": image.min_disk,
                    "min_memory_mb": image.min_ram,
                    "os_distro": image.os_distro,
                    "os_version": image.os_version,
                    "architecture": image.architecture,
                    "created_at": image.created_at,
                    "description": image.get("description"),
                })
            return images
        except Exception as e:
            logger.error(f"Failed to list images: {e}")
            raise OpenStackException(
                message=f"Failed to list images: {str(e)}",
                openstack_error=str(e),
            )

    async def get_image(self, image_id: str) -> dict[str, Any]:
        """Get image details from OpenStack."""
        try:
            conn = self._get_connection()
            image = conn.image.find_image(image_id)
            if image is None:
                raise ResourceNotFoundException("Image", image_id)
            return {
                "id": image.id,
                "name": image.name,
                "status": image.status,
                "size_bytes": image.size,
                "min_disk_gb": image.min_disk,
                "min_memory_mb": image.min_ram,
                "os_distro": image.os_distro,
                "os_version": image.os_version,
                "architecture": image.architecture,
                "created_at": image.created_at,
                "description": image.get("description"),
            }
        except ResourceNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get image {image_id}: {e}")
            raise OpenStackException(
                message=f"Failed to get image: {str(e)}",
                openstack_error=str(e),
            )

    async def check_connection(self) -> bool:
        """Check connection to OpenStack."""
        try:
            conn = self._get_connection()
            # Try to list flavors as a simple connectivity check
            list(conn.compute.flavors(limit=1))
            return True
        except Exception as e:
            logger.error(f"OpenStack connection check failed: {e}")
            return False


def get_openstack_client() -> BaseOpenStackClient:
    """Factory function to get the appropriate OpenStack client."""
    settings = get_settings()

    if settings.use_mock_openstack:
        logger.info("Using mock OpenStack client")
        return MockOpenStackClient()
    else:
        if not settings.openstack_credentials_configured:
            logger.warning(
                "OpenStack credentials not configured, falling back to mock client"
            )
            return MockOpenStackClient()

        logger.info("Using real OpenStack client")
        return RealOpenStackClient(settings)
