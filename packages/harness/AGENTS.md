# AGENTS.md

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
