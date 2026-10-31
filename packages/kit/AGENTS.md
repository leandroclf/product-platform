# AGENTS.md

## Objetivo central: evolução autônoma dos produtos

A Product Platform existe para que agentes executem trabalho de engenharia de ponta a ponta e evoluam continuamente os produtos do ecossistema da empresa, a partir de objetivos e backlog autorizados. Autonomia é entregar resultados verificáveis com intervenção humana nas decisões necessárias.

- Dentro do escopo autorizado, inspecione, planeje, implemente, teste, corrija falhas, valide e prepare a entrega; prossiga entre etapas sem pedir novamente autorização já concedida.
- Não encerre no plano, na sugestão ou na criação de um PR quando ainda houver trabalho autorizado executável. Continue até os critérios de aceite ou registre um bloqueio concreto com evidência e próxima ação.
- Use o `ai-team` e suas sessões isoladas; preserve REUSE > EXTEND > CREATE e os donos canônicos das capacidades. Não introduza outro orquestrador só para obter autonomia.
- Para trabalho longo, mantenha checkpoints e evidências vinculados a tarefa, repositório, base e HEAD; respeite orçamento, cancelamento, locks e detecção de falta de progresso. Uma interrupção com efeito incerto exige reconciliação antes de repetir.
- Autonomia não concede autorização para produção, credenciais, permissões, operações destrutivas, merge ou deploy. Aplique as autorizações já existentes e os gates pertinentes; não amplie o escopo nem fabrique aprovações.
- Só relate como concluído o resultado demonstrado pelos checks e critérios de aceite. Diferencie implementação local, revisão, merge, publicação e operação contínua.

Operação e limites: `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md` na raiz da plataforma.

## Mission
Use this repository as a portable AI-engineering control layer. Prefer more-specific project-local instructions.

## Default workflow
1. Inspect the target repository, stack, build/test commands and local instructions.
2. Read `skills/engineering/SKILL.md` and `skills/testing/SKILL.md` for implementation work.
3. Load specialized skills only when relevant; do not preload unrelated guidance.
4. Verify commands, dependencies and APIs from the repository or authoritative documentation.
5. Make the smallest cohesive change that follows existing architecture.
6. Run the narrowest useful checks first, then broader project checks when practical.
7. Report changed files, verification, remaining risks and unverified assumptions concisely.

## Token efficiency
Follow `config/token-policy.yaml`. Keep routine responses concise, avoid repeating repository context already available in files, and use the lowest reasoning effort that reliably completes and verifies the task. Escalate reasoning for genuinely complex work or after a low-effort attempt fails. For long-running work, compact/refresh context at meaningful milestones rather than carrying irrelevant history indefinitely.

## Capability activation
- Core: repository inspection, GitHub and current documentation.
- Browser/E2E: Playwright only when browser interaction or UI verification is needed.
- UI: UI guidance only for interface work.
- Security: Strix/security tooling only for authorized security analysis or sensitive changes.
- Data/Infra: database/cloud/Kubernetes capabilities only when required.

Relevance is not authorization. Privileged operations still require explicit intent and appropriate credentials.

## Source of truth
Reusable guidance belongs in `skills/`; profiles select task-relevant capabilities. Do not duplicate detailed policy in this entry point.
