# Remote application deployment

## Status and assumptions

This is a portable Docker Compose reference for a Linux host. It pulls the API,
web and PostgreSQL images, and builds the MinIO image from the pinned upstream
source release in this repository. It does not connect to or deploy on an
Instituto de Telecomunicações (IT) server. The IT infrastructure, network and
operating constraints have not yet been confirmed.

The `.github/workflows/ci.yml` runs tests, lint, frontend build and Compose
configuration checks for pull requests to `dev`. After a push to `dev`, it runs
the same checks and then publishes the API and web images to GHCR. Publication
uses the package names configured in `.env.production.example`.

The deployment web image combines the built React SPA with a deployment-specific
NGINX template. The template preserves the existing `/api/v1` reverse-proxy
behavior and adds proxying for signed MinIO object URLs. A separate template is
needed because the development NGINX configuration targets Vite and HMR. The
development `compose.yaml`, Vite container and `nginx/nginx.conf` remain
unchanged.

## Requirements

- Linux host with Docker Engine and Docker Compose v2.
- Network access to GHCR and the PostgreSQL base image registry.
- GHCR read access if the application packages are private.
- A secure external method for supplying database and MinIO credentials.
- Host storage suitable for PostgreSQL, MinIO and the retained legacy file
  volume.

## GHCR image publication

The existing CI workflow publishes images only for a successful `push` to
`dev`. The publication job waits for backend tests/lint, frontend tests/lint/
build and both Compose configuration checks. Pull request runs do not receive
package write permission and do not publish images. CI uses the repository's
`GITHUB_TOKEN`; it does not use a personal access token or deployment secrets.

The workflow builds with the repository root as context and uses these
Dockerfiles:

| Package | Dockerfile | Deployment variable |
| --- | --- | --- |
| `ghcr.io/apontaua/fullstack-apontaua-api` | `Dockerfile` | `API_IMAGE` |
| `ghcr.io/apontaua/fullstack-apontaua-web` | `deployment/Dockerfile.web` | `WEB_IMAGE` |

Each image receives a commit-specific `sha-<full-commit-sha>` tag and a moving
`dev` tag. Prefer the SHA tag (or an image digest) in deployment configuration
so updates are explicit and can be rolled back. For example:

```dotenv
API_IMAGE=ghcr.io/apontaua/fullstack-apontaua-api:sha-<commit-sha>
WEB_IMAGE=ghcr.io/apontaua/fullstack-apontaua-web:sha-<commit-sha>
```

The build adds OCI metadata, including `org.opencontainers.image.source`, to
associate each package with this GitHub repository. The workflow does not
change package visibility. Confirm the package's access and visibility in the
GitHub package settings; if the packages are private, deployment hosts need
GHCR read access. Do not put registry credentials in image build arguments or
in the repository. Authenticate a deployment host through its approved secret
management process, then pull the selected references:

```bash
docker login ghcr.io -u <github-user> --password-stdin
docker compose --env-file .env.production -f compose.deployment.yaml pull api web db
docker compose --env-file .env.production -f compose.deployment.yaml build minio
```

The login command reads the password from standard input. Use an appropriately
scoped credential on the host, not the workflow's `GITHUB_TOKEN`.

MinIO is not pulled from the ApontaUA GHCR namespace. Compose builds
`apontaua/minio-server:RELEASE.2025-10-15T17-29-55Z` from
`minio/Server.Dockerfile`; that Dockerfile pins the MinIO server release and
`mc` version and includes the existing ApontaUA initialization script. The
script creates the private bucket and restricted application user required by
the API. The deployment helper builds this image during `up`; `pull` only
pulls API, web and PostgreSQL images. Rollback reuses the same pinned local
MinIO image when it is already present. It builds that reference only if it is
missing; rollback does not rebuild an available image unnecessarily.

The Dockerfile pins MinIO server to
`RELEASE.2025-10-15T17-29-55Z` and `mc` to
`RELEASE.2025-08-13T08-35-41Z`. The source builds resolve respectively to Go
module revisions `v0.0.0-20251015172955-9e49d5e7a648` and
`v0.0.0-20250813083541-7394ce0dd2a8`, matching the release timestamps and
upstream commit prefixes. The binaries print `DEVELOPMENT.GOGET` because
`go install module@tag` builds the tagged source without injecting the
linker-time version variables used for upstream release binaries. This label
does not mean the build used an unpinned latest revision, but it makes runtime
version reporting less useful for audit. See the
[MinIO release](https://github.com/minio/minio/releases/tag/RELEASE.2025-10-15T17-29-55Z)
and the [upstream issue about release version metadata in source builds](https://github.com/minio/minio/issues/21666).

Two clean `--no-cache` builds produced byte-identical `minio` and `mc`
binaries, but different full image IDs and layer hashes. Therefore these
builds are source-version-pinned, but strict bit-for-bit image reproducibility
has not been demonstrated. The floating `alpine:3.21` base tag and unpinned
Alpine package repository state can change the resulting image; pinning base
image digests and package snapshots would be needed for stronger
reproducibility. The MinIO Community repository is
[archived](https://github.com/minio/minio), which is also a maintenance and
security-update risk to resolve before long-term production use.

The official MinIO repository recommends building container images from source.
The official Quay tag was checked and returned `no such manifest`. The MinIO
Community source repository is archived, so this pinned release does not
receive future upstream fixes. Review that maintenance risk before a
production deployment.

## Configure environment

Copy `.env.production.example` to a local `.env.production` file and restrict
its permissions. Do not commit the local file. Set unique credentials through
the approved secret manager or secure host configuration, and replace the API
and web placeholder references with images that exist in GHCR. Prefer
references pinned to an image digest; a commit-specific tag is also suitable
when the publishing process treats it as immutable. The MinIO image is built
locally from its pinned source release.

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

The Compose file passes only each service's required variables. PostgreSQL
credentials are not passed to the web container; MinIO root credentials are
not passed to the API. PostgreSQL, MinIO and the MinIO console do not publish
host ports. Only the web gateway publishes a port, loopback-bound by default.

The named volumes are configured by `POSTGRES_VOLUME_NAME`,
`MINIO_VOLUME_NAME` and `UPLOADED_FILES_VOLUME_NAME`. This keeps their Docker
names stable across application updates and preserves the legacy
`/data/files` volume required by current backup tooling. The physical storage
location is controlled by the Docker volume driver/host configuration; confirm
the supported storage and backup policy with IT before deployment.

To place these volumes at explicit host paths, use
`compose.deployment.host-paths.yaml` and set absolute
`POSTGRES_DATA_PATH`, `MINIO_DATA_PATH` and `UPLOADED_FILES_DATA_PATH` values.
Create the directories first and set ownership/permissions to match the
container users. This overlay still creates named Docker volumes backed by
those paths, so the existing backup scripts can identify them.
Changing a volume's driver options does not migrate existing data. Use new
volume names for a new location and perform a separately planned, verified
data migration; do not point an existing populated volume name at another path.

`MINIO_PUBLIC_ENDPOINT` must be the browser-accessible origin used when signing
download URLs, with no path component. The gateway forwards requests for the
configured bucket to MinIO while preserving the original `Host` and path. Do
not rewrite the hostname or bucket path after a URL has been signed. The MinIO
service itself has no published port, and its console is not routed.

## Validate and start

Run from the repository root after setting the local environment file:

```bash
scripts/deployment.sh validate
scripts/deployment.sh pull
scripts/deployment.sh up
scripts/deployment.sh status
```

`up` pulls the selected images and recreates services as needed without building
images or removing volumes. It does not run Alembic migrations. Check the
container and application health through the script before routing users to
the service.

Database migrations remain an explicit maintenance action. After a verified
backup and compatibility review, an operator can run the Alembic migration
command against the selected deployment configuration:

```bash
docker compose --env-file .env.production -f compose.deployment.yaml \
  exec -T api /app/.venv/bin/alembic upgrade head
```

Do not run this as part of an unattended update. If using a Compose overlay,
include it in the command as well.

The default host binding is `127.0.0.1:8080`. Configure `WEB_BIND_ADDRESS` and
`WEB_PORT` for the private interface and port that an IT-provided ingress or
reverse proxy is allowed to reach. Do not bind to a public interface unless
the approved firewall and ingress design require it.

## HTTPS options

By default, the deployment NGINX listens on HTTP and is intended to sit behind
an IT-provided TLS-terminating reverse proxy. The proxy must preserve the Host
header, path and query string for signed MinIO URLs, and should forward
`X-Forwarded-Proto`.

If the deployment host is approved to terminate TLS directly at NGINX, provide
certificate and key paths managed by IT and use the TLS overlay:

```bash
DEPLOY_COMPOSE_FILES="compose.deployment.yaml compose.deployment.tls.yaml" \
  scripts/deployment.sh validate
DEPLOY_COMPOSE_FILES="compose.deployment.yaml compose.deployment.tls.yaml" \
  scripts/deployment.sh up
```

Set `TLS_CERTIFICATE_FILE`, `TLS_PRIVATE_KEY_FILE` and `HTTPS_PORT` in the local
environment file. The overlay requires real certificate files and does not
create or provide certificates. Set `MINIO_PUBLIC_ENDPOINT` to the public HTTPS
origin, including a non-standard public port if applicable.

## Updating and rollback

Record the current deployment environment file securely before changing image
references. Use an immutable reference for each image. Then validate and update:

```bash
cp .env.production .env.production.previous
chmod 600 .env.production.previous
# Update API_IMAGE and WEB_IMAGE in .env.production.
scripts/deployment.sh validate
scripts/deployment.sh up
```

Rollback selects the previous image references from the saved environment file:

```bash
scripts/deployment.sh rollback .env.production.previous
```

The rollback command does not delete volumes or run database migrations. It
cannot reverse schema changes. Before updating, verify that the prior
application version can read the current PostgreSQL schema. Take and verify a
backup using the existing backup procedure before a schema-changing release.
Keep the project name, volume names and service credentials consistent between
release environment files; update the saved file if credentials are rotated.

## Persistence and backups

The deployment uses stable named volumes for PostgreSQL, MinIO objects and the
legacy local file path. Updates do not remove or rename these volumes. Never use
`docker compose down -v` for deployment data.

The existing backup and isolated restore scripts use Docker Compose's selected
configuration. To run them against this deployment, select the deployment
Compose file and environment file in the shell environment:

```bash
COMPOSE_FILE=compose.deployment.yaml \
COMPOSE_ENV_FILES=.env.production \
  scripts/backup.sh

COMPOSE_FILE=compose.deployment.yaml \
COMPOSE_ENV_FILES=.env.production \
  scripts/restore-test.sh /absolute/path/to/encrypted-backup
```

`COMPOSE_FILE` and `COMPOSE_ENV_FILES` are Docker Compose pre-defined
environment variables; see the [Docker Compose environment variable
documentation](https://docs.docker.com/compose/how-tos/environment-variables/envvars/).

For direct NGINX TLS, include both Compose files in `COMPOSE_FILE`, separated
with the platform's Compose file separator, and use the corresponding local
environment. Keep encrypted backup artifacts and their passphrase separate
from the application host and repository.

## Deployment integration validation

The deployment helper supports multiple Compose files through
`DEPLOY_COMPOSE_FILES`. Validation does not print the resolved Compose model or
credential values. The helper's `status` command checks the gateway, SPA,
liveness and readiness endpoints through NGINX.

For host-path volumes, set
`DEPLOY_COMPOSE_FILES="compose.deployment.yaml compose.deployment.host-paths.yaml"`.
For NGINX TLS, add
`compose.deployment.tls.yaml` to the same space-separated list.

Remote deployment remains operator initiated. This workflow publishes
application images but does not connect to or deploy on a server. Local Compose
validation and isolated runtime checks should be recorded separately from any
future IT deployment evidence.

## Limitations

- A successful GitHub Actions run is required to confirm that GHCR accepts the
  package writes and creates the API and web packages with the intended access
  settings.
- The pinned MinIO Community release is no longer maintained upstream; future
  security fixes may require a migration to a maintained distribution or a
  separately approved object-storage service.
- Image pulling, startup and restore behavior require published images and
  valid host credentials; example references are not deployable.
- The database schema migration policy and compatibility guarantees are not
  automated.
- CPU/memory sizing, availability, firewall rules, TLS ownership, storage
  performance and backup retention require decisions for the target host.
- No deployment has been performed on institutional or production systems.

## US-067 (#77) acceptance criteria status

- **Remote hosting:** the Compose configuration is prepared for a compatible
  Linux/Docker host. API/web images are expected from GHCR and MinIO is built
  locally from the pinned source release. Actual remote hosting remains
  pending because IT requirements and published application images are not
  available yet.
- **Configured domain or public endpoint:** the web bind address and port,
  backend `ALLOWED_HOSTS`, and `MINIO_PUBLIC_ENDPOINT` are configurable. The
  final domain, DNS and ingress settings must be supplied by the host operator.
- **HTTPS:** direct NGINX TLS is prepared through the TLS overlay, or TLS can be
  terminated by an IT-provided proxy. Runtime TLS verification awaits
  IT-provided certificate material and endpoint details.
- **Required components:** the deployment includes the SPA/NGINX gateway,
  FastAPI, PostgreSQL and MinIO with health checks and startup ordering.
- **Production/development separation:** deployment uses
  `compose.deployment.yaml`; the development Compose and Vite configuration
  remain unchanged.
- **Documented procedure:** configuration, startup, updates, persistence,
  backups, migrations and rollback are documented above.
- **Smoke tests:** local isolated checks passed for the SPA, API health and a
  signed MinIO download. A smoke test on the final public endpoint remains
  pending remote hosting.
- **Rollback:** the helper restores previous image references without deleting
  volumes or applying migrations; schema compatibility still requires operator
  review.

## Validation performed for this implementation

- Compose configuration validation passed for the base deployment file, the
  TLS overlay and the host-path volume overlay using non-production test values.
- The deployment web image built successfully; `npm ci` reported zero
  vulnerabilities and the React/TypeScript production build passed.
- NGINX rendered the configured bucket route and passed `nginx -t` with the
  same read-only filesystem and temporary directories used by Compose.
- An isolated local stack built the API and custom MinIO images, started
  PostgreSQL and MinIO before the API and gateway, and passed frontend, API
  liveness and readiness checks.
- A signed MinIO download was retrieved through NGINX with the original host
  and object path intact. A test PostgreSQL row and MinIO object remained
  available after restarting both services.
- The test used unique `apontaua-us067-validation-*` volumes. Containers were
  stopped after validation; the test volumes were left intact.
- This execution environment's Docker daemon returned `operation not permitted`
  for every test container when `no-new-privileges:true` was set, including a
  generic Alpine container. The integrated test therefore used a temporary,
  uncommitted Compose override to remove that option. The deployment config
  retains `no-new-privileges:true`; its runtime behavior needs verification on
  the target Docker host.
- The TLS Compose overlay passed model validation, but NGINX TLS startup was
  not tested because no IT-provided certificate/key were available. No image
  publication to GHCR or remote deployment was performed.

### Final MinIO and deployment validation

- Two clean MinIO builds resolved the pinned upstream tags to the Go module
  revisions documented above. The `minio` and `mc` binary checksums matched
  across builds, while complete container image IDs differed; strict image
  reproducibility is therefore a remaining limitation.
- The exact Quay image tag
  `quay.io/minio/minio:RELEASE.2025-10-15T17-29-55Z` was not available
  (`no such manifest`), which supports keeping the existing local source build.
- An isolated deployment stack passed PostgreSQL, MinIO, API and web health
  checks. NGINX served the SPA and proxied liveness/readiness successfully.
  Anonymous access to the private MinIO bucket was denied; the limited
  application identity could upload and read an object, while MinIO
  administrative information remained denied to it.
- A test object remained readable after restarting MinIO and API. The isolated
  test used volumes `apontaua-final-20261123051536-655193-postgres`,
  `apontaua-final-20261123051536-655193-minio` and
  `apontaua-final-20261123051536-655193-files`. The test containers were
  stopped, and these volumes were retained. Existing development volumes were
  not used or modified.
- The successful integration test required a temporary, uncommitted override
  setting `no-new-privileges:false` on API/web because this host's Docker
  daemon rejected container startup with the deployment setting
  `no-new-privileges:true`. Thus the stack's exact production security setting
  still needs validation on the target host before merge/deployment.

## Integração futura com a infraestrutura IT

The following details must be confirmed before adapting or operating this
reference deployment:

- Type of infrastructure provided;
- Operating system and supported versions;
- Whether Docker/containers and Docker Compose are supported;
- CPU, memory and storage resources available;
- Domain name, DNS and public URL;
- HTTPS certificates and TLS termination point;
- Network topology, firewall rules and allowed ingress ports;
- Access to GHCR and image-pull authentication;
- Storage location, persistence, capacity and volume-driver options;
- Backup schedule, retention, encryption and restore ownership;
- Secret-management mechanism and rotation process;
- Logging, monitoring, alerting and operational ownership;
- Deployment, maintenance-window and rollback procedures;
- Access requirements for institutional services, including identity and email.
