from types import SimpleNamespace

from backend.app.modules.health import router as health


async def test_liveness(client) -> None:
    response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_readiness_when_database_is_available(client, monkeypatch) -> None:
    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _query):
            return 1

    monkeypatch.setattr(health, "engine", SimpleNamespace(connect=Connection))
    monkeypatch.setattr(
        health,
        "ObjectStorage",
        lambda: SimpleNamespace(check_bucket=_ready),
    )
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "object_storage": "ok"}


async def test_readiness_when_database_is_unavailable(client, monkeypatch) -> None:
    class Connection:
        async def __aenter__(self):
            raise RuntimeError("database unavailable")

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(health, "engine", SimpleNamespace(connect=Connection))
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


async def _ready() -> bool:
    return True


async def test_readiness_when_minio_is_unavailable(client, monkeypatch) -> None:
    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _query):
            return 1

    async def unavailable() -> bool:
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(health, "engine", SimpleNamespace(connect=Connection))
    monkeypatch.setattr(health, "ObjectStorage", lambda: SimpleNamespace(check_bucket=unavailable))
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "object storage unavailable"}
