# FullStack-ApontaUA

Repositório da aplicação ApontaUA.

## Componentes

- `frontend/`: SPA React + TypeScript + Vite.
- `backend/`: API FastAPI organizada como monólito modular.
- `docs/ms3/legal/`: inventários e análise documental da MS3.

O microsite Docusaurus mantido no repositório de documentação é um projeto
separado e não faz parte desta aplicação.

O processo de branches e pull requests está descrito em
[docs/development/branching.md](docs/development/branching.md).

## Ambiente integrado com Docker

O Docker Compose inicia o frontend React/Vite, a API FastAPI, PostgreSQL e o
NGINX. Consulte o [guia do ambiente containerizado](docs/development/containerized-environment.md)
para pré-requisitos, portas, health checks e comandos.

Para executar os componentes diretamente na máquina, consulte
[frontend/README.md](frontend/README.md) e [backend/README.md](backend/README.md).
