# MS3 — Licenciamento de software e dependências

**Âmbito:** repositório `FullStack-ApontaUA`, fotografia dos lockfiles gerados em 2026-11-08. Esta análise documental de metadados não constitui parecer jurídico nem avaliação de segurança.

## Inventário reproduzível

- **Frontend:** `frontend/package-lock.json` (lockfile v3) contém 90 pacotes externos, incluindo 66 dependências opcionais/condicionais de plataforma; todos têm campo `license` nos metadados do lockfile. Há 9 dependências diretas: React/React DOM em runtime e sete ferramentas ou tipos de desenvolvimento. Foi usada a metadata do lockfile para incluir também pacotes opcionais que não estão instalados nesta plataforma.
- **Backend:** `uv.lock` contém 30 distribuições externas resolvidas: 5 dependências runtime diretas, Hatchling como dependência de build e 24 dependências transitivas. Os metadados de licença foram lidos das distribuições instaladas num ambiente Python 3.12 sincronizado com `uv.lock`; para dois pacotes sem expressão declarada foram examinados os classificadores e os ficheiros LICENSE incluídos.
- **Código próprio:** nem `apontaua-frontend` nem `apontaua-backend` têm licença do projeto declarada. A equipa ainda precisa escolher como licenciar o código ApontaUA.
- **Ferramenta de exportação:** `scripts/export_license_inventories.py` reconstrói os CSVs a partir de `package-lock.json`, `uv.lock` e metadata das distribuições Python.

## Resumo das licenças

| Inventário | Licenças/expressões encontradas | Observação |
|---|---|---|
| Frontend, 90 pacotes | MIT 54; Apache-2.0 22; MPL-2.0 12; ISC 1; BSD-3-Clause 1 | Os 12 pacotes MPL-2.0 são `lightningcss` e bindings opcionais para plataformas, na árvore do Vite. Rever a licença/NOTICE antes de distribuir bundles e preservar as informações de origem. |
| Backend, 30 pacotes | MIT 16; BSD-3-Clause 6; Apache-2.0 3; MIT License 1; PSF-2.0 1; MPL-2.0 1; `MIT AND PSF-2.0` 1; `Apache-2.0 OR BSD-2-Clause` 1 | `pathspec` (MPL-2.0) entra pela ferramenta de build Hatchling; `packaging` declara duas licenças alternativas; `greenlet` declara expressão dupla. |

Não foram encontrados GPL, LGPL, AGPL ou licenças proprietárias nas árvores resolvidas. As expressões são metadados dos pacotes, não uma conclusão de compatibilidade global.

## Pontos de atenção e obrigações

- **MPL-2.0:** licença copyleft ao nível dos ficheiros cobertos. A FAQ oficial da Mozilla descreve que modificações a ficheiros MPL distribuídos devem ser disponibilizadas sob MPL, sem obrigar a relicenciar automaticamente ficheiros independentes do produto inteiro. Confirmar condições de distribuição e avisos se o projeto modificar ou redistribuir esses componentes. ([FAQ MPL 2.0](https://www.mozilla.org/en-US/MPL/2.0/FAQ/))
- **Apache-2.0:** manter avisos de copyright/licença, incluir cópia da licença em redistribuições e reproduzir avisos NOTICE aplicáveis. TypeScript inclui `NOTICE.txt`; preservar se a sua distribuição for redistribuída. ([Aplicação da licença Apache](https://www.apache.org/legal/apply-license))
- **MIT/BSD/ISC/PSF:** preservar os avisos de copyright e licença quando redistribuídos. Os pacotes BSD/ISC/PSF estão discriminados linha a linha nos CSVs.
- Não se concluiu que exista conflito entre licenças. Os componentes MPL encontrados são dependências transitivas em ferramentas de build e incluem variantes específicas de plataforma; a aplicabilidade prática depende dos artefactos efetivamente distribuídos e de eventual modificação.
- O repositório ainda não tem `LICENSE`/`NOTICE` do código próprio. Separar avisos de terceiros do licenciamento da aplicação.

## Infraestrutura e limites remanescentes

As imagens `python:3.12-slim` e `postgres:17-alpine`, o executável uv copiado da imagem oficial e os serviços externos previstos estão no inventário próprio. As tags não estão fixadas por digest e os pacotes do sistema operativo dentro das imagens não foram inventariados via SBOM. Não há configuração efetiva Apache nem NGINX neste repositório. O contexto fornecido indica Apache, enquanto o NFR v2.0 indica NGINX; a equipa precisa confirmar a decisão antes de completar a licença do proxy.

O `Dockerfile` usa agora `uv sync --locked --no-dev --no-install-project`, pelo que as dependências runtime da imagem vêm de `uv.lock`. A licença do binário uv foi acrescentada ao inventário de infraestrutura. A imagem não foi construída nesta execução; as licenças dos pacotes do sistema operativo e a inspeção SBOM continuam pendentes.

## Processo adotado

O backend usa `uv` sobre o `pyproject.toml` existente: intervalos de dependências não foram alterados, e `uv.lock` fixa versões compatíveis. Hatchling mantém-se em `[build-system]` e também foi incluído no grupo `build` para o resolver aparecer no lock. As instruções estão em `backend/README.md`. O frontend usa npm e `package-lock.json`; o script de exportação reconstrói os CSVs sem instalar novas dependências no produto.
