# Cross-repository duplication register

Candidates are reviewed, never auto-refactored solely because code looks similar.

| Capability | Current copies | Canonical owner | Migration |
|---|---|---|---|
| ProductEvent create/emit | vehicle-tracking, ai-docs (historical), bussola-financeira | product-platform-harness runtime / product-platform-kit contract | v1 conformance; frozen kit SDKs until migration |
| generic engineering skills | product-platform-engineering-team, product-platform-kit | product-platform-kit | compatibility snapshots until distribution |
| ProductEvent schema validation | vehicle-tracking, product-platform-kit | product-platform-kit | consumer conformance runner |
| payment gateway contract | vehicle-tracking | product-platform-kit contract / product adapters | contract centralized; adapters local |
| engineering proposal boundary | product-platform-cli / team docs | product-platform-cli contract | v1 handoff |

Rule of Three applies to runtime implementations. Domain-specific similarities are not sufficient grounds for extraction.
