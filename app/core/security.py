"""Security utilities for API authentication."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

# API Key header definition
api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API key for authentication",
    auto_error=False,
)


def get_api_key_header() -> APIKeyHeader:
    """Return the API key header dependency."""
    return api_key_header


async def verify_api_key(
    api_key: Annotated[str | None, Security(api_key_header)],
) -> str:
    """Verify the API key from request header.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTHENTICATION_ERROR",
                "message": "API key is required",
                "details": "Provide API key in X-API-Key header",
            },
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AUTHENTICATION_ERROR",
                "message": "Invalid API key",
                "details": "The provided API key is not valid",
            },
        )

    return api_key


# Type alias for dependency injection
APIKeyDep = Annotated[str, Depends(verify_api_key)]
