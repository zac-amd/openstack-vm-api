"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_title: str = Field(default="OpenStack VM Lifecycle API")
    api_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)

    # API Key Authentication
    api_key: str = Field(default="dev-api-key-change-in-production")

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./openstack_vm.db"
    )

    # OpenStack Configuration
    use_mock_openstack: bool = Field(default=True)

    # OpenStack Credentials
    os_auth_url: Optional[str] = Field(default=None)
    os_project_name: Optional[str] = Field(default=None)
    os_project_domain_name: str = Field(default="Default")
    os_username: Optional[str] = Field(default=None)
    os_password: Optional[str] = Field(default=None)
    os_user_domain_name: str = Field(default="Default")
    os_region_name: str = Field(default="RegionOne")

    # Application Credentials (alternative auth)
    os_application_credential_id: Optional[str] = Field(default=None)
    os_application_credential_secret: Optional[str] = Field(default=None)

    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    reload: bool = Field(default=False)

    @property
    def openstack_credentials_configured(self) -> bool:
        """Check if OpenStack credentials are properly configured."""
        if self.os_application_credential_id and self.os_application_credential_secret:
            return True
        return all([
            self.os_auth_url,
            self.os_project_name,
            self.os_username,
            self.os_password,
        ])


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
