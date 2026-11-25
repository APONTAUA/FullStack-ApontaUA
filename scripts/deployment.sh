#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
CALLER_DIR="$PWD"
DEFAULT_ENV_FILE="$PROJECT_ROOT/.env.production"
DEPLOY_ENV_FILE="${DEPLOY_ENV_FILE:-$DEFAULT_ENV_FILE}"
DEPLOY_COMPOSE_FILES="${DEPLOY_COMPOSE_FILES:-compose.deployment.yaml}"

fail() {
  printf 'Erro: %s\n' "$*" >&2
  exit 1
}

resolve_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s/%s\n' "$CALLER_DIR" "$1" ;;
  esac
}

ENV_FILE="$(resolve_path "$DEPLOY_ENV_FILE")"
[[ -r "$ENV_FILE" ]] || fail "ficheiro de ambiente não legível: $ENV_FILE"

read -r -a COMPOSE_FILE_NAMES <<< "$DEPLOY_COMPOSE_FILES"
(( ${#COMPOSE_FILE_NAMES[@]} > 0 )) || fail 'DEPLOY_COMPOSE_FILES está vazio'

COMPOSE_FILES=()
for file in "${COMPOSE_FILE_NAMES[@]}"; do
  if [[ "$file" = /* ]]; then
    COMPOSE_PATH="$file"
  else
    COMPOSE_PATH="$PROJECT_ROOT/$file"
  fi
  [[ -f "$COMPOSE_PATH" ]] || fail "ficheiro Compose não encontrado: $COMPOSE_PATH"
  COMPOSE_FILES+=("$COMPOSE_PATH")
done

compose() {
  local -a command=(docker compose --project-directory "$PROJECT_ROOT" --env-file "$ENV_FILE")
  for file in "${COMPOSE_FILES[@]}"; do
    command+=(-f "$file")
  done
  "${command[@]}" "$@"
}

validate() {
  compose config --quiet || fail 'configuração Compose inválida; verifica as variáveis obrigatórias'
}

pull_registry_images() {
  compose pull api web db
}

build_minio_image() {
  compose build minio
}

reuse_or_build_minio_image() {
  local minio_image
  minio_image="$(compose config --images | sed -n '/^apontaua\/minio-server:/p' | head -n 1)"
  [[ -n "$minio_image" ]] || fail 'não foi encontrada uma referência de imagem MinIO local na configuração Compose'
  if docker image inspect "$minio_image" >/dev/null 2>&1; then
    printf 'A reutilizar a imagem MinIO local %s.\n' "$minio_image"
  else
    build_minio_image
  fi
}

check_health() {
  compose ps
  compose exec -T web wget -q -O /dev/null http://127.0.0.1:8080/nginx-health \
    || fail 'NGINX não respondeu ao health check'
  compose exec -T web wget -q -O /dev/null http://127.0.0.1:8080/ \
    || fail 'frontend não respondeu através do NGINX'
  compose exec -T web wget -q -O /dev/null http://127.0.0.1:8080/api/v1/health/live \
    || fail 'endpoint de liveness da API não respondeu através do NGINX'
  compose exec -T web wget -q -O /dev/null http://127.0.0.1:8080/api/v1/health/ready \
    || fail 'endpoint de readiness da API não respondeu através do NGINX'
  printf 'Health checks do NGINX, frontend e API concluídos.\n'
}

usage() {
  cat >&2 <<'USAGE'
Utilização:
  scripts/deployment.sh validate
  scripts/deployment.sh pull
  scripts/deployment.sh up
  scripts/deployment.sh status
  scripts/deployment.sh rollback <ficheiro-de-ambiente-da-versao-anterior>

Variáveis opcionais:
  DEPLOY_ENV_FILE       Ficheiro local com valores para o deployment (default: .env.production)
  DEPLOY_COMPOSE_FILES  Ficheiros Compose separados por espaços (default: compose.deployment.yaml)
USAGE
}

case "${1:-}" in
  validate)
    validate
    printf 'Configuração de deployment válida.\n'
    ;;
  pull)
    validate
    pull_registry_images
    ;;
  up)
    validate
    pull_registry_images
    build_minio_image
    compose up -d --no-build
    check_health
    ;;
  status)
    check_health
    ;;
  rollback)
    [[ $# -eq 2 ]] || { usage; exit 2; }
    PREVIOUS_ENV_FILE="$(resolve_path "$2")"
    [[ -r "$PREVIOUS_ENV_FILE" ]] || fail "ficheiro da versão anterior não legível: $PREVIOUS_ENV_FILE"
    printf 'Aviso: confirma que a versão anterior é compatível com o esquema PostgreSQL atual.\n' >&2
    ENV_FILE="$PREVIOUS_ENV_FILE"
    validate
    pull_registry_images
    reuse_or_build_minio_image
    compose up -d --no-build
    check_health
    ;;
  *)
    usage
    exit 2
    ;;
esac
