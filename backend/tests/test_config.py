import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_settings_accept_valid_values() -> None:
    settings = Settings(
        _env_file=None,
        APP_ENV="test",
        DB_PASSWORD="test-only",
        POSTGRES_PORT="55432",
        CORS_ORIGINS=["http://localhost:5173"],
    )

    assert settings.app_env == "test"
    assert settings.postgres_port == 55432
    assert settings.cors_origins == ["http://localhost:5173"]
    assert "test-only" not in repr(settings)


@pytest.mark.parametrize(
    ("values", "field"),
    [
        ({"DB_PASSWORD": "  "}, "db_password"),
        ({"DB_PASSWORD": "secret", "POSTGRES_PORT": "0"}, "postgres_port"),
        ({"DB_PASSWORD": "secret", "APP_ENV": "invalid"}, "app_env"),
    ],
)
def test_settings_reject_invalid_values(values: dict[str, str], field: str) -> None:
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **values)

    assert field in str(error.value)
