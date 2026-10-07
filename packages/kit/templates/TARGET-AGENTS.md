# AGENTS.md (repositório alvo)

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
