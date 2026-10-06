# Cross-repository duplication register

Candidates are reviewed, never auto-refactored solely because code looks similar.

| Capability | Current copies | Canonical owner | Migration |
|---|---|---|---|
| ProductEvent create/emit | vehicle-tracking, ai-docs, bussola-financeira | ai-kit | v1 conformance, then SDK packages |
| generic engineering skills | ai-engineering-team, ai-kit | ai-kit | compatibility snapshots until distribution |
| ProductEvent schema validation | vehicle-tracking, ai-kit | ai-kit | consumer conformance runner |
| payment gateway contract | vehicle-tracking | ai-kit contract / product adapters | contract centralized; adapters local |
| engineering proposal boundary | OmniCLI / team docs | OmniCLI contract | v1 handoff |

Rule of Three applies to runtime implementations. Domain-specific similarities are not sufficient grounds for extraction.
