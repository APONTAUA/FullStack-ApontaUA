from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.core.database import engine
from backend.app.core.observability import configure_logging, install_request_logging

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Path(settings.file_storage_path).mkdir(parents=True, exist_ok=True)
    yield
    await engine.dispose()


docs_url = f"{settings.api_v1_prefix}/docs" if settings.app_env != "production" else None
redoc_url = f"{settings.api_v1_prefix}/redoc" if settings.app_env != "production" else None
openapi_url = f"{settings.api_v1_prefix}/openapi.json" if settings.app_env != "production" else None

app = FastAPI(
    title=settings.app_name,
    description="API REST modular para a base de conhecimento colaborativa ApontaUA.",
    version="0.1.0",
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
install_request_logging(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)
