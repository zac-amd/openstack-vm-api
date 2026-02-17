"""Flavor (VM sizes) endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.core.openstack_client import BaseOpenStackClient, get_openstack_client
from app.core.security import verify_api_key
from app.schemas.common import FlavorResponse, FlavorListResponse

router = APIRouter()

# Type alias for dependency injection
APIKeyDep = Annotated[str, Depends(verify_api_key)]


def get_client() -> BaseOpenStackClient:
    """Dependency to get OpenStack client."""
    return get_openstack_client()


OpenStackClientDep = Annotated[BaseOpenStackClient, Depends(get_client)]


@router.get(
    "",
    response_model=FlavorListResponse,
    summary="List all flavors",
    description="Get a list of all available VM flavors/sizes.",
)
async def list_flavors(
    client: OpenStackClientDep,
    api_key: APIKeyDep,
) -> FlavorListResponse:
    """List all available VM flavors.

    Flavors define the compute, memory, and storage capacity of VMs.
    """
    flavors = await client.list_flavors()
    return FlavorListResponse(
        items=[FlavorResponse(**f) for f in flavors],
        total=len(flavors),
    )


@router.get(
    "/{flavor_id}",
    response_model=FlavorResponse,
    summary="Get flavor details",
    description="Get detailed information about a specific flavor.",
)
async def get_flavor(
    client: OpenStackClientDep,
    api_key: APIKeyDep,
    flavor_id: str = Path(..., description="Flavor ID"),
) -> FlavorResponse:
    """Get details of a specific flavor by ID."""
    flavor = await client.get_flavor(flavor_id)
    return FlavorResponse(**flavor)
