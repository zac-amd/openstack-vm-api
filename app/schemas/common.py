"""Common Pydantic schemas for API responses."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service status", examples=["healthy"])
    version: str = Field(..., description="API version", examples=["1.0.0"])
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )
    database: str = Field(
        ..., description="Database connection status", examples=["connected"]
    )
    openstack: str = Field(
        ...,
        description="OpenStack connection status",
        examples=["connected", "mock_mode"],
    )


class ErrorDetail(BaseModel):
    """Error detail schema."""

    field: Optional[str] = Field(default=None, description="Field with error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[list[ErrorDetail]] = Field(
        default=None, description="Additional error details"
    )
    request_id: Optional[str] = Field(
        default=None, description="Request ID for tracking"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )


class FlavorResponse(BaseModel):
    """VM Flavor/Size response schema."""

    id: str = Field(..., description="Flavor ID", examples=["m1.small"])
    name: str = Field(..., description="Flavor name", examples=["Small Instance"])
    vcpus: int = Field(..., description="Number of vCPUs", examples=[2])
    memory_mb: int = Field(..., description="Memory in MB", examples=[2048])
    disk_gb: int = Field(..., description="Root disk size in GB", examples=[20])
    ephemeral_gb: int = Field(
        default=0, description="Ephemeral disk size in GB", examples=[0]
    )
    swap_mb: int = Field(default=0, description="Swap size in MB", examples=[0])
    is_public: bool = Field(default=True, description="Whether flavor is public")
    description: Optional[str] = Field(
        default=None, description="Flavor description"
    )


class FlavorListResponse(BaseModel):
    """List of flavors response."""

    items: list[FlavorResponse] = Field(..., description="List of flavors")
    total: int = Field(..., description="Total number of flavors")


class ImageResponse(BaseModel):
    """VM Image response schema."""

    id: str = Field(..., description="Image ID", examples=["ubuntu-22.04"])
    name: str = Field(
        ..., description="Image name", examples=["Ubuntu 22.04 LTS"]
    )
    status: str = Field(..., description="Image status", examples=["active"])
    size_bytes: Optional[int] = Field(
        default=None, description="Image size in bytes"
    )
    min_disk_gb: int = Field(
        default=0, description="Minimum disk required in GB"
    )
    min_memory_mb: int = Field(
        default=0, description="Minimum memory required in MB"
    )
    os_distro: Optional[str] = Field(
        default=None, description="Operating system distribution", examples=["ubuntu"]
    )
    os_version: Optional[str] = Field(
        default=None, description="Operating system version", examples=["22.04"]
    )
    architecture: Optional[str] = Field(
        default=None, description="CPU architecture", examples=["x86_64"]
    )
    created_at: Optional[datetime] = Field(
        default=None, description="Image creation timestamp"
    )
    description: Optional[str] = Field(default=None, description="Image description")


class ImageListResponse(BaseModel):
    """List of images response."""

    items: list[ImageResponse] = Field(..., description="List of images")
    total: int = Field(..., description="Total number of images")
