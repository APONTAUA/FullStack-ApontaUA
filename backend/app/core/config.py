from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ApontaUA API"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    postgres_db: str = "apontaua"
    db_user: str = "apontaua_app"
    db_password: SecretStr = Field(repr=False)
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, gt=0, le=65535)
    file_storage_path: Path = Path("./var/files")
    max_upload_size_mb: int = Field(default=25, gt=0)
    cors_origins: list[str] = Field(default_factory=list)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    @field_validator("db_password")
    @classmethod
    def database_password_must_not_be_empty(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("DB_PASSWORD must be set in the environment")
        return value

    # Configuração preparada; o fluxo OIDC será ligado após confirmação do IdP institucional.
    oidc_issuer_url: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: SecretStr | None = Field(default=None, repr=False)

    smtp_host: str | None = None
    smtp_port: int = Field(default=587, gt=0, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = Field(default=None, repr=False)
    smtp_from: str | None = None
    smtp_starttls: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
