# Harness SDKs

These are source reference packages for the shared, language-specific implementation of canonical ai-kit contracts.

- harness-ts: TypeScript ProductEvent core
- harness-python: Python ProductEvent core

They deliberately contain no product-specific sinks, CRM, payment gateway adapters or domain policies. Products retain those integrations locally.

Publishing/versioned distribution is a separate release step; consumers must not copy these files manually once package distribution is enabled.
