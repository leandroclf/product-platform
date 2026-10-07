# Consumer conformance

Consumers pin a product-platform-kit release/commit and run the canonical conformance runner or validate their emitted fixture against `contracts/product-event/v1.schema.json`.

The conformance kit owns event vocabulary, required metadata and forbidden additional fields. Product repositories own only their event emission points, sinks and domain-specific policy.

Do not fork the schema into a new product-owned contract. Compatibility copies must declare the pinned product-platform-kit contract version and are transitional.

## Platform handoff

O handoff entre o product-platform-cli e o product-platform-engineering-team segue `contracts/platform-handoff/v1.schema.json` (fixture em `contracts/platform-handoff/fixtures/valid.json`). `scripts/validate-platform-handoff.py` valida o contrato e confere capacidades e donos contra `contracts/capability-registry.yaml`; `scripts/validate-platform-handoff.test.py` cobre as condições de parada. Não bifurque o schema: referências de regras usam SHA completo.
