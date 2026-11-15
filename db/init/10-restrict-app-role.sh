#!/bin/sh
set -eu

case "$APP_DB_USER" in
  ""|[0-9]*|*[!a-zA-Z0-9_]*)
    echo "APP_DB_USER must contain only letters, digits, and underscores, and cannot start with a digit." >&2
    exit 1
    ;;
esac

psql \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --set=app_user="$APP_DB_USER" \
  --set=db_name="$POSTGRES_DB" \
  <<SQL
SELECT format(
    'CREATE ROLE %I LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS',
    :'app_user'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec

GRANT CONNECT ON DATABASE :"db_name" TO :"app_user";
GRANT USAGE, CREATE ON SCHEMA public TO :"app_user";
\\password $APP_DB_USER
$APP_DB_PASSWORD
$APP_DB_PASSWORD
SQL
