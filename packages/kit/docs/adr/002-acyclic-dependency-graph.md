# ADR 002: Acyclic repository dependency graph

ai-kit is a leaf shared kernel: it depends on no product or orchestration repository. OmniCLI, ai-engineering-team and products may consume versioned ai-kit artifacts. Products must not import other product repositories.

Cross-product integration, when genuinely required, uses an explicit runtime/API/event contract rather than source-code dependency.

This prevents circular ownership and makes every reusable capability traceable to one canonical repository.
