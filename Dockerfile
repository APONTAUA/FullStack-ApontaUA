FROM ghcr.io/astral-sh/uv:0.13.7 AS uv-bin
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=uv-bin /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
RUN groupadd --system --gid 10001 apontaua \
    && useradd --system --uid 10001 --gid 10001 --home-dir /home/apontaua --create-home apontaua \
    && mkdir -p /data/files \
    && chown 10001:10001 /data/files
COPY --chown=10001:10001 backend ./backend
USER 10001:10001

EXPOSE 8000
CMD ["/app/.venv/bin/python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

