from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator

from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Path(settings.file_storage_path).mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="API REST modular para a base de conhecimento colaborativa ApontaUA.",
    version="0.1.0",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)
