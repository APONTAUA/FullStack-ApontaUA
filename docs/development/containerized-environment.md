# Ambiente containerizado

## Âmbito

O `compose.yaml` define o ambiente de desenvolvimento integrado com quatro
serviços separados:

- `frontend`: React + Vite, acessível pelo NGINX e com HMR encaminhado pelo proxy.
- `api`: FastAPI, SQLAlchemy assíncrono e `asyncpg`.
- `db`: PostgreSQL 17.
- `nginx`: porta de entrada HTTP; encaminha `/api/v1/` para a API e o restante
  tráfego para o servidor Vite.

Este Compose executa Vite em modo de desenvolvimento. Para uma implantação de
produção ainda são necessários, entre outros aspetos, TLS, gestão de segredos,
backups e um frontend construído para produção.

## Requisitos

- Docker Engine em execução.
- Docker Compose v2.24 ou superior (o Compose usa `env_file.required`).

O ficheiro `.env` é opcional. Sem ele, o Compose usa valores locais de
desenvolvimento. Para personalizar portas, credenciais e outras definições:

```bash
cp .env.example .env
```

O `.env` está excluído do Git. A palavra-passe de exemplo serve apenas para
desenvolvimento local; substitui-a antes de partilhar o ambiente.

## Iniciar

Na raiz do repositório:

```bash
docker compose config
docker compose up --build -d
docker compose ps
```

A aplicação fica disponível em `http://localhost:8080` (ou na porta definida
por `WEB_PORT`). O NGINX faz o reverse proxy e encaminha os pedidos da SPA e da
API para os serviços internos.

## Endpoints e portas locais

- Frontend e proxy: `http://localhost:8080/`.
- API através do NGINX: `http://localhost:8080/api/v1/`.
- Liveness: `http://localhost:8080/api/v1/health/live`.
- Readiness (inclui `SELECT 1` no PostgreSQL):
  `http://localhost:8080/api/v1/health/ready`.
- Documentação OpenAPI: `http://localhost:8080/api/v1/docs`.
- Acesso direto de desenvolvimento à API: `http://localhost:8000`.
- PostgreSQL no host: `localhost:5432`.

As portas da API e do PostgreSQL estão limitadas ao loopback do host. Para as
alterar, define `API_PORT` e `POSTGRES_PORT` no `.env`.

## Ver estado e logs

```bash
docker compose ps
docker compose logs -f
docker compose logs -f api
```

O Compose verifica a ligação ao PostgreSQL com `pg_isready`, a readiness da API
com uma consulta à base de dados e a resposta HTTP do frontend e do NGINX. O
NGINX só inicia depois de frontend e API estarem saudáveis; a API espera que o
PostgreSQL esteja saudável.

## Persistência e paragem

Os dados do PostgreSQL ficam no volume `postgres_data`. Os ficheiros enviados
pela API ficam no volume `uploaded_files`, montado em `/data/files`.

```bash
docker compose down
```

Este comando pára e remove os containers, mantendo os volumes nomeados. Não
uses `docker compose down --volumes` se quiseres conservar a base de dados e os
ficheiros.
