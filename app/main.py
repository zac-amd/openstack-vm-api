"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import get_settings
from app.core.exceptions import APIException
from app.database import create_tables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting OpenStack VM Lifecycle API...")

    # Create database tables
    await create_tables()
    logger.info("Database tables created/verified")

    settings = get_settings()
    logger.info(f"Running in {'mock' if settings.use_mock_openstack else 'real'} OpenStack mode")

    yield

    # Shutdown
    logger.info("Shutting down OpenStack VM Lifecycle API...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="""
## OpenStack VM Lifecycle Management API

A RESTful API for managing OpenStack virtual machine lifecycle operations.

### Features
- Create, list, get, update, and delete VMs
- Start, stop, and reboot VMs
- List available flavors (VM sizes) and images
- API key authentication
- Automatic OpenAPI documentation

### Authentication
All API endpoints (except health check) require an API key.
Include the API key in the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Quick Start
1. List available flavors: `GET /api/v1/flavors`
2. List available images: `GET /api/v1/images`
3. Create a VM: `POST /api/v1/vms`
4. Manage VM lifecycle: start, stop, reboot
        """,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    return app


# Create the application instance
app = create_application()


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)} if get_settings().debug else {},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
    )
