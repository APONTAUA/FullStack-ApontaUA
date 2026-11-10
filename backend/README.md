# Backend ApontaUA

API REST em FastAPI, organizada como monólito modular. Cada domínio deve manter
as suas rotas, modelos e regras de negócio no respetivo pacote dentro de
`backend/app/modules/`; `api/router.py` agrega as rotas públicas.

## Arranque local

1. Copiar `.env.example` para `.env` e ajustar os valores locais.
2. Sincronizar as versões bloqueadas: `uv sync --locked --group build`.
3. Iniciar PostgreSQL (por exemplo, `docker compose up -d db`).
4. Iniciar a API: `uvicorn backend.app.main:app --reload`.

OpenAPI fica disponível em `/api/v1/docs`. Os endpoints de estado são
`/api/v1/health/live` e `/api/v1/health/ready`.

`uv.lock` fixa as dependências runtime e a ferramenta de build. Alterações aos
intervalos declarados em `pyproject.toml` exigem revisão e regeneração do lock
com `uv lock`; não editar `uv.lock` manualmente.

## Persistência e integrações

PostgreSQL é a fonte de verdade. Ficheiros originais são guardados no caminho
persistente definido por `FILE_STORAGE_PATH`; a base de dados deverá guardar
metadados e referências. As credenciais OIDC e SMTP são apenas pontos de
configuração: os parâmetros reais dependem da confirmação institucional.

O `compose.yaml` é um perfil de desenvolvimento local. Substituir credenciais,
definir segredos fora do repositório e configurar volumes/backups antes de
qualquer implantação partilhada ou de produção.
