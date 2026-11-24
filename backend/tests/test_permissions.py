"""Papel simulado (X-Dev-Role) só com APP_ENV explícito de desenvolvimento ou teste."""

import pytest
from httpx import AsyncClient

from backend.app.core import permissions
from backend.app.core.config import Settings

ADMIN = {"X-Dev-Role": "administrador"}


def make_settings(monkeypatch: pytest.MonkeyPatch, app_env: str | None) -> Settings:
    if app_env is None:
        monkeypatch.delenv("APP_ENV", raising=False)
        return Settings(_env_file=None, DB_PASSWORD="test-only")
    return Settings(_env_file=None, DB_PASSWORD="test-only", APP_ENV=app_env)


@pytest.mark.parametrize(
    ("app_env", "enabled"),
    [
        ("development", True),
        ("test", True),
        ("staging", False),
        ("production", False),
        (None, False),
    ],
)
def test_dev_roles_enabled(
    monkeypatch: pytest.MonkeyPatch, app_env: str | None, enabled: bool
) -> None:
    assert permissions.dev_roles_enabled(make_settings(monkeypatch, app_env)) is enabled


def test_app_env_em_falta_assume_development_mas_nao_ativa_papel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = make_settings(monkeypatch, None)
    assert current.app_env == "development"
    assert permissions.dev_roles_enabled(current) is False


@pytest.mark.parametrize("app_env", ["production", "staging", None])
async def test_rotas_protegidas_recusam_papel_simulado_fora_de_dev(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, app_env: str | None
) -> None:
    monkeypatch.setattr(permissions, "settings", make_settings(monkeypatch, app_env))

    leitura = await client.get("/api/v1/cursos", headers=ADMIN)
    escrita = await client.post("/api/v1/cursos", json={"codigo": "1", "nome": "A"}, headers=ADMIN)

    assert leitura.status_code == 401
    assert escrita.status_code == 401
