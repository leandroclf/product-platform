# Product workload roadmap

Status: active after synthetic convergence decision.

The engineering runtime is now structurally settled. The next objective is to use maintained products to expose missing capabilities and improve the runtime only when product evidence requires it.

## Priority order

### P0 — Bússola Financeira
Use a deterministic backend/data task. Prefer official-source ingestion, provenance, schema validation or deterministic analytical behavior. Avoid turning the benchmark into investment advice or an LLM-quality contest.

Expected capability pressure: Python/FastAPI, data contracts, provenance, deterministic testing, security.

### P1 — FiveM Server Monitor Pro
Use a bounded production-readiness task from the existing beta backlog, preferably framework compatibility, authorization, resilience or observability.

Expected capability pressure: Node/runtime integration, security, observability, packaging and release evidence.

### P1 — AI Docs
Use a bounded document-processing reliability task: queue idempotency, callback correctness, schema validation or deterministic fallback.

Expected capability pressure: Python/FastAPI, AWS queues/storage, idempotency, async failure handling.

### P2 — Yukz canonicalization
Before using Yukz as a workload, choose the canonical frontend and backend repositories and document predecessor relationships. Do not benchmark against multiple generations of the same product.

Expected capability pressure: TypeScript, Supabase/auth, realtime, maps, multi-tenant boundaries.

### P2 — Legal/CNJ
First document bounded contexts and canonical ownership among ingestion, communication, workflow and agent capabilities. Then select a task crossing no more than one bounded-context boundary.

Expected capability pressure: event ingestion, idempotency, document lineage, delivery contracts.

## Runtime evolution rule

A product workload may add or modify an ai-engineering-team skill only when all are true:

1. the capability is missing or materially weak in the canonical catalog;
2. the need recurs beyond one repository-specific implementation detail;
3. the proposed skill is smaller than introducing a new runtime/service/gateway;
4. deterministic validation can demonstrate the intended behavior;
5. the addition does not duplicate an existing stable skill.

## Explicit non-goals

- no dynamic provider router;
- no additional control plane;
- no bulk import of the 246 reference skills;
- no learned model router or extra classifier call; the demonstrated token-efficiency requirement is handled by deterministic routing for unmistakably small documentation tasks;
- no architecture work disconnected from a product workload.

## Completion criterion

This phase is complete after at least three different product families have supplied bounded workloads without requiring another orchestration layer. At that point, remaining legacy orchestration repositories can be evaluated for archival based on uniqueness rather than speculation.
