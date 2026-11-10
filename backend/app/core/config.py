from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApontaUA API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://apontaua:apontaua@localhost:5432/apontaua"
    file_storage_path: Path = Path("./var/files")
    max_upload_size_mb: int = Field(default=25, gt=0)

    # Configuração preparada; o fluxo OIDC será ligado após confirmação do IdP institucional.
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None

    smtp_host: str | None = None
    smtp_port: int = Field(default=587, gt=0, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
