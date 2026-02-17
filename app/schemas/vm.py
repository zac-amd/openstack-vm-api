"""Pydantic schemas for VM operations."""

import enum
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.vm import VMState


class RebootType(str, enum.Enum):
    """Reboot type enumeration."""

    SOFT = "SOFT"
    HARD = "HARD"


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class VMBase(BaseModel):
    """Base VM schema with common fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="VM name",
        examples=["my-web-server"],
    )
    flavor_id: str = Field(
        ...,
        description="Flavor ID defining VM size",
        examples=["m1.small"],
    )
    image_id: str = Field(
        ...,
        description="Image ID for the VM's operating system",
        examples=["ubuntu-22.04"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="VM description",
    )


class VMCreate(VMBase):
    """Schema for creating a new VM."""

    key_name: Optional[str] = Field(
        default=None,
        description="SSH key pair name",
        examples=["my-keypair"],
    )
    user_data: Optional[str] = Field(
        default=None,
        description="Cloud-init user data (base64 encoded)",
    )
    network_id: Optional[str] = Field(
        default=None,
        description="Network ID to attach VM to",
    )
    security_groups: Optional[list[str]] = Field(
        default=None,
        description="List of security group names",
        examples=[["default", "web-server"]],
    )
    availability_zone: Optional[str] = Field(
        default=None,
        description="Availability zone for the VM",
    )
    metadata: Optional[dict[str, str]] = Field(
        default=None,
        description="Key-value metadata for the VM",
    )


class VMUpdate(BaseModel):
    """Schema for updating a VM."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New VM name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="New VM description",
    )


class VMResponse(BaseModel):
    """Schema for VM response."""

    model_config = ConfigDict(from_attributes=True)

    uuid: str = Field(..., description="Unique VM identifier")
    name: str = Field(..., description="VM name")
    state: VMState = Field(..., description="Current VM state")
    state_description: Optional[str] = Field(
        default=None, description="Additional state information"
    )

    # Configuration
    flavor_id: str = Field(..., description="Flavor ID")
    image_id: str = Field(..., description="Image ID")

    # Resources
    vcpus: Optional[int] = Field(default=None, description="Number of vCPUs")
    memory_mb: Optional[int] = Field(default=None, description="Memory in MB")
    disk_gb: Optional[int] = Field(default=None, description="Disk size in GB")

    # Network
    ip_address: Optional[str] = Field(default=None, description="Private IP address")
    floating_ip: Optional[str] = Field(default=None, description="Floating/public IP")

    # Metadata
    description: Optional[str] = Field(default=None, description="VM description")
    key_name: Optional[str] = Field(default=None, description="SSH key pair name")

    # OpenStack reference
    openstack_id: Optional[str] = Field(
        default=None, description="OpenStack server ID"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    launched_at: Optional[datetime] = Field(
        default=None, description="Launch timestamp"
    )
    terminated_at: Optional[datetime] = Field(
        default=None, description="Termination timestamp"
    )

    # Computed properties
    is_running: bool = Field(..., description="Whether VM is running")
    is_stopped: bool = Field(..., description="Whether VM is stopped")
    is_transitioning: bool = Field(
        ..., description="Whether VM is in a transitional state"
    )


class VMListResponse(BaseModel):
    """Schema for paginated VM list response."""

    items: list[VMResponse] = Field(..., description="List of VMs")
    total: int = Field(..., description="Total number of VMs")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")


class VMActionResponse(BaseModel):
    """Schema for VM action response."""

    vm_uuid: str = Field(..., description="VM UUID")
    action: str = Field(..., description="Action performed")
    status: str = Field(..., description="Action status")
    message: str = Field(..., description="Status message")
    previous_state: Optional[VMState] = Field(
        default=None, description="State before action"
    )
    current_state: VMState = Field(..., description="Current state after action")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Action timestamp"
    )


class VMRebootRequest(BaseModel):
    """Schema for VM reboot request."""

    reboot_type: RebootType = Field(
        default=RebootType.SOFT,
        description="Type of reboot (SOFT or HARD)",
    )


class VMResizeRequest(BaseModel):
    """Schema for VM resize request."""

    flavor_id: str = Field(
        ...,
        description="New flavor ID for the VM",
        examples=["m1.medium"],
    )


class VMSnapshotRequest(BaseModel):
    """Schema for VM snapshot request."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Snapshot name",
        examples=["my-vm-snapshot-2024"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Snapshot description",
    )


class VMSnapshotResponse(BaseModel):
    """Schema for VM snapshot response."""

    snapshot_id: str = Field(..., description="Created snapshot ID")
    vm_uuid: str = Field(..., description="Source VM UUID")
    name: str = Field(..., description="Snapshot name")
    status: str = Field(..., description="Snapshot status")
    created_at: datetime = Field(..., description="Creation timestamp")
