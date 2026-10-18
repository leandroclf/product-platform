# Quality Gates
Apply proportionally to risk.
1. Requirements: acceptance conditions covered.
2. Build/static: native build, lint, formatting, typing or static analysis where configured.
3. Tests: focused tests; broader suite for higher-risk changes where practical.
4. Security: required for R2/R3 and trust-boundary changes.
5. Diff: review final diff for scope and regressions.
6. Evidence: record executed checks and outcomes.
A missing tool is not a passing gate: mark it NOT RUN with reason.

## Política de achados dos pareceres locais

No pipeline local `ai-team`, a entrega requer os pareceres de validação e revisão técnica no HEAD/plan_id exatos, com todas as condições de aceite aprovadas. Achados **CRITICAL, HIGH e MEDIUM** precisam estar `RESOLVED` e `verified=true`; a declaração `PASS_WITH_FINDINGS` isolada não os isenta. Um achado marcado `RESOLVED` em qualquer severidade precisa ter verificação positiva. Achados LOW/INFO podem permanecer `OPEN` sob `PASS_WITH_FINDINGS`, mas exigem inspeção e decisão explícita do proprietário do PR antes do merge; o parecer automático não é aceite humano de risco.

Esse check local não substitui o gate nativo GitHub nem a revisão manual atual. A avaliação de severidade informada pelo modelo não prova a gravidade real do problema; confirmar no diff e nos testes. Qualquer exceção para um achado MEDIUM+ exige um processo próprio de governança e **não** é suportada por este caminho de entrega.
