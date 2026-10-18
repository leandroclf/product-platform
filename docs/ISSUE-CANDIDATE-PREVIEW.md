# Backlog → prévia de handoff no GitHub Actions

Etapa intermediária, sem modelos e sem credenciais externas: uma issue existente com label `agent-candidate` e bloco `autonomy-task` válido passa por um workflow GitHub Actions **somente de leitura**, que publica artefato JSON com `execution_allowed: false`.

## Como experimentar
1. Criar uma issue no `product-platform` com o contrato de `docs/AUTONOMOUS-TASK-HANDOFF.md`.
2. Aplicar o label `agent-candidate` (ou usar o botão **Run workflow** em `Agent candidate preview` informando o número).
3. Verificar execução de `Agent candidate preview` em Actions e obter o artefato `candidate-preview` com retenção limitada.
4. Confirmar que item R2/R3, PR disfarçado de issue, item fechado ou sem label são rejeitados.

## Limites
- Não altera issue, estado, labels ou branch; não cria commit, PR, execução de agente nem auto-merge.
- Não considera label uma autorização de implementação. Artefato é apenas uma prévia rastreável.
- O evento de issue usa o código da branch padrão, não executa scripts introduzidos pelo conteúdo da issue.
- Acesso ao artefato segue permissões do GitHub Actions; evite registrar segredos na issue.
- Para chegar à evolução autônoma é preciso autenticar o `ai-team`, integrar a revisão independente real, CI/rulesets, limites de custo e o fluxo de merge; ver `docs/AUTONOMY-PENDING-PC.md`.
