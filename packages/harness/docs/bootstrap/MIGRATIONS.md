# Migration contract

Harness migrations are product-applied artifacts.

Rules:
- EXPAND migrations are additive/backward compatible.
- application deploy happens only after EXPAND succeeds.
- rollback means rolling back application code, not destructive DB rollback.
- CONTRACT migrations are released separately after compatibility window.
- every migration is idempotently tracked.
- migrations never read secrets other than the product database connection.
- no Harness release may silently execute migrations at package import/startup.
