FROM golang:1.24.2-alpine3.21 AS build

ENV CGO_ENABLED=0 GOBIN=/out
RUN apk add --no-cache ca-certificates git
RUN go install -v github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z
RUN go install -v github.com/minio/mc@RELEASE.2025-08-13T08-35-41Z

FROM alpine:3.21
RUN apk add --no-cache ca-certificates \
    && addgroup -S minio \
    && adduser -S -G minio minio \
    && mkdir /data \
    && chown minio:minio /data
COPY --from=build /out/minio /usr/local/bin/minio
COPY --from=build /out/mc /usr/local/bin/mc
COPY entrypoint.sh /usr/local/bin/apontaua-minio-entrypoint
RUN chmod 755 /usr/local/bin/apontaua-minio-entrypoint
USER minio
VOLUME ["/data"]
EXPOSE 9000 9001
ENTRYPOINT ["/usr/local/bin/apontaua-minio-entrypoint"]
