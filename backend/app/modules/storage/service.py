"""Cliente reutilizável para objetos privados no MinIO."""

import asyncio
from datetime import timedelta
from typing import BinaryIO
from urllib.parse import urlsplit

from minio.error import S3Error

from backend.app.core.config import Settings, get_settings
from minio import Minio


def _client(endpoint: str, access_key: str, secret_key: str, region: str) -> Minio:
    parsed = urlsplit(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path not in {"", "/"}:
        raise ValueError("MinIO endpoint deve ser uma origem HTTP(S), sem caminho")
    return Minio(
        parsed.netloc,
        access_key=access_key,
        secret_key=secret_key,
        secure=parsed.scheme == "https",
        region=region,
    )


class ObjectStorage:
    """Operações async para bucket privado; chamadas SDK bloqueantes vão para threads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        secret = self.settings.minio_secret_key.get_secret_value()
        if not self.settings.minio_access_key or not secret:
            raise ValueError("Credenciais MinIO não configuradas")
        self._client = _client(
            self.settings.minio_internal_endpoint,
            self.settings.minio_access_key,
            secret,
            self.settings.minio_region,
        )
        # URLs assinadas são criadas para este host. Nunca substituir o hostname depois.
        self._url_client = _client(
            self.settings.minio_public_endpoint,
            self.settings.minio_access_key,
            secret,
            self.settings.minio_region,
        )
        self.bucket = self.settings.minio_bucket

    async def upload(
        self,
        object_key: str,
        data: BinaryIO,
        length: int,
        content_type: str,
        sha256: str | None = None,
    ) -> None:
        metadata = {"sha256": sha256} if sha256 else None
        await asyncio.to_thread(
            self._client.put_object,
            bucket_name=self.bucket,
            object_name=object_key,
            data=data,
            length=length,
            content_type=content_type,
            metadata=metadata,
        )

    async def check_bucket(self) -> bool:
        """Devolve se o bucket configurado está acessível com as credenciais da aplicação."""
        return await asyncio.to_thread(self._client.bucket_exists, self.bucket)

    async def presigned_download(
        self,
        object_key: str,
        expires: timedelta = timedelta(minutes=10),
    ) -> str:
        return await asyncio.to_thread(
            self._url_client.presigned_get_object,
            bucket_name=self.bucket,
            object_name=object_key,
            expires=expires,
        )

    async def exists(self, object_key: str) -> bool:
        try:
            await asyncio.to_thread(self._client.stat_object, self.bucket, object_key)
            return True
        except S3Error as exc:
            if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise

    async def delete(self, object_key: str) -> None:
        await asyncio.to_thread(self._client.remove_object, self.bucket, object_key)
