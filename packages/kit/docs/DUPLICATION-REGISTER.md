# Cross-repository duplication register

Candidates are reviewed, never auto-refactored solely because code looks similar.

| Capability | Current copies | Canonical owner | Migration |
|---|---|---|---|
| ProductEvent create/emit | vehicle-tracking (harness tarball), ai-docs and bussola-financeira (both migrated to the harness Python wheel in `harness-v0.2.1`; local copies replaced by adapters) | product-platform-harness runtime / product-platform-kit contract | v1 conformance; legacy kit SDKs removed in the platform consolidation |
| generic engineering skills | product-platform-engineering-team (13 validated skills), product-platform-kit (16 short stubs) | product-platform-engineering-team for execution skills (validated catalog and ownership); kit keeps profiles and policy | decided at the consolidation: do not extend the kit stubs; retire each stub once its skill is covered and referenced from the profile (open follow-up) |
| ProductEvent schema validation | vehicle-tracking, product-platform-kit, product-platform-harness | product-platform-kit | harness validates against the kit corpus in CI; no local snapshot; consumers run the conformance runner |
| payment gateway contract | vehicle-tracking | product-platform-kit contract / product adapters | contract centralized; adapters local |
| engineering proposal boundary | product-platform-cli / team docs | product-platform-cli contract | v1 handoff |

Rule of Three applies to runtime implementations. Domain-specific similarities are not sufficient grounds for extraction.
