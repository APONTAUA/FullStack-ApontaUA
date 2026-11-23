# Cálculo da reputação (US-051)

A reputação de um utilizador é um valor de 0 a 100 (RN-099), calculado em dois passos:
cada critério é normalizado para 0 a 100 e os cinco são agregados pela soma ponderada
da RN-101. O código está em `backend/app/modules/reputation/service.py`.

As funções recebem indicadores já filtrados: só avaliações válidas, consultas e
downloads válidos (US-056) e infrações confirmadas (US-055).

## Fórmulas

| Critério | Função | Fórmula |
| --- | --- | --- |
| Reputação global | `calcular_reputacao` | `R = 0,30Q + 0,20U + 0,15C + 0,20M + 0,15F` |
| Qualidade (Q) | `calcular_qualidade` | `ajustada = (n × média + 10 × 3) / (n + 10)`; `Q = (ajustada − 1) / 4 × 100` |
| Utilidade (U) | `calcular_utilidade` | `min((consultas + downloads) / 100, 1) × 100` |
| Colaboração (C) | `calcular_colaboracao` | `min((comentários úteis + sugestões úteis) / 20, 1) × 100` |
| Melhoria contínua (M) | `calcular_melhoria_continua` | `min(sugestões incorporadas / 10, 1) × 100` |
| Fiabilidade (F) | `calcular_fiabilidade` | `max(100 − 25 × infrações confirmadas, 0)` |

## Métodos e fontes

| Critério | Método | Fonte |
| --- | --- | --- |
| Reputação global | Simple Additive Weighting (SAW) | MacCrimmon (1968), em https://arxiv.org/pdf/2509.06388 (secção 8.2) |
| Qualidade | Média bayesiana | https://en.wikipedia.org/wiki/Bayesian_average |
| Utilidade, Colaboração, Melhoria contínua | Normalização linear do SAW | https://reference-global.com/download/article/10.2478/scjme-2022-0016.pdf (Tabela 1) |
| Fiabilidade | Sistema de pontos por infração | https://www.gov.pt/servicos/consultar-os-pontos-da-carta-de-conducao |

## Adaptações aos métodos

- **Normalização linear:** a fonte divide pelo máximo observado; aqui divide-se por um
  valor de referência fixo, com teto em 100, porque ainda não há dados reais e para a
  reputação de um utilizador não depender da atividade dos outros.
- **Média bayesiana:** a média de partida devia ser a média de toda a plataforma; usa-se
  3 (meio da escala de 1 a 5) enquanto não houver avaliações.
- **Sistema de pontos:** penalização fixa por infração, porque o modelo de domínio ainda
  não distingue gravidades.

## Constantes

Os pesos vêm da RN-100. As restantes são valores iniciais, sem dados que os suportem,
a recalibrar com os dados do piloto.

| Constante | Valor | Critério |
| --- | --- | --- |
| `MEDIA_DE_PARTIDA` | 3 estrelas | Qualidade |
| `PESO_DA_MEDIA_DE_PARTIDA` | 10 | Qualidade |
| `INTERACOES_DE_REFERENCIA` | 100 | Utilidade |
| `CONTRIBUICOES_DE_REFERENCIA` | 20 | Colaboração |
| `SUGESTOES_DE_REFERENCIA` | 10 | Melhoria contínua |
| `PENALIZACAO_POR_INFRACAO` | 25 pontos | Fiabilidade |

## Consequências a conhecer

- Sem avaliações, a Qualidade é 50 (a média de partida).
- Um utilizador novo começa com reputação 30: Qualidade 50 e Fiabilidade 100.
- Quatro infrações confirmadas levam a Fiabilidade a 0.

## Exemplo

Média 4,5 em 8 avaliações, 40 consultas e 20 downloads, 3 comentários e 1 sugestão
úteis, 2 sugestões incorporadas, sem infrações:
Q = 66,7; U = 60; C = 20; M = 20; F = 100; **R = 54**.

## Por definir

- A RN-105 não diz se as sugestões contam para quem as fez ou para quem as aceitou.
- O modelo de domínio não tem entidade para consultas e downloads, nem forma de marcar
  um comentário como útil.
- A leitura dos indicadores na base de dados depende dos modelos de outros epics.