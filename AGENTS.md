# Instruções para agentes

## Objetivo central: evolução autônoma dos produtos

A Product Platform existe para que agentes executem trabalho de engenharia de ponta a ponta e evoluam continuamente os produtos do ecossistema da empresa, a partir de objetivos e backlog autorizados. Autonomia é entregar resultados verificáveis com intervenção humana nas decisões necessárias.

- Dentro do escopo autorizado, inspecione, planeje, implemente, teste, corrija falhas, valide e prepare a entrega; prossiga entre etapas sem pedir novamente autorização já concedida.
- Não encerre no plano, na sugestão ou na criação de um PR quando ainda houver trabalho autorizado executável. Continue até os critérios de aceite ou registre um bloqueio concreto com evidência e próxima ação.
- Use o `ai-team` e suas sessões isoladas; preserve REUSE > EXTEND > CREATE e os donos canônicos das capacidades. Não introduza outro orquestrador só para obter autonomia.
- Para trabalho longo, mantenha checkpoints e evidências vinculados a tarefa, repositório, base e HEAD; respeite orçamento, cancelamento, locks e detecção de falta de progresso. Uma interrupção com efeito incerto exige reconciliação antes de repetir.
- Autonomia não concede autorização para produção, credenciais, permissões, operações destrutivas, merge ou deploy. Aplique as autorizações já existentes e os gates pertinentes; não amplie o escopo nem fabrique aprovações.
- Só relate como concluído o resultado demonstrado pelos checks e critérios de aceite. Diferencie implementação local, revisão, merge, publicação e operação contínua.

Operação e limites: `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md` na raiz da plataforma.

## Fluxo de pull requests

- Neste repositório, enquanto não houver branch de desenvolvimento no remoto, crie a branch de trabalho a partir de `main` e abra o PR para `main`. Esta exceção ao Gitflow global foi solicitada para o fluxo deste projeto; não presume promoção ou deploy em outros ambientes.
- Para desbloquear PRs, investigue os checks, conflitos, revisões e regras de proteção efetivamente aplicáveis; preserve a identidade e o SHA exato de cada revisão.
- Delegue a um subagente revisor independente a análise de PRs com código ou alterações em segurança, pagamentos, dependências, permissões ou pipelines. Use `backend_code_reviewer` para backend e `code_reviewer` para mudanças gerais, quando disponíveis; delimite base, HEAD e escopo e peça achados com evidências e limitações.
- O subagente atua em somente leitura e não aprova, publica reviews nem faz merge. Avalie e corrija os achados antes de solicitar a revisão necessária no GitHub; um parecer local não substitui a aprovação da identidade exigida pelo gate.
- Verifique o parecer independente, os checks e o HEAD atual; registre a aprovação pela identidade revisora permitida no GitHub somente quando houver análise real favorável. Um parecer obsoleto ou achado bloqueante exige correção e nova revisão.
- Mantenha os controles de CI, revisão e proteção de branches. Siga a política de risco e o procedimento em `docs/AUTOMERGE-OPERATIONS.md`; PRs sensíveis não entram automaticamente no fluxo R1. Merge depende de solicitação explícita e dos controles aplicáveis; depois confira o estado do PR e os checks da `main`.
- Instruções específicas dos pacotes complementam estas regras. Os comandos e limites do monorepositório estão no `README.md`.
