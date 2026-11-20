import logging
import re
import sys
import time
from collections.abc import Awaitable, Callable
from logging import Logger
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
RequestHandler = Callable[[Request], Awaitable[Response]]


def configure_logging(level: str) -> Logger:
    logger = logging.getLogger("backend")
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level.upper() if level.upper() in logging.getLevelNamesMapping() else "INFO")
    logger.propagate = False
    return logger


def install_request_logging(app: FastAPI) -> None:
    logger = logging.getLogger("backend.http")

    @app.middleware("http")
    async def log_requests(request: Request, call_next: RequestHandler) -> Response:
        supplied_id = request.headers.get("X-Request-ID", "")
        request_id = supplied_id if REQUEST_ID_PATTERN.fullmatch(supplied_id) else uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        route = "unmatched"

        try:
            response = await call_next(request)
            route = getattr(request.scope.get("route"), "path", route)
        except Exception as exc:
            route = getattr(request.scope.get("route"), "path", route)
            logger.error(
                "request failed request_id=%s method=%s route=%s error_type=%s",
                request_id,
                request.method,
                route,
                type(exc).__name__,
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )

        response.headers["X-Request-ID"] = request_id
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "request completed request_id=%s method=%s route=%s status_code=%d duration_ms=%.2f",
            request_id,
            request.method,
            route,
            response.status_code,
            elapsed_ms,
        )
        return response


__all__ = ["configure_logging", "install_request_logging"]
