# Objective

Atualizar somente a seção “Regras da plataforma (kit e harness)” em packages/engineering-team/docs/LOCAL-LINUX-WORKFLOW.md para distinguir o gate obrigatório de capacidades em trabalho de novo produto ou capacidade transversal de tarefas locais sem mudança de capacidades, que podem omitir --handoff e usar capability_decisions vazio; incluir um exemplo de chamada local sem --handoff.

## Original request

Atualize apenas a secao Regras da plataforma (kit e harness) em packages/engineering-team/docs/LOCAL-LINUX-WORKFLOW.md para esclarecer que o gate de capacidades e obrigatorio antes do PLAN em trabalho de novo produto ou capacidade transversal; tarefas locais sem mudanca de capacidades podem omitir --handoff e devem usar capability_decisions vazio, sem bloquear apenas pela ausencia de capacidades. Inclua um exemplo de chamada local sem --handoff. Preserve todo o resto do documento. Risco R0/R1; nao altere codigo, schema, regras nem validadores. Critérios: texto coerente com packages/engineering-team/AGENTS.md e packages/engineering-team/docs/CAPABILITY-RESOLUTION-GATE.md; exemplo válido; escopo somente nesse trecho documental.

## Out of scope

- Alterar qualquer outra seção ou arquivo.
- Alterar código, schemas, regras da plataforma ou validadores.

## Acceptance

- AC1: O texto esclarece que o gate de capacidades é obrigatório antes de PLAN para trabalho de novo produto ou capacidade transversal, em coerência com packages/engineering-team/AGENTS.md e docs/CAPABILITY-RESOLUTION-GATE.md.
- AC2: A seção contém um exemplo válido de chamada local sem --handoff para tarefa sem mudança de capacidades e explica que capability_decisions fica vazio, sem bloquear apenas pela ausência de capacidades.
- AC3: As alterações ficam restritas à seção “Regras da plataforma (kit e harness)” em packages/engineering-team/docs/LOCAL-LINUX-WORKFLOW.md; o restante do documento é preservado.
