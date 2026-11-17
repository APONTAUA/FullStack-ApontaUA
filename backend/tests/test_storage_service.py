from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace

import pytest

from backend.app.core.config import Settings
from backend.app.modules.storage import service
from backend.app.modules.storage.models import StoredFile
from backend.app.modules.storage.service import ObjectStorage


class FakeClient:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self.calls: list[tuple] = []

    def put_object(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))

    def presigned_get_object(self, *, bucket_name, object_name, expires):
        self.calls.append((bucket_name, object_name, expires))
        return f"{self.endpoint}/{bucket_name}/{object_name}?signature=signed"

    def stat_object(self, _bucket, _key):
        if getattr(self, "error_code", None):
            raise FakeS3Error(self.error_code)
        return SimpleNamespace(size=1)

    def remove_object(self, *args) -> None:
        self.calls.append(args)


class FakeS3Error(Exception):
    def __init__(self, code: str) -> None:
        self.code = code


@pytest.fixture
def storage(monkeypatch) -> tuple[ObjectStorage, list[FakeClient]]:
    clients: list[FakeClient] = []

    def make_client(endpoint: str, _access: str, _secret: str, _region: str) -> FakeClient:
        client = FakeClient(endpoint)
        clients.append(client)
        return client

    monkeypatch.setattr(service, "_client", make_client)
    settings = Settings(
        db_password="test-only",
        minio_internal_endpoint="http://minio:9000",
        minio_public_endpoint="https://files.example.test",
        minio_access_key="test-user",
        minio_secret_key="test-secret",
        minio_bucket="private-files",
        minio_region="us-east-1",
    )
    return ObjectStorage(settings), clients


@pytest.mark.asyncio
async def test_upload_passes_content_type_and_checksum(storage) -> None:
    client, clients = storage
    await client.upload("docs/a.pdf", BytesIO(b"pdf"), 3, "application/pdf", "a" * 64)
    args, kwargs = clients[0].calls[0]
    assert args == ()
    assert kwargs["bucket_name"] == "private-files"
    assert kwargs["object_name"] == "docs/a.pdf"
    assert kwargs["length"] == 3
    assert kwargs["content_type"] == "application/pdf"
    assert kwargs["metadata"] == {"sha256": "a" * 64}


@pytest.mark.asyncio
async def test_presigned_url_uses_browser_accessible_signing_host(storage) -> None:
    client, clients = storage
    url = await client.presigned_download("docs/a.pdf", timedelta(minutes=5))
    assert url.startswith("https://files.example.test/private-files/docs/a.pdf?")
    assert clients[1].calls[0][2] == timedelta(minutes=5)


@pytest.mark.asyncio
async def test_exists_and_missing_object(storage, monkeypatch) -> None:
    client, clients = storage
    assert await client.exists("docs/a.pdf") is True
    monkeypatch.setattr(service, "S3Error", FakeS3Error)
    clients[0].error_code = "NoSuchKey"
    assert await client.exists("missing") is False


@pytest.mark.asyncio
async def test_delete_calls_minio_client(storage) -> None:
    client, clients = storage
    await client.delete("docs/a.pdf")
    assert clients[0].calls == [("private-files", "docs/a.pdf")]


@pytest.mark.asyncio
async def test_file_metadata_is_stored_in_sqlalchemy(session_factory) -> None:
    async with session_factory() as session:
        record = StoredFile(
            object_key="academic/uuid/notes.pdf",
            original_name="notas.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            checksum_sha256="b" * 64,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)

        assert record.id is not None
        assert record.created_at is not None
        assert record.object_key == "academic/uuid/notes.pdf"
