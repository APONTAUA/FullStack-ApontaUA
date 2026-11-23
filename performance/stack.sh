#!/usr/bin/env bash
set -euo pipefail

: "${PERF_DB_PASSWORD:?Define PERF_DB_PASSWORD localmente}"
: "${PERF_POSTGRES_PASSWORD:?Define PERF_POSTGRES_PASSWORD localmente}"
: "${PERF_MINIO_ROOT_PASSWORD:?Define PERF_MINIO_ROOT_PASSWORD localmente}"
: "${PERF_MINIO_APP_PASSWORD:?Define PERF_MINIO_APP_PASSWORD localmente}"

export APP_ENV=test
export APONTAUA_ENV_FILE=/dev/null
export DB_USER=perf_app
export DB_PASSWORD="$PERF_DB_PASSWORD"
export POSTGRES_DB=apontaua_perf
export POSTGRES_USER=perf_admin
export POSTGRES_PASSWORD="$PERF_POSTGRES_PASSWORD"
export POSTGRES_PORT=15432
export API_PORT=18000
export MINIO_ROOT_USER=perf_minio_root
export MINIO_ROOT_PASSWORD="$PERF_MINIO_ROOT_PASSWORD"
export MINIO_APP_USER=perf_minio_app
export MINIO_APP_PASSWORD="$PERF_MINIO_APP_PASSWORD"
export MINIO_BUCKET=apontaua-perf-files
export MINIO_API_PORT=19000
export MINIO_PUBLIC_ENDPOINT=http://127.0.0.1:19000

project=apontaua-perf

case "${1:-}" in
    up)
        docker compose -p "$project" up -d db minio api
        docker compose -p "$project" exec -T api /app/.venv/bin/alembic upgrade head
        PERF_ENVIRONMENT=isolated-local \
            POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=15432 \
            uv run --locked --group performance python performance/seed.py
        docker compose -p "$project" ps
        ;;
    stop)
        docker compose -p "$project" stop api db minio
        ;;
    *)
        echo "Usage: $0 {up|stop}" >&2
        exit 2
        ;;
esac
