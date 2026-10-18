# Portfolio convergence and product boundaries

## Canonical responsibilities

The four product-building modules share the single repository `leandroclf/product-platform`; the listed paths are modules, **not independent Git repositories**. The `ai-engineering-control-plane` project remains a separate experimental repository.

The portfolio deliberately separates four concerns.

| Canonical module or repository | Canonical responsibility | Must not become |
| --- | --- | --- |
| `product-platform/packages/engineering-team` | Execute bounded software-engineering work through isolated plan, implement, validate and review stages and preserve evidence | Dynamic model gateway, general-purpose idea discovery tool, central policy repository |
| `product-platform/packages/cli` | Turn ambiguous product/engineering intent into a challenged, reviewable proposal before implementation | Code-execution runtime |
| `product-platform/packages/harness` | Reusable runtime embedded in products: identity, plans, entitlements, product events, payment adapters, economics, safe observability | Product domain logic, central database, mandatory control plane |
| `product-platform/packages/kit` | Reusable engineering policies, skills, profiles and agent-native adapters | Competing orchestration/control plane |
| `ai-engineering-control-plane` | Architectural laboratory/reference for governance concepts not yet justified in the local runtime | Default runtime or mandatory dependency |

## Preferred flow

```text
rough intent
   |
   v
product-platform/packages/cli (optional)
   |
   v
reviewed proposal / bounded task
   |
   v
product-platform/packages/engineering-team
   |
   +--> product-platform/packages/kit policies / skills when useful
   |
   v
verified branch / PR + evidence
```

A project may enter directly at `product-platform/packages/engineering-team` when the task is already bounded. No repository above is allowed to add a gateway, router, database, graph, service or agent merely to make this diagram more uniform.

## Decision rule for consolidation

A capability moves into the canonical runtime only when a real workload demonstrates a recurring problem and the candidate capability improves a measurable outcome without unacceptable security, operational or maintenance cost.

The default for overlapping infrastructure is therefore **do not merge code yet**. First measure it, then either absorb the smallest useful capability or retire the duplicate.

## Current portfolio policy

1. New orchestration work belongs in `product-platform/packages/engineering-team`.
2. Reusable policy/skill content belongs in `product-platform/packages/kit` or the team's versioned skill catalog, with one canonical source chosen before duplication.
3. Proposal-generation work remains in `product-platform/packages/cli`.
4. New control-plane infrastructure is frozen unless an end-to-end benchmark exposes a concrete requirement that cannot be solved more simply.
5. Product repositories are preferred as real workloads for evaluation.

## Skill catalog provenance still under verification

`skills/catalog.yaml` now identifies the consolidated `leandroclf/product-platform` repository. The separate `skills/ownership.yaml` still points at `leandroclf/ai-kit` as the historical canonical upstream for generic skills. **Do not treat that legacy path as a verified, accessible repository** or silently copy skills from it. Before changing the canonical ownership policy, compare the current kit and engineering-team catalogs, confirm the authoritative distribution path and test consumers; keep the snapshot rule in force until that decision is evidenced.
