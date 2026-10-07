# Tasks

- [x] Baseline per-stage token and tool-output profile from a real task (bbdf40eb).
- [x] Shared token-discipline rules inserted into every stage prompt (`with_efficiency`).
- [x] RTK for Codex stages: read-only mount, stage-scoped AGENTS.md, telemetry off, fingerprint recorded in `stage_runs[].tools`.
- [x] `ai-team efficiency` and HTML report section (tokens, cache, tool output, top commands, repeated reads, RTK status).
- [x] Unit tests (tests/unit/test_token_efficiency.py) and a real Codex probe proving RTK use inside the stage container.
- [x] Advanced research with measurements (fixed overhead, turns x context, thinking share, behavior of agents); corrected the repeated-read metric.
- [x] Sharper shared rules, Codex batching instructions, quota warning before run, indicator strip in watch, per-stage turns/context/thinking metrics and recommendations.
- [x] Compare the validation run against the baseline (RESULT in proposal.md): cycle-1 tokens -38%, Claude cost -19%, one sample per side.
- [x] Surface exhausted provider limits with reset time (watch strip, health, warning before run).
- [ ] Repeat the comparison on a second task to confirm the gain is not run-to-run variance.
- [x] Argus split into fresh sessions behind `implement_parts` (default 1), with progress handoff, per-session metrics and tests.
- [ ] A/B run on the same task with `--implement-parts 2` against the single-session baseline; adopt as default only if tokens and cost drop at equal gate results (blocked until the Codex limit resets on 2026-10-05 01:32).
- [ ] Operator decision: effort tuning per stage.
- [ ] Operator decision on the Headroom sidecar experiment (read-only stages only, A/B, ephemeral, memory off).
- [x] Validate configured models/efforts against each CLI catalog (`ai-team models`; checked in `init` and `run`); refuse credit-billed models.
- [x] Per-stage model profile for the validation project with rationale (save on the producer, keep strong and diverse verifiers).
- [ ] A/B run for the Sonnet 5.5 producer (quality gates, tokens, cost) before touching framework defaults.
