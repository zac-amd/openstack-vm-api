"""Image (OS images) endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.core.openstack_client import BaseOpenStackClient, get_openstack_client
from app.core.security import verify_api_key
from app.schemas.common import ImageResponse, ImageListResponse

router = APIRouter()

# Type alias for dependency injection
APIKeyDep = Annotated[str, Depends(verify_api_key)]


def get_client() -> BaseOpenStackClient:
    """Dependency to get OpenStack client."""
    return get_openstack_client()


OpenStackClientDep = Annotated[BaseOpenStackClient, Depends(get_client)]


@router.get(
    "",
    response_model=ImageListResponse,
    summary="List all images",
    description="Get a list of all available OS images.",
)
async def list_images(
    client: OpenStackClientDep,
    api_key: APIKeyDep,
) -> ImageListResponse:
    """List all available OS images.

    Images are operating system templates used to boot VMs.
    """
    images = await client.list_images()
    return ImageListResponse(
        items=[ImageResponse(**img) for img in images],
        total=len(images),
    )


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    summary="Get image details",
    description="Get detailed information about a specific image.",
)
async def get_image(
    client: OpenStackClientDep,
    api_key: APIKeyDep,
    image_id: str = Path(..., description="Image ID"),
) -> ImageResponse:
    """Get details of a specific image by ID."""
    image = await client.get_image(image_id)
    return ImageResponse(**image)
