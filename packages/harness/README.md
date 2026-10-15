# product-platform-harness

Reusable runtime capabilities for products in the portfolio.

## Modules

- `core`: plans, entitlements and usage policy.
- `growth`: product events, sales signals and CRM/analytics boundaries.
- `commerce`: provider-neutral payments, subscriptions and webhook contracts.
- `economics`: payment economics and FinOps ledger primitives.
- `observability`: privacy-safe common telemetry attributes.

Products keep domain logic and product-specific adapters/configuration. Shared behavior is implemented here once, released immutably, and consumed by products. Contracts and portfolio ownership remain in `product-platform-kit`.

## Initial adoption

Latest verified release (2026-10-14): `harness-v0.2.1`, published with the TypeScript tarball,
Python wheel and `SHA256SUMS`. The stricter
event validator rejects previously accepted unknown fields; validate adapters
before upgrading from the `0.1.0` pilot artifact.

`vehicle-tracking` consumes the `harness-v0.2.0` tarball from commit
`b3375495bd86b6ee01d8430419496cbc492fbb49`; `bussola-financeira` consumes the
`harness-v0.2.1` wheel from `4040e76bbd0ff8b5933550121b07201010919bf5`.
Their `vendor/harness-artifact.json` files record the version and checksum.
Local changes require a new immutable release before consumer adoption. Current primitives do not implement
durable usage metering, webhook inbox or outbox delivery.

Python ProductEvent runtime is now maintained in `packages/python`, using the
`product_platform_harness` import. Previous kit packages remain frozen compatibility
snapshots until consumers migrate. `npm run validate` runs build, TypeScript tests
and Python standard-library tests against the canonical kit corpus
(`../kit/contracts/product-event/fixtures/compatibility-cases.json`); there is no local copy.
`PRODUCT_EVENT_CASES` overrides the path. Runtime validators reject unknown fields and invalid
metadata; typed callers alone do not provide this boundary.
