# Synthetic convergence decision

Date: 2026-10-06  
Evidence class: **synthetic simulation — not provider benchmark**

## Decision

The simulated comparison exercises the same frozen English Coach restore workload across the logical conditions `single-openai`, `single-claude` and `team`. All conditions are intentionally assigned only the deterministic outcome already demonstrated by the merged product change: acceptance criteria satisfied and no regression detected by CI.

Provider-dependent measurements are not simulated. Token count, monetary cost, elapsed provider time, repair cycles and provider-specific review findings remain unknown.

Because the simulated conditions tie on the only defensible functional evidence, there is no basis for introducing dynamic model selection, a gateway or another control plane.

The portfolio therefore keeps the fixed isolated responsibility model:

1. OpenAI reasoning stage — planning.
2. Claude implementation stage — implementation.
3. OpenAI validation stage — validation.
4. Claude fresh-session review stage — review.

## Consolidation consequence

- `ai-engineering-team` remains the canonical bounded engineering runtime.
- `ai-kit` remains reusable policy/skills/profiles/adapters.
- `OmniCLI` remains an optional upstream proposal workflow.
- `ai-engineering-control-plane` remains a reference/architecture laboratory; its existing security scanner failure must not be bypassed merely to merge a documentation status change.
- `agents-workspace` and `agentesautonomos` remain legacy/reference.
- `codex-kit-skills` remains a source for selective skill migration.

## Selective skill migration

The canonical catalog already covers the core engineering domains: tech leadership, architecture, backend, QA, security, review, observability, Java/Spring, Node/TypeScript, Python/FastAPI, AWS, Kubernetes and GitHub delivery. The reference skill repository contains 246 skill documents, so bulk migration would increase context and maintenance cost. Candidate migration must therefore be demand-driven by a real workload and deduplicated against this catalog.

## Archive rule under simulation-only strategy

Simulation is sufficient to stop new development in redundant orchestration repositories. It is **not** sufficient to delete unique code. Physical repository archival should occur only after a uniqueness check confirms that required capabilities or references have either been migrated or intentionally abandoned.

This closes the architecture-choice phase. Future work should prioritize product workloads and selective simplification, not additional orchestration layers.
