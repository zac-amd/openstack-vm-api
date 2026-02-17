"""API endpoint integration tests."""

from typing import Any

import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        """Test health check endpoint."""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        assert data["database"] == "connected"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient) -> None:
        """Test API root endpoint."""
        response = await client.get("/api/v1/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestAuthenticationEndpoints:
    """Tests for API authentication."""

    @pytest.mark.asyncio
    async def test_missing_api_key(self, client: AsyncClient) -> None:
        """Test request without API key."""
        response = await client.get("/api/v1/vms")
        assert response.status_code == 401

        data = response.json()
        assert data["detail"]["error"] == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_invalid_api_key(self, client: AsyncClient) -> None:
        """Test request with invalid API key."""
        response = await client.get(
            "/api/v1/vms",
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_api_key(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test request with valid API key."""
        response = await client.get("/api/v1/vms", headers=api_key_header)
        assert response.status_code == 200


class TestVMEndpoints:
    """Tests for VM lifecycle endpoints."""

    @pytest.mark.asyncio
    async def test_list_vms_empty(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test listing VMs when none exist."""
        response = await client.get("/api/v1/vms", headers=api_key_header)
        assert response.status_code == 200

        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_create_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test creating a new VM."""
        response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == sample_vm_data["name"]
        assert data["flavor_id"] == sample_vm_data["flavor_id"]
        assert data["image_id"] == sample_vm_data["image_id"]
        assert data["state"] == "ACTIVE"
        assert "uuid" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_vm_invalid_flavor(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test creating VM with invalid flavor."""
        response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json={
                "name": "test-vm",
                "flavor_id": "invalid-flavor",
                "image_id": "ubuntu-22.04",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_vm_invalid_image(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test creating VM with invalid image."""
        response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json={
                "name": "test-vm",
                "flavor_id": "m1.small",
                "image_id": "invalid-image",
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test getting VM details."""
        # Create VM first
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        # Get VM
        response = await client.get(
            f"/api/v1/vms/{vm_uuid}",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["uuid"] == vm_uuid
        assert data["name"] == sample_vm_data["name"]

    @pytest.mark.asyncio
    async def test_get_vm_not_found(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test getting non-existent VM."""
        response = await client.get(
            "/api/v1/vms/non-existent-uuid",
            headers=api_key_header,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test updating VM details."""
        # Create VM first
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        # Update VM
        response = await client.patch(
            f"/api/v1/vms/{vm_uuid}",
            headers=api_key_header,
            json={"name": "updated-vm-name", "description": "Updated description"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "updated-vm-name"
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_delete_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test deleting a VM."""
        # Create VM first
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        # Delete VM
        response = await client.delete(
            f"/api/v1/vms/{vm_uuid}",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["action"] == "delete"
        assert data["status"] == "success"
        assert data["current_state"] == "DELETED"

        # Verify VM is deleted
        get_response = await client.get(
            f"/api/v1/vms/{vm_uuid}",
            headers=api_key_header,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_stop_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test stopping a running VM."""
        # Create VM first (starts as ACTIVE)
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        # Stop VM
        response = await client.post(
            f"/api/v1/vms/{vm_uuid}/stop",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["action"] == "stop"
        assert data["status"] == "success"
        assert data["current_state"] == "SHUTOFF"

    @pytest.mark.asyncio
    async def test_start_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test starting a stopped VM."""
        # Create and stop VM
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        await client.post(
            f"/api/v1/vms/{vm_uuid}/stop",
            headers=api_key_header,
        )

        # Start VM
        response = await client.post(
            f"/api/v1/vms/{vm_uuid}/start",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["action"] == "start"
        assert data["status"] == "success"
        assert data["current_state"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_reboot_vm(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
        sample_vm_data: dict[str, Any],
    ) -> None:
        """Test rebooting a running VM."""
        # Create VM first
        create_response = await client.post(
            "/api/v1/vms",
            headers=api_key_header,
            json=sample_vm_data,
        )
        vm_uuid = create_response.json()["uuid"]

        # Reboot VM (soft)
        response = await client.post(
            f"/api/v1/vms/{vm_uuid}/reboot",
            headers=api_key_header,
            json={"reboot_type": "SOFT"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "reboot" in data["action"]
        assert data["status"] == "success"
        assert data["current_state"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_list_vms_pagination(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test VM list pagination."""
        # Create multiple VMs
        for i in range(5):
            await client.post(
                "/api/v1/vms",
                headers=api_key_header,
                json={
                    "name": f"test-vm-{i}",
                    "flavor_id": "m1.small",
                    "image_id": "ubuntu-22.04",
                },
            )

        # Test pagination
        response = await client.get(
            "/api/v1/vms",
            headers=api_key_header,
            params={"page": 1, "page_size": 2},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["pages"] == 3


class TestFlavorEndpoints:
    """Tests for flavor endpoints."""

    @pytest.mark.asyncio
    async def test_list_flavors(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test listing available flavors."""
        response = await client.get("/api/v1/flavors", headers=api_key_header)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["total"] > 0

        # Check flavor structure
        flavor = data["items"][0]
        assert "id" in flavor
        assert "name" in flavor
        assert "vcpus" in flavor
        assert "memory_mb" in flavor
        assert "disk_gb" in flavor

    @pytest.mark.asyncio
    async def test_get_flavor(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test getting a specific flavor."""
        response = await client.get(
            "/api/v1/flavors/m1.small",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "m1.small"
        assert "vcpus" in data
        assert "memory_mb" in data

    @pytest.mark.asyncio
    async def test_get_flavor_not_found(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test getting a non-existent flavor."""
        response = await client.get(
            "/api/v1/flavors/non-existent",
            headers=api_key_header,
        )
        assert response.status_code == 404


class TestImageEndpoints:
    """Tests for image endpoints."""

    @pytest.mark.asyncio
    async def test_list_images(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test listing available images."""
        response = await client.get("/api/v1/images", headers=api_key_header)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["total"] > 0

        # Check image structure
        image = data["items"][0]
        assert "id" in image
        assert "name" in image
        assert "status" in image

    @pytest.mark.asyncio
    async def test_get_image(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test getting a specific image."""
        response = await client.get(
            "/api/v1/images/ubuntu-22.04",
            headers=api_key_header,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "ubuntu-22.04"
        assert "name" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_get_image_not_found(
        self,
        client: AsyncClient,
        api_key_header: dict[str, str],
    ) -> None:
        """Test getting a non-existent image."""
        response = await client.get(
            "/api/v1/images/non-existent",
            headers=api_key_header,
        )
        assert response.status_code == 404
