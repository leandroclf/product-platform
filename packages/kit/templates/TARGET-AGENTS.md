# AGENTS.md (repositório alvo)

## Objetivo central: evolução autônoma dos produtos

A Product Platform existe para que agentes executem trabalho de engenharia de ponta a ponta e evoluam continuamente os produtos do ecossistema da empresa, a partir de objetivos e backlog autorizados. Autonomia é entregar resultados verificáveis com intervenção humana nas decisões necessárias.

- Dentro do escopo autorizado, inspecione, planeje, implemente, teste, corrija falhas, valide e prepare a entrega; prossiga entre etapas sem pedir novamente autorização já concedida.
- Não encerre no plano, na sugestão ou na criação de um PR quando ainda houver trabalho autorizado executável. Continue até os critérios de aceite ou registre um bloqueio concreto com evidência e próxima ação.
- Use o `ai-team` e suas sessões isoladas; preserve REUSE > EXTEND > CREATE e os donos canônicos das capacidades. Não introduza outro orquestrador só para obter autonomia.
- Para trabalho longo, mantenha checkpoints e evidências vinculados a tarefa, repositório, base e HEAD; respeite orçamento, cancelamento, locks e detecção de falta de progresso. Uma interrupção com efeito incerto exige reconciliação antes de repetir.
- Autonomia não concede autorização para produção, credenciais, permissões, operações destrutivas, merge ou deploy. Aplique as autorizações já existentes e os gates pertinentes; não amplie o escopo nem fabrique aprovações.
- Só relate como concluído o resultado demonstrado pelos checks e critérios de aceite. Diferencie implementação local, revisão, merge, publicação e operação contínua.

Operação e limites: `docs/AUTONOMOUS-PRODUCT-EVOLUTION.md` na raiz da plataforma.

Este produto segue a esteira da plataforma. Fonte canônica: `product-platform-kit/docs/PLATFORM-DELIVERY-FLOW.md`.

## Versões das regras
- product-platform-kit: `<SHA ou tag>`
- product-platform-harness: `<SHA ou versão pinada em vendor/harness-artifact.json>`
- registry_fingerprint da proposta: `<sha256>`

## Regras obrigatórias
- Depender somente de product-platform-kit e product-platform-harness, com versão imutável; nunca de outro produto.
- Resolver capacidades em REUSE > EXTEND > CREATE; não reimplementar eventos, entitlements, pagamentos, ledger ou observabilidade que o harness já possui.
- ProductEvent v1 do kit sem fork; `product_id` e `release_sha` obrigatórios; sem PII, GPS, IMEI, OCR ou credenciais.
- Falha de analytics/CRM não pode quebrar a requisição; entitlements decididos no servidor.
- Migrações EXPAND aplicadas pelo produto, nunca no startup; rollback só de código.

## Comandos do projeto
- Lint: `<comando>`
- Testes: `<comando>`
- Build: `<comando>`
- Conformance de ProductEvent: `<comando>`

Estas regras podem ser endurecidas aqui, nunca enfraquecidas.
