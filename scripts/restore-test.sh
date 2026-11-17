#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKUP_DIR="${1:-}"
BACKUP_GPG_PASSPHRASE="${BACKUP_GPG_PASSPHRASE:-}"
RESTORE_CONTAINER="apontaua-restore-test-$(date -u +%Y%m%d%H%M%S)-$$"
CONTAINER_STARTED="false"
MINIO_TEST_CONTAINER="apontaua-minio-restore-test-$(date -u +%Y%m%d%H%M%S)-$$"
MINIO_TEST_STARTED="false"
MINIO_TEST_VOLUME="apontaua-minio-restore-test-$(date -u +%Y%m%d%H%M%S)-$$"
MINIO_TEST_VOLUME_CREATED="false"
RESTORE_TMP=""

fail() { printf 'Erro: %s\n' "$*" >&2; exit 1; }

[[ -n "$BACKUP_DIR" ]] || fail 'utilização: scripts/restore-test.sh <diretório-do-backup>'
BACKUP_DIR="$(cd -- "$BACKUP_DIR" && pwd)" || fail 'diretório do backup não encontrado'
[[ -f "$BACKUP_DIR/manifest.txt" && -f "$BACKUP_DIR/SHA256SUMS" ]] || fail 'manifesto ou checksums não encontrados'
[[ -f "$BACKUP_DIR/database.dump.gpg" && -f "$BACKUP_DIR/files.tar.gz.gpg" && -f "$BACKUP_DIR/minio-data.tar.gz.gpg" && -f "$BACKUP_DIR/table-row-counts.txt.gpg" && -f "$BACKUP_DIR/minio-object-keys.jsonl.gpg" ]] || fail 'artefactos cifrados incompletos'

for command in docker gpg sha256sum jq; do
  command -v "$command" >/dev/null 2>&1 || fail "comando obrigatório não encontrado: $command"
done

if [[ -z "$BACKUP_GPG_PASSPHRASE" ]]; then
  [[ -r /dev/tty ]] || fail 'define BACKUP_GPG_PASSPHRASE por um gestor de segredos ou executa num terminal interativo'
  read -r -s -p 'Frase secreta para decifrar o backup: ' BACKUP_GPG_PASSPHRASE </dev/tty
  printf '\n' >/dev/tty
fi
[[ ${#BACKUP_GPG_PASSPHRASE} -ge 20 ]] || fail 'a frase secreta tem de ter pelo menos 20 caracteres'

(
  cd "$BACKUP_DIR"
  sha256sum --check --status SHA256SUMS
) || fail 'falha na validação dos checksums dos artefactos cifrados'

EXPECTED_FILE_COUNT="$(sed -n 's/^file_count=//p' "$BACKUP_DIR/manifest.txt")"
EXPECTED_MINIO_COUNT="$(sed -n 's/^minio_object_count=//p' "$BACKUP_DIR/manifest.txt")"
EXPECTED_METADATA_COUNT="$(sed -n 's/^stored_metadata_count=//p' "$BACKUP_DIR/manifest.txt")"
METADATA_TABLE_PRESENT="$(sed -n 's/^metadata_table_present=//p' "$BACKUP_DIR/manifest.txt")"
EXPECTED_TABLE_COUNT="$(sed -n 's/^table_count=//p' "$BACKUP_DIR/manifest.txt")"
[[ "$EXPECTED_FILE_COUNT" =~ ^[0-9]+$ ]] || fail 'file_count inválido no manifesto'
[[ "$EXPECTED_MINIO_COUNT" =~ ^[0-9]+$ ]] || fail 'minio_object_count inválido no manifesto'
[[ "$EXPECTED_METADATA_COUNT" =~ ^[0-9]+$ ]] || fail 'stored_metadata_count inválido no manifesto'
[[ "$METADATA_TABLE_PRESENT" == true || "$METADATA_TABLE_PRESENT" == false ]] || fail 'metadata_table_present inválido no manifesto'
[[ "$EXPECTED_TABLE_COUNT" =~ ^[0-9]+$ ]] || fail 'table_count inválido no manifesto'

compose_config="$(docker compose config --format json)" || fail 'não foi possível ler a configuração Docker Compose'
DB_IMAGE="$(jq -er '.services.db.image' <<<"$compose_config")"
MINIO_IMAGE="$(jq -er '.services.minio.image' <<<"$compose_config")"
DB_NAME="$(jq -er '.services.db.environment.POSTGRES_DB' <<<"$compose_config")"
DB_USER="$(jq -er '.services.db.environment.POSTGRES_USER' <<<"$compose_config")"
DB_PASSWORD="$(jq -er '.services.db.environment.POSTGRES_PASSWORD' <<<"$compose_config")"
APP_DB_USER="$(jq -er '.services.db.environment.APP_DB_USER' <<<"$compose_config")"
APP_DB_PASSWORD="$(jq -er '.services.db.environment.APP_DB_PASSWORD' <<<"$compose_config")"
MINIO_ROOT_USER="$(jq -er '.services.minio.environment.MINIO_ROOT_USER' <<<"$compose_config")"
MINIO_ROOT_PASSWORD="$(jq -er '.services.minio.environment.MINIO_ROOT_PASSWORD' <<<"$compose_config")"
MINIO_BUCKET="$(jq -er '.services.minio.environment.MINIO_BUCKET' <<<"$compose_config")"
unset compose_config

cleanup() {
  local status=$?
  trap - EXIT
  if [[ "$CONTAINER_STARTED" == true ]]; then
    docker rm --force "$RESTORE_CONTAINER" >/dev/null 2>&1 || status=1
  fi
  if [[ "$MINIO_TEST_STARTED" == true ]]; then
    docker rm --force "$MINIO_TEST_CONTAINER" >/dev/null 2>&1 || status=1
  fi
  if [[ "$MINIO_TEST_VOLUME_CREATED" == true ]]; then
    docker volume rm "$MINIO_TEST_VOLUME" >/dev/null 2>&1 || status=1
  fi
  if [[ -n "$RESTORE_TMP" && -d "$RESTORE_TMP" ]]; then
    rm -rf -- "$RESTORE_TMP"
  fi
  unset BACKUP_GPG_PASSPHRASE DB_PASSWORD APP_DB_PASSWORD MINIO_ROOT_PASSWORD
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# O teste usa apenas a camada descartável de um container, sem montar ou
# remover qualquer volume Docker existente ou persistente.
docker run --detach --rm --name "$RESTORE_CONTAINER" --network none \
  --env-file <(printf 'POSTGRES_DB=%s\nPOSTGRES_USER=%s\nPOSTGRES_PASSWORD=%s\nAPP_DB_USER=%s\nAPP_DB_PASSWORD=%s\n' \
    "$DB_NAME" "$DB_USER" "$DB_PASSWORD" "$APP_DB_USER" "$APP_DB_PASSWORD") \
  --mount "type=bind,src=$PROJECT_ROOT/db/init/10-restrict-app-role.sh,dst=/docker-entrypoint-initdb.d/10-restrict-app-role.sh,readonly" \
  "$DB_IMAGE" >/dev/null
CONTAINER_STARTED="true"

ready="false"
for _ in {1..60}; do
  if docker exec "$RESTORE_CONTAINER" pg_isready --username "$DB_USER" --dbname "$DB_NAME" >/dev/null 2>&1; then
    ready="true"
    break
  fi
  sleep 1
done
[[ "$ready" == true ]] || fail 'PostgreSQL isolado não ficou pronto'

APP_ROLE_FLAGS="$(printf "SELECT concat_ws('|', rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls) FROM pg_roles WHERE rolname = :'app_role';\n" \
  | docker exec --interactive "$RESTORE_CONTAINER" psql --username "$DB_USER" --dbname "$DB_NAME" \
      --no-psqlrc --tuples-only --no-align --set=app_role="$APP_DB_USER" \
  | tr -d '[:space:]')"
[[ "$APP_ROLE_FLAGS" == 'f|f|f|f|f' ]] || fail 'a role da aplicação no ambiente isolado tem privilégios inesperados'

docker exec "$RESTORE_CONTAINER" mkdir -p /restore-files

docker volume create "$MINIO_TEST_VOLUME" >/dev/null
MINIO_TEST_VOLUME_CREATED="true"
RESTORE_TMP="$(mktemp -d)"
gpg --batch --pinentry-mode loopback --passphrase-fd 3 --decrypt \
  "$BACKUP_DIR/minio-object-keys.jsonl.gpg" 3<<<"$BACKUP_GPG_PASSPHRASE" \
  > "$RESTORE_TMP/expected-minio-object-keys.jsonl"
EXPECTED_KEY_COUNT="$(wc -l < "$RESTORE_TMP/expected-minio-object-keys.jsonl" | tr -d '[:space:]')"
[[ "$EXPECTED_KEY_COUNT" == "$EXPECTED_MINIO_COUNT" ]] || fail 'contagem de chaves MinIO difere do manifesto'

gpg --batch --pinentry-mode loopback --passphrase-fd 3 --decrypt \
  "$BACKUP_DIR/database.dump.gpg" 3<<<"$BACKUP_GPG_PASSPHRASE" \
  | docker exec --interactive "$RESTORE_CONTAINER" pg_restore \
      --username "$DB_USER" --dbname "$DB_NAME" --clean --if-exists --exit-on-error

gpg --batch --pinentry-mode loopback --passphrase-fd 3 --decrypt \
  "$BACKUP_DIR/files.tar.gz.gpg" 3<<<"$BACKUP_GPG_PASSPHRASE" \
  | docker exec --interactive "$RESTORE_CONTAINER" tar --extract --gzip --file - --directory /restore-files

gpg --batch --pinentry-mode loopback --passphrase-fd 3 --decrypt \
  "$BACKUP_DIR/minio-data.tar.gz.gpg" 3<<<"$BACKUP_GPG_PASSPHRASE" \
  | docker run --rm --interactive --network none \
      --mount "type=volume,src=$MINIO_TEST_VOLUME,dst=/restore" \
      --entrypoint tar "$DB_IMAGE" -C /restore -xzf -

# MinIO restaurado usa apenas diretório efémero do teste e rede isolada. O
# cliente mc liga-se ao namespace de rede desse container para validar objetos.
docker run --detach --rm --name "$MINIO_TEST_CONTAINER" --network none \
  --env "MINIO_ROOT_USER=$MINIO_ROOT_USER" --env "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD" \
  --user 0 \
  --mount "type=volume,src=$MINIO_TEST_VOLUME,dst=/data" \
  --entrypoint minio "$MINIO_IMAGE" server /data --address ":9000" --console-address ":9001" >/dev/null
MINIO_TEST_STARTED="true"
minio_ready="false"
for _ in {1..60}; do
  if docker exec --user 0 "$MINIO_TEST_CONTAINER" /bin/sh -ec \
      'mc alias set restored http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 && mc ready restored >/dev/null 2>&1' \
      >/dev/null 2>&1; then
    minio_ready="true"
    break
  fi
  sleep 1
done
[[ "$minio_ready" == true ]] || fail 'MinIO isolado não ficou pronto com os dados restaurados'
RESTORED_MINIO_COUNT="$(docker exec --user 0 "$MINIO_TEST_CONTAINER" /bin/sh -ec \
  'mc ls --recursive --json "restored/'"$MINIO_BUCKET"'"' \
  | jq -c 'select(.type == "file") | .key' | sort \
  | tee "$RESTORE_TMP/restored-minio-object-keys.jsonl" | wc -l \
  | tr -d '[:space:]')"
[[ "$RESTORED_MINIO_COUNT" == "$EXPECTED_MINIO_COUNT" ]] || fail "quantidade de objetos MinIO difere: esperado=$EXPECTED_MINIO_COUNT obtido=$RESTORED_MINIO_COUNT"
cmp -s "$RESTORE_TMP/expected-minio-object-keys.jsonl" "$RESTORE_TMP/restored-minio-object-keys.jsonl" \
  || fail 'as chaves dos objetos MinIO restaurados diferem do backup'

if [[ "$METADATA_TABLE_PRESENT" == true ]]; then
  docker exec "$RESTORE_CONTAINER" sh -ec \
    'psql --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" --no-psqlrc --tuples-only --no-align --quiet --command "SELECT COALESCE(json_agg(object_key ORDER BY object_key), '\''[]'\''::json)::text FROM stored_file"' \
    | jq -c '.[]' | sort > "$RESTORE_TMP/restored-stored-file-object-keys.jsonl"
  RESTORED_METADATA_COUNT="$(wc -l < "$RESTORE_TMP/restored-stored-file-object-keys.jsonl" | tr -d '[:space:]')"
  [[ "$RESTORED_METADATA_COUNT" == "$EXPECTED_METADATA_COUNT" ]] || fail 'quantidade de metadados de ficheiros restaurados difere do manifesto'
  cmp -s "$RESTORE_TMP/expected-minio-object-keys.jsonl" "$RESTORE_TMP/restored-stored-file-object-keys.jsonl" \
    || fail 'as chaves dos metadados PostgreSQL não correspondem aos objetos MinIO restaurados'
else
  RESTORED_METADATA_COUNT=0
fi

ROW_COUNTS="$(gpg --batch --pinentry-mode loopback --passphrase-fd 3 --decrypt \
  "$BACKUP_DIR/table-row-counts.txt.gpg" 3<<<"$BACKUP_GPG_PASSPHRASE")"
RESTORED_TABLE_COUNT=0
if [[ -n "$ROW_COUNTS" ]]; then
  while IFS='|' read -r schema table expected_rows; do
    [[ -n "$schema" && -n "$table" && "$expected_rows" =~ ^[0-9]+$ ]] || fail 'inventário de tabelas malformado'
    actual_rows="$(printf 'SELECT count(*) FROM :"schema".:"table";\n' \
      | docker exec --interactive "$RESTORE_CONTAINER" psql --username "$DB_USER" --dbname "$DB_NAME" \
          --no-psqlrc --tuples-only --no-align --set=schema="$schema" --set=table="$table" \
      | tr -d '[:space:]')"
    [[ "$actual_rows" == "$expected_rows" ]] || fail "contagem de linhas difere em $schema.$table: esperado=$expected_rows obtido=$actual_rows"
    RESTORED_TABLE_COUNT=$((RESTORED_TABLE_COUNT + 1))
  done <<< "$ROW_COUNTS"
fi
[[ "$RESTORED_TABLE_COUNT" == "$EXPECTED_TABLE_COUNT" ]] || fail "quantidade de tabelas difere: esperado=$EXPECTED_TABLE_COUNT obtido=$RESTORED_TABLE_COUNT"

RESTORED_FILE_COUNT="$(docker exec "$RESTORE_CONTAINER" sh -c 'find /restore-files -type f | wc -l' | tr -d '[:space:]')"
[[ "$RESTORED_FILE_COUNT" == "$EXPECTED_FILE_COUNT" ]] || fail "contagem de ficheiros restaurados difere: esperado=$EXPECTED_FILE_COUNT obtido=$RESTORED_FILE_COUNT"

printf 'Restauro isolado funcional. Ficheiros legados: %s; objetos MinIO: %s; metadados comparados: %s; tabelas e contagens verificadas: %s.\n' \
  "$RESTORED_FILE_COUNT" "$RESTORED_MINIO_COUNT" "$RESTORED_METADATA_COUNT" "$RESTORED_TABLE_COUNT"
