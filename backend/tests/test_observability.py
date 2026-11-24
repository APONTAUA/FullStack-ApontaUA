import logging
from io import StringIO

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.core.observability import install_request_logging


async def test_request_logging_correlates_request_and_omits_query_string() -> None:
    app = FastAPI()
    install_request_logging(app)

    @app.get("/private/{record_id}")
    async def private_record(record_id: str) -> dict[str, str]:
        return {"id": record_id}

    logger = logging.getLogger("backend.http")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/private/record-1?access_token=do-not-log",
                headers={"X-Request-ID": "trace-123"},
            )
    finally:
        logger.removeHandler(handler)

    log_output = stream.getvalue()
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "trace-123"
    assert "request_id=trace-123" in log_output
    assert "route=/private/{record_id}" in log_output
    assert "do-not-log" not in log_output
    assert "record-1" not in log_output


async def test_unhandled_exception_is_sanitized_and_has_correlation_id() -> None:
    app = FastAPI()
    install_request_logging(app)

    @app.get("/failure")
    async def fail() -> None:
        raise RuntimeError("sensitive-token-value")

    logger = logging.getLogger("backend.http")
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/failure")
    finally:
        logger.removeHandler(handler)

    log_output = stream.getvalue()
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers.get("X-Request-ID")
    assert "error_type=RuntimeError" in log_output
    assert "sensitive-token-value" not in log_output
