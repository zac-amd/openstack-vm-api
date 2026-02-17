"""Pytest configuration and fixtures."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import Settings, get_settings
from app.database import Base, get_session
from app.main import app

# Set test environment variables before importing app modules
os.environ["USE_MOCK_OPENSTACK"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["API_KEY"] = "test-api-key"
os.environ["DEBUG"] = "true"


def get_test_settings() -> Settings:
    """Get test settings override."""
    return Settings(
        use_mock_openstack=True,
        database_url="sqlite+aiosqlite:///:memory:",
        api_key="test-api-key",
        debug=True,
    )


# Override settings for tests
app.dependency_overrides[get_settings] = get_test_settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Create test database with fresh tables for each test."""
    # Create in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yield session_factory

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(
    test_db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    async with test_db() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(
    test_db: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with test_db() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def api_key_header() -> dict[str, str]:
    """Get API key header for authenticated requests."""
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def sample_vm_data() -> dict[str, Any]:
    """Sample VM creation data."""
    return {
        "name": "test-vm",
        "flavor_id": "m1.small",
        "image_id": "ubuntu-22.04",
        "description": "Test virtual machine",
    }


@pytest.fixture
def sample_vm_data_full() -> dict[str, Any]:
    """Full sample VM creation data with all optional fields."""
    return {
        "name": "test-vm-full",
        "flavor_id": "m1.medium",
        "image_id": "ubuntu-22.04",
        "description": "Test virtual machine with all options",
        "key_name": "my-keypair",
        "network_id": "network-123",
        "security_groups": ["default", "web-server"],
        "availability_zone": "nova",
        "metadata": {"environment": "test", "owner": "pytest"},
    }
