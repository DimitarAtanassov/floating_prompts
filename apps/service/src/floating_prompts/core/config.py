"""Application configuration.

Settings are loaded from environment variables (and an optional ``.env`` file)
using ``pydantic-settings``. Configuration is grouped into nested sections so
that related knobs live together and map to a clear env-var namespace:

    FP_DB__HOST=db.internal   -> settings.db.host
    FP_SERVER__PORT=9000      -> settings.server.port
    FP_LOG__LEVEL=DEBUG       -> settings.log.level

The single entry point is :func:`get_settings`, which returns a cached instance.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "AppSettings",
    "DatabaseSettings",
    "Environment",
    "LoggingSettings",
    "ServerSettings",
    "get_settings",
]


class Environment(StrEnum):
    """Deployment environment."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseSettings(BaseModel):
    """PostgreSQL connection configuration."""

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"  # noqa: S105 - dev default; override in real envs
    name: str = "floating_prompts"

    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    echo: bool = False

    def url(self, *, driver: str = "asyncpg") -> str:
        """Build a SQLAlchemy connection URL for the given DBAPI driver.

        Args:
            driver: ``asyncpg`` for the async app, ``psycopg`` for Alembic.
        """
        password = quote_plus(self.password)
        return (
            f"postgresql+{driver}://{self.user}:{password}"
            f"@{self.host}:{self.port}/{self.name}"
        )

    @property
    def async_url(self) -> str:
        """Async (asyncpg) connection URL used by the running service."""
        return self.url(driver="asyncpg")

    @property
    def sync_url(self) -> str:
        """Sync (psycopg) connection URL used by Alembic migrations."""
        return self.url(driver="psycopg")


class ServerSettings(BaseModel):
    """HTTP server configuration."""

    host: str = "0.0.0.0"  # noqa: S104 - binding all interfaces is intended in containers
    port: int = 8000
    reload: bool = False
    root_path: str = ""
    cors_origins: list[str] = Field(default_factory=list)


class LoggingSettings(BaseModel):
    """Structured logging configuration."""

    level: str = "INFO"
    json_logs: bool = True


class AppSettings(BaseSettings):
    """Top-level application settings, composed of nested sections."""

    model_config = SettingsConfigDict(
        env_prefix="FP_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.LOCAL
    debug: bool = False

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    log: LoggingSettings = Field(default_factory=LoggingSettings)

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return the cached application settings instance."""
    return AppSettings()
