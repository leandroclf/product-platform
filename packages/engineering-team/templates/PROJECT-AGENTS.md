# Project Agent Adapter

## Objetivo central: evolução autônoma dos produtos

A Product Platform existe para que agentes executem trabalho de engenharia de ponta a ponta e evoluam continuamente os produtos do ecossistema da empresa, a partir de objetivos e backlog autorizados. Autonomia é entregar resultados verificáveis com intervenção humana nas decisões necessárias.

- Dentro do escopo autorizado, inspecione, planeje, implemente, teste, corrija falhas, valide e prepare a entrega; prossiga entre etapas sem pedir novamente autorização já concedida.
- Não encerre no plano, na sugestão ou na criação de um PR quando ainda houver trabalho autorizado executável. Continue até os critérios de aceite ou registre um bloqueio concreto com evidência e próxima ação.
- Use o `ai-team` e suas sessões isoladas; preserve REUSE > EXTEND > CREATE e os donos canônicos das capacidades. Não introduza outro orquestrador só para obter autonomia.
- Para trabalho longo, mantenha checkpoints e evidências vinculados a tarefa, repositório, base e HEAD; respeite orçamento, cancelamento, locks e detecção de falta de progresso. Uma interrupção com efeito incerto exige reconciliação antes de repetir.
- Autonomia não concede autorização para produção, credenciais, permissões, operações destrutivas, merge ou deploy. Aplique as autorizações já existentes e os gates pertinentes; não amplie o escopo nem fabrique aprovações.
- Só relate como concluído o resultado demonstrado pelos checks e critérios de aceite. Diferencie implementação local, revisão, merge, publicação e operação contínua.

Operação e limites: `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md` na raiz da plataforma.

Adapt only after reading existing instructions. For local `ai-team`, this file belongs in the target repository when needed; installation and `init` do not copy it automatically. Keep real checks here and configure their offline equivalents explicitly through `ai-team init`. See [onboarding](../docs/PROJECT-ONBOARDING.md).
## System purpose
<what this repository does>
## Architecture
<components, boundaries, critical flows>
## Native commands
- setup: <command>
- test: <command>
- lint/typecheck: <command>
- build: <command>
## Constraints
<compatibility, regulatory, performance and data rules>
## Ownership / sensitive areas
<paths and required approvals>
## Deployment
<environments and rules>
## Local Definition of Done
<additional project gates>
