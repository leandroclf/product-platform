# product-harness

Reusable runtime capabilities for products in the portfolio.

## Modules

- `core`: plans, entitlements and usage policy.
- `growth`: product events, sales signals and CRM/analytics boundaries.
- `commerce`: provider-neutral payments, subscriptions and webhook contracts.
- `economics`: payment economics and FinOps ledger primitives.
- `observability`: privacy-safe common telemetry attributes.

Products keep domain logic and product-specific adapters/configuration. Shared behavior is implemented here once, released immutably, and consumed by products. Contracts and portfolio ownership remain in `ai-kit`.
