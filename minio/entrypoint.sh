#!/bin/sh
set -eu
rm -f /tmp/minio-init-ready

minio server /data --address ":9000" --console-address ":9001" &
server_pid=$!
terminate() {
  kill -TERM "$server_pid" 2>/dev/null || true
  wait "$server_pid" 2>/dev/null || true
}
trap terminate TERM INT

ready=false
for _ in $(seq 1 60); do
  if wget -q -O /dev/null http://127.0.0.1:9000/minio/health/ready; then
    ready=true
    break
  fi
  kill -0 "$server_pid" 2>/dev/null || break
  sleep 1
done
[ "$ready" = true ] || { echo "MinIO não ficou pronto" >&2; exit 1; }

mc alias set local http://127.0.0.1:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
mc mb --ignore-existing "local/$MINIO_BUCKET" >/dev/null
mc anonymous set none "local/$MINIO_BUCKET" >/dev/null

cat >/tmp/apontaua-policy.json <<EOF
{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetBucketLocation","s3:ListBucket"],"Resource":["arn:aws:s3:::$MINIO_BUCKET"]},{"Effect":"Allow","Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],"Resource":["arn:aws:s3:::$MINIO_BUCKET/*"]}]}
EOF
mc admin policy info local apontaua-app >/dev/null 2>&1 \
  || mc admin policy create local apontaua-app /tmp/apontaua-policy.json >/dev/null
mc admin user info local "$MINIO_APP_USER" >/dev/null 2>&1 \
  || mc admin user add local "$MINIO_APP_USER" "$MINIO_APP_PASSWORD" >/dev/null
mc admin policy attach local apontaua-app --user "$MINIO_APP_USER" >/dev/null

touch /tmp/minio-init-ready
wait "$server_pid"
