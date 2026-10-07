# ADR 002: Acyclic repository dependency graph

product-platform-kit is a leaf shared kernel: it depends on no product or orchestration repository. product-platform-cli, product-platform-engineering-team and products may consume versioned product-platform-kit artifacts. Products must not import other product repositories.

Cross-product integration, when genuinely required, uses an explicit runtime/API/event contract rather than source-code dependency.

This prevents circular ownership and makes every reusable capability traceable to one canonical repository.
