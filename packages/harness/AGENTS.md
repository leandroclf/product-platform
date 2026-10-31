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
`product-platform-harness` é o runtime reutilizável embutido nos produtos do portfólio. Os contratos e a propriedade das capacidades ficam em `product-platform-kit`; este repositório os implementa. Esteira completa: `product-platform-kit/docs/PLATFORM-DELIVERY-FLOW.md`.

## Ownership
- Dono: core (planos, entitlements, identidade), growth (ProductEvent, sinks, sinais de venda), commerce (gateways Stripe e Mercado Pago), economics (ledger) e observability (atributos seguros).
- Não contém lógica de domínio de produto, banco central, control plane obrigatório, roteador dinâmico de modelos nem contrato de ProductEvent próprio. Ver `product-platform-kit/contracts/product-harness-ownership.yaml`.
- Depende somente do kit.

## Regras de mudança
- O schema do ProductEvent é do kit. Alterações de vocabulário ou campos começam em `packages/kit/contracts/product-event/`; o harness valida sempre contra `../kit/contracts/product-event/fixtures/compatibility-cases.json` e não mantém cópia do fixture.
- Falha de sink nunca derruba a requisição; entitlements decididos no servidor; eventos sem PII, GPS, IMEI, documentos ou credenciais.
- Consumidores fixam SHA completo ou artefato com checksum (`docs/CONSUMING.md`); nunca publique mudança que quebre adapters pinados sem nova versão.
- Não declare como implementado o que o registry do kit lista como `planned` (inbox durável, outbox, ledger persistido, reserva atômica de uso, OTEL).

## Verificação
- `npm run validate` (build, testes TypeScript e unittest Python). Reporte o resultado real; não relaxe testes ou tipos para obter build verde.
- `dist/` e artefatos de build: confirme `.gitignore` antes de commitar.

## Instruções de agente
Siga `AGENTS.md` do kit para o fluxo geral (inspecionar, menor mudança coesa, verificar, reportar evidência).
