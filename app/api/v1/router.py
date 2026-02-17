"""API v1 main router combining all endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import vms, flavors, images, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    vms.router,
    prefix="/vms",
    tags=["Virtual Machines"],
)

api_router.include_router(
    flavors.router,
    prefix="/flavors",
    tags=["Flavors"],
)

api_router.include_router(
    images.router,
    prefix="/images",
    tags=["Images"],
)

api_router.include_router(
    health.router,
    tags=["Health"],
)
