# Portfolio convergence status

Status: 2026-10-06

## Target state

The portfolio has one canonical bounded engineering runtime:

- **ai-engineering-team** — plan, implement, validate, review, evidence and delivery.
- **ai-kit** — reusable policies, skills, profiles and agent adapters.
- **OmniCLI** — optional upstream intent/proposal workflow.
- **ai-engineering-control-plane** — architecture laboratory/reference, pending its repository gate.
- **codex-kit-skills** — migration source/reference; do not add new orchestration.
- **agents-workspace** and **agentesautonomos** — legacy/reference; no new runtime development.

## Completed convergence actions

- Canonical boundaries and M13 added to ai-engineering-team.
- End-to-end workload contract added to CI.
- First workload frozen against professional-english-coach SHA `2883d73b173b8fadefe38f8a3479409a9649d228`.
- The selected real backlog task — validated, conflict-safe local backup restore — was implemented and passed the product CI.
- AI Kit scope was narrowed to reusable capability/policy.
- OmniCLI boundary was narrowed to pre-implementation proposal work.
- Legacy/reference status was documented in agents-workspace and agentesautonomos.
- codex-kit-skills was marked as a migration source rather than a new runtime.

## Evidence limitation

The first product workload proves that the task and deterministic verifier are viable. It is **not** a comparative OpenAI-vs-Claude-vs-team result because the three experimental conditions were not executed independently in their authenticated provider runtimes. Do not backfill or infer those measurements.

## Remaining gates

1. Run the frozen workload independently under `single-openai`, `single-claude` and `team` from the same pinned SHA.
2. Record tokens/cost/time and deterministic acceptance evidence.
3. Repeat across multiple real tasks before changing model/stage defaults.
4. Inspect codex-kit-skills and migrate only skills that improve measured outcomes or remove duplication.
5. Archive legacy repositories only after migration/reference checks confirm that no unique required capability remains.
6. Reconcile Yukz and Legal/CNJ families separately; choose canonical repositories before archival.

The convergence objective is achieved structurally when new orchestration has one home and legacy repositories stop diverging. Performance superiority remains an empirical question until authenticated benchmark runs exist.
