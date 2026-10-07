# End-to-end engineering benchmark

## Purpose

Measure whether the complete `ai-engineering-team` workflow improves verified engineering outcomes relative to simpler baselines. This complements the existing skill benchmarks; it does not replace them.

The benchmark optimizes for **verified useful work per unit of cost and time**, not raw token minimization.

## Conditions

For the same frozen task and repository revision, compare when the provider/environment permits:

1. `single-openai`: one OpenAI coding-agent session.
2. `single-claude`: one Claude coding-agent session.
3. `team`: Atlas/OpenAI plan -> Argus/Claude implement -> offline checks -> Sentinel/OpenAI validate -> Atlas/Claude review.
4. `human-assisted`: optional reference condition where a human may clarify or repair between stages; never mix this result with autonomous conditions.

Every condition must start from the same commit, receive the same task acceptance criteria, and run the repository's deterministic checks. Model IDs, effort, CLI versions and configuration are evidence, not hidden variables.

## Workload classes

The initial suite should contain real, bounded tasks from maintained product repositories:

| Class | Example workload | Primary signal |
| --- | --- | --- |
| bug-fix | failing regression with deterministic test | verified fix without unrelated change |
| backend-api | endpoint/contract change | contract + integration tests |
| refactoring | behavior-preserving structural change | tests + complexity/change scope |
| security | bounded vulnerability remediation | exploit/regression test + security review |
| performance | measurable hot-path improvement | benchmark threshold + correctness |
| brownfield | change in an unfamiliar existing codebase | verified completion + context efficiency |
| documentation | docs synchronized with executable behavior | link/contract checks + reviewer findings |
| architecture-change | multi-file bounded design change | acceptance coverage + rework |

Do not manufacture a task solely because it is easy for an agent. Prefer issues or changes that would otherwise be performed in the product.

## Required metrics

Each run records:

- `verified_pass`: all deterministic acceptance checks pass on the delivered SHA;
- `acceptance_coverage`: accepted criteria with preserved evidence / total criteria;
- `regression_count`: newly failing deterministic checks;
- `review_findings`: severity-counted independent findings;
- `repair_cycles`: implementation/repair cycles before final disposition;
- `elapsed_seconds`;
- input/output/cache tokens when exposed;
- provider-reported or reproducibly calculated cost when available;
- changed files and diff size;
- final disposition: `PASS`, `FAIL`, `BLOCKED` or `INCONCLUSIVE`.

A run without deterministic verification cannot claim success and is `INCONCLUSIVE`.

## Experimental discipline

- Pin the target repository SHA and task text.
- Preserve prompts, stage configuration, model/catalog evidence and final SHA.
- Never compare different task revisions as if they were repetitions.
- Run multiple repetitions before claiming a winner; one run is evidence, not a conclusion.
- Separate subscription/quota failures from engineering failures.
- Do not change the team defaults merely because one benchmark favors another configuration.
- Report negative results.

## Promotion criterion

A workflow/configuration becomes the default only when repeated real workloads show a material improvement in verified pass rate, rework, elapsed time or cost without a critical regression in security or correctness. If the team pipeline is more expensive without improving verified outcomes, prefer the simpler baseline.

## Initial product workloads

Candidates, subject to a bounded real task being available:

- `professional-english-coach`: frontend/learning-engine behavior and regression work;
- `bussola-financeira`: Python/FastAPI data lineage and deterministic analytics;
- `fivem-server-monitor-pro`: Lua/JS compatibility, security and packaging;
- `ai-docs`: Python/FastAPI asynchronous processing and document contracts;
- Yukz canonical repository after the tracking family is reconciled.

These repositories are workloads, not dependencies of the framework.
