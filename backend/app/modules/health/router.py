import logging

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.modules.storage.service import ObjectStorage

router = APIRouter()
logger = logging.getLogger("backend.health")


@router.get("/health/live", summary="Verifica se a API está ativa")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Verifica se a API está pronta para servir pedidos")
async def readiness(request: Request) -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning(
            "readiness dependency unavailable request_id=%s dependency=postgresql error_type=%s",
            getattr(request.state, "request_id", "unknown"),
            type(exc).__name__,
        )
        raise HTTPException(status_code=503, detail="database unavailable") from None

    try:
        if not await ObjectStorage().check_bucket():
            raise RuntimeError("configured bucket is unavailable")
    except Exception as exc:
        logger.warning(
            "readiness dependency unavailable request_id=%s dependency=minio error_type=%s",
            getattr(request.state, "request_id", "unknown"),
            type(exc).__name__,
        )
        raise HTTPException(status_code=503, detail="object storage unavailable") from None

    return {"status": "ok", "database": "ok", "object_storage": "ok"}
