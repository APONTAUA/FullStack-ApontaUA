# Fluxo de branches

## Fluxo de trabalho

1. Atualizar a branch `dev` local com `origin/dev`.
2. Criar cada branch de trabalho a partir de `dev`.
3. Abrir um pull request da branch de trabalho para `dev`.
4. Depois da integração e validação em `dev`, abrir um pull request de `dev` para `main`.
5. Não integrar branches de trabalho diretamente em `main`.

O workflow `.github/workflows/branch-direction.yml` rejeita PRs para `main` cuja origem não seja `dev`, e rejeita PRs de `main` para `dev`.

## Proteções no GitHub

Como o repositório agora é público, o GitHub Free permite configurar rulesets para proteger `dev` e `main`.

Quando a proteção estiver disponível, criar rulesets ativos para `dev` e `main`, sem atores de bypass:

- Aplicar a cada branch a regra **Require a pull request before merging**.
- Em `main`, exigir também o status check **Validate branch direction** do workflow *Branch direction*.
- Em `dev`, exigir o status check **Validate branch direction** depois de o workflow estar ativo.
- Não permitir bypass por administradores ou outras funções, se o objetivo for impedir pushes diretos também por esses utilizadores.

Com essas regras, os PRs de branches de trabalho podem entrar em `dev`, mas apenas um PR de `dev` pode entrar em `main`. A regra **Require a pull request before merging** bloqueia atualizações diretas às branches protegidas.

Até os rulesets estarem ativos, o workflow consegue marcar como falhado um PR com direção incorreta, mas não consegue impedir que alguém faça merge ou push direto. O fluxo depende de todos os contribuidores seguirem o processo documentado.

## Ativação inicial

1. Integrar este workflow em `dev` através de um PR de uma branch de trabalho.
2. Criar o ruleset de `dev` com PR obrigatório e sem bypass.
3. Criar o ruleset de `main` com PR obrigatório e sem bypass. Para o primeiro PR de promoção, confirmar manualmente que a origem é `dev`.
4. Integrar esse primeiro PR `dev` → `main`. Como o workflow ainda não existe na branch base `main`, a verificação automática de origem só poderá ser usada nos PRs seguintes.
5. Depois de o workflow executar num PR para `main`, adicionar o status check **Validate branch direction** ao ruleset de `main`. Adicionar o mesmo check ao ruleset de `dev` depois de executar num PR para `dev`.

Branches de trabalho devem ser criadas a partir de `dev`; esta convenção está documentada, enquanto o workflow valida a direção dos PRs e bloqueia PRs de trabalho para `main`.
