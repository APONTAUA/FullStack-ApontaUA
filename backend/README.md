# Backend ApontaUA

API REST em FastAPI, organizada como monólito modular. Cada domínio deve manter
as suas rotas, modelos e regras de negócio no respetivo pacote dentro de
`backend/app/modules/`; `api/router.py` agrega as rotas públicas.

## Arranque local

1. Copiar `.env.example` para `.env` e ajustar os valores locais.
2. Sincronizar as versões bloqueadas: `uv sync --locked --group build`.
3. Iniciar PostgreSQL (por exemplo, `docker compose up -d db`).
4. Criar ou atualizar as tabelas: `uv run alembic upgrade head`.
5. Iniciar a API: `uvicorn backend.app.main:app --reload`.

Para iniciar a stack integrada com Docker Compose, incluindo frontend, API,
PostgreSQL e NGINX, consulte
[`docs/development/containerized-environment.md`](../docs/development/containerized-environment.md).

OpenAPI fica disponível em `/api/v1/docs`. Os endpoints de estado são
`/api/v1/health/live` e `/api/v1/health/ready`.

`uv.lock` fixa as dependências runtime e a ferramenta de build. Alterações aos
intervalos declarados em `pyproject.toml` exigem revisão e regeneração do lock
com `uv lock`; não editar `uv.lock` manualmente.

## Migrações

As tabelas são criadas com Alembic (`backend/migrations/`). O URL da base de dados
vem das mesmas variáveis de ambiente da API; `alembic.ini` não guarda credenciais.

- Aplicar migrações: `uv run alembic upgrade head`.
- Criar uma migração depois de alterar modelos: `uv run alembic revision --autogenerate -m "descricao"`,
  rever o ficheiro gerado e importar o módulo novo em `backend/migrations/env.py`.
- Confirmar que os modelos e as migrações coincidem: `uv run alembic check`.

## Testes

`uv run --group test pytest` corre os testes com SQLite em memória, sem precisar de PostgreSQL.

## Permissões provisórias

Enquanto a autenticação institucional (EPIC-01) e os papéis (EPIC-02) não existem,
as rotas protegidas leem o papel do cabeçalho `X-Dev-Role` (por exemplo,
`X-Dev-Role: administrador`). Isto só funciona com `APP_ENV` igual a `development`
ou `test`; nos restantes ambientes, as rotas protegidas devolvem 401. A lógica está em
`backend/app/core/permissions.py` e deve ser substituída quando a autenticação existir.

## Persistência e integrações

PostgreSQL é a fonte de verdade. Ficheiros originais são guardados no caminho
persistente definido por `FILE_STORAGE_PATH`; a base de dados deverá guardar
metadados e referências. As credenciais OIDC e SMTP são apenas pontos de
configuração: os parâmetros reais dependem da confirmação institucional.

O `compose.yaml` é um ambiente de desenvolvimento local. Substituir credenciais,
definir segredos fora do repositório e configurar TLS, volumes e backups antes
de qualquer implantação partilhada ou de produção.
