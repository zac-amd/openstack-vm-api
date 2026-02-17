"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from app.config import get_settings
from app.core.openstack_client import get_openstack_client
from app.database import async_session_factory
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies.",
)
async def health_check() -> HealthResponse:
    """Check API health status.

    Returns the status of:
    - API service
    - Database connection
    - OpenStack connection
    """
    settings = get_settings()
    db_status = "connected"
    openstack_status = "mock_mode" if settings.use_mock_openstack else "unknown"

    # Check database connection
    try:
        async with async_session_factory() as session:
            await session.execute("SELECT 1")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Check OpenStack connection
    if not settings.use_mock_openstack:
        try:
            client = get_openstack_client()
            connected = await client.check_connection()
            openstack_status = "connected" if connected else "disconnected"
        except Exception as e:
            openstack_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.api_version,
        timestamp=datetime.utcnow(),
        database=db_status,
        openstack=openstack_status,
    )


@router.get(
    "/",
    summary="API root",
    description="Get basic API information.",
)
async def root() -> dict:
    """Get API root information."""
    settings = get_settings()
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }
