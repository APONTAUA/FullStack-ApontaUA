#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_GPG_PASSPHRASE="${BACKUP_GPG_PASSPHRASE:-}"
WORK_DIR=""
API_CONTAINER=""
API_WAS_RUNNING="false"
MINIO_CONTAINER=""
MINIO_WAS_RUNNING="false"

fail() { printf 'Erro: %s\n' "$*" >&2; exit 1; }

for command in docker gpg sha256sum jq; do
  command -v "$command" >/dev/null 2>&1 || fail "comando obrigatório não encontrado: $command"
done

if [[ -z "$BACKUP_GPG_PASSPHRASE" ]]; then
  [[ -r /dev/tty ]] || fail 'define BACKUP_GPG_PASSPHRASE por um gestor de segredos ou executa num terminal interativo'
  read -r -s -p 'Frase secreta para cifrar o backup: ' BACKUP_GPG_PASSPHRASE </dev/tty
  printf '\n' >/dev/tty
  read -r -s -p 'Confirma a frase secreta: ' BACKUP_GPG_CONFIRM </dev/tty
  printf '\n' >/dev/tty
  [[ -n "$BACKUP_GPG_PASSPHRASE" && "$BACKUP_GPG_PASSPHRASE" == "$BACKUP_GPG_CONFIRM" ]] || fail 'as frases secretas estão vazias ou não coincidem'
  unset BACKUP_GPG_CONFIRM
fi
[[ ${#BACKUP_GPG_PASSPHRASE} -ge 20 ]] || fail 'usa uma frase secreta com pelo menos 20 caracteres'

DB_CONTAINER="$(docker compose ps -q db)"
API_CONTAINER="$(docker compose ps -q api)"
MINIO_CONTAINER="$(docker compose ps -q minio)"
[[ -n "$DB_CONTAINER" && -n "$API_CONTAINER" && -n "$MINIO_CONTAINER" ]] || fail 'inicia os serviços db, api e minio antes do backup'
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$DB_CONTAINER")" == healthy ]] || fail 'PostgreSQL não está healthy'
[[ "$(docker inspect --format '{{.State.Health.Status}}' "$MINIO_CONTAINER")" == healthy ]] || fail 'MinIO não está healthy'
DB_IMAGE="$(docker inspect --format '{{.Config.Image}}' "$DB_CONTAINER")"
API_WAS_RUNNING="$(docker inspect --format '{{.State.Running}}' "$API_CONTAINER")"
MINIO_WAS_RUNNING="$(docker inspect --format '{{.State.Running}}' "$MINIO_CONTAINER")"
FILE_VOLUME="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data/files"}}{{.Name}}{{end}}{{end}}' "$API_CONTAINER")"
MINIO_VOLUME="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}' "$MINIO_CONTAINER")"
[[ -n "$FILE_VOLUME" ]] || fail 'não foi encontrado um volume Docker montado em /data/files'
[[ -n "$MINIO_VOLUME" ]] || fail 'não foi encontrado um volume Docker montado em /data do MinIO'
mkdir -p -- "$BACKUP_DIR"
chmod 700 -- "$BACKUP_DIR"
WORK_DIR="$(mktemp -d "$BACKUP_DIR/.apontaua-backup.XXXXXXXX")"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FINAL_DIR="$BACKUP_DIR/apontaua-$TIMESTAMP"
[[ ! -e "$FINAL_DIR" ]] || fail "já existe um backup para $TIMESTAMP"

cleanup() {
  local status=$?
  trap - EXIT
  if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
    rm -rf -- "$WORK_DIR"
  fi
  if [[ "$MINIO_WAS_RUNNING" == true ]]; then
    docker compose start minio >/dev/null || status=1
  fi
  if [[ "$API_WAS_RUNNING" == true ]]; then
    docker compose start api >/dev/null || status=1
  fi
  unset BACKUP_GPG_PASSPHRASE
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

encrypt_backup() {
  gpg --batch --yes --pinentry-mode loopback --passphrase-fd 3 \
    --symmetric --cipher-algo AES256 --output "$1" 3<<<"$BACKUP_GPG_PASSPHRASE"
}

# Para a API antes de enumerar os objetos. Depois para MinIO antes do dump e da
# cópia do volume, mantendo metadados e objetos no mesmo ponto operacional.
docker compose stop api >/dev/null
docker exec "$MINIO_CONTAINER" /bin/sh -ec \
  'mc alias set local http://127.0.0.1:9000 "$MINIO_APP_USER" "$MINIO_APP_PASSWORD" >/dev/null; mc ls --recursive --json "local/$MINIO_BUCKET"' \
  | jq -c 'select(.type == "file") | .key' | sort > "$WORK_DIR/minio-object-keys.jsonl"
MINIO_OBJECT_COUNT="$(wc -l < "$WORK_DIR/minio-object-keys.jsonl" | tr -d '[:space:]')"
docker compose stop minio >/dev/null

METADATA_TABLE_PRESENT="$(docker compose exec -T db sh -ec \
  'psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --tuples-only --no-align --quiet --command "SELECT to_regclass('\''public.stored_file'\'') IS NOT NULL"' \
  | tr -d '[:space:]')"
[[ "$METADATA_TABLE_PRESENT" == t || "$METADATA_TABLE_PRESENT" == f ]] || fail 'não foi possível verificar a tabela stored_file'
if [[ "$METADATA_TABLE_PRESENT" == t ]]; then
  METADATA_TABLE_PRESENT=true
  docker compose exec -T db sh -ec \
    'psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --tuples-only --no-align --quiet --command "SELECT COALESCE(json_agg(object_key ORDER BY object_key), '\''[]'\''::json)::text FROM stored_file"' \
    | jq -c '.[]' | sort > "$WORK_DIR/stored-file-object-keys.jsonl"
else
  METADATA_TABLE_PRESENT=false
  : > "$WORK_DIR/stored-file-object-keys.jsonl"
fi
STORED_METADATA_COUNT="$(wc -l < "$WORK_DIR/stored-file-object-keys.jsonl" | tr -d '[:space:]')"
if [[ "$METADATA_TABLE_PRESENT" == true ]] && ! cmp -s \
    "$WORK_DIR/stored-file-object-keys.jsonl" "$WORK_DIR/minio-object-keys.jsonl"; then
  fail 'as chaves de stored_file e os objetos MinIO não coincidem'
fi

docker compose exec -T db sh -c \
  'exec pg_dump --format=custom --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"' \
  | encrypt_backup "$WORK_DIR/database.dump.gpg"

docker run --rm --network none \
  --mount "type=volume,src=$FILE_VOLUME,dst=/source,readonly" \
  --entrypoint tar "$DB_IMAGE" -C /source -czf - . \
  | encrypt_backup "$WORK_DIR/files.tar.gz.gpg"

docker run --rm --network none \
  --mount "type=volume,src=$MINIO_VOLUME,dst=/source,readonly" \
  --entrypoint tar "$DB_IMAGE" -C /source -czf - . \
  | encrypt_backup "$WORK_DIR/minio-data.tar.gz.gpg"

FILE_COUNT="$(docker run --rm --network none \
  --mount "type=volume,src=$FILE_VOLUME,dst=/source,readonly" \
  --entrypoint sh "$DB_IMAGE" -c 'find /source -type f | wc -l' | tr -d '[:space:]')"

TABLE_COUNT="$(docker compose exec -T db sh -c \
  'psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --tuples-only --no-align --command "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('\''pg_catalog'\'', '\''information_schema'\'')"' \
  | tr -d '[:space:]')"
docker compose exec -T db sh -c \
  'exec psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --tuples-only --no-align --field-separator="|"' \
  < "$PROJECT_ROOT/scripts/table-row-counts.sql" \
  | encrypt_backup "$WORK_DIR/table-row-counts.txt.gpg"
encrypt_backup "$WORK_DIR/minio-object-keys.jsonl.gpg" \
  < "$WORK_DIR/minio-object-keys.jsonl"
rm -f -- "$WORK_DIR/minio-object-keys.jsonl" "$WORK_DIR/stored-file-object-keys.jsonl"

(
  cd "$WORK_DIR"
  sha256sum database.dump.gpg files.tar.gz.gpg minio-data.tar.gz.gpg table-row-counts.txt.gpg minio-object-keys.jsonl.gpg > SHA256SUMS
)
{
  printf 'format_version=2\n'
  printf 'created_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'file_count=%s\n' "$FILE_COUNT"
  printf 'minio_object_count=%s\n' "$MINIO_OBJECT_COUNT"
  printf 'stored_metadata_count=%s\n' "$STORED_METADATA_COUNT"
  printf 'metadata_table_present=%s\n' "$METADATA_TABLE_PRESENT"
  printf 'table_count=%s\n' "$TABLE_COUNT"
} > "$WORK_DIR/manifest.txt"

mv -- "$WORK_DIR" "$FINAL_DIR"
WORK_DIR=""
printf 'Backup cifrado criado: %s\n' "$FINAL_DIR"
