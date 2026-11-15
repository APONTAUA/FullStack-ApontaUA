from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.core.database import engine

router = APIRouter()


@router.get("/health/live", summary="Verifica se a API está ativa")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready", summary="Verifica se a API está pronta para servir pedidos")
async def readiness() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable") from None
    return {"status": "ok", "database": "ok"}
