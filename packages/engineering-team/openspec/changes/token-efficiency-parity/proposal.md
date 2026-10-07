# Token efficiency parity across the four stages

Status: IMPLEMENTED for RTK, shared token rules, measurement, indicators and quota warning (2026-10-04). Headroom and session splitting: DEFERRED. Risk: R2 (agent runtime and container mounts).

## Why
The host has RTK (output condensing) and Headroom (context proxy), but the isolated stages did not use either: the provider image has neither, and nothing routes stage traffic through a proxy. Measured on task bbdf40eb (real run, 14 files):

| Stage | Agent | Tokens in/out | Cache hit | Tool output | Shell |
|---|---|---|---|---|---|
| plan | Atlas / Codex | 396k / 8k | 82% | 236 KB (cat 223 KB) | yes |
| implement | Argus / Claude | 2.47M / 75k | 94% | 162 KB | no (Read/Grep/Glob/Edit/Write) |
| validate | Sentinel / Codex | 757k / 8k | 86% | 235 KB (sed 97, cat 82, nl 28) | yes |
| review | Atlas / Claude | 902k / 15k | 90% | 151 KB | no |

Findings: most volume is whole-file reads, which RTK does not condense (`cat` unchanged); files are re-read inside a stage (changes.patch x5, global.css x3); Claude stages have no Bash, so a Bash hook cannot apply to them.

## Decision per stage
- **All four stages**: shared token-discipline rules inserted before the request (`with_efficiency`): read once, targeted searches and ranges, batch calls, minimal narration. They never relax a required check.
- **Codex stages (plan, validate)**: RTK mounted read-only from the host (static binary, sha256 prefix recorded per stage run), stage-scoped instructions mounted read-only as the global AGENTS.md (`templates/codex-stage-AGENTS.md`), `RTK_TELEMETRY_DISABLED=1`. Full-content reads stay plain `cat`/`sed`; `rtk read --level minimal|aggressive`, `--max-lines` and `--tail-lines` are forbidden because reviewers need complete content.
- **Claude stages (implement, review)**: RTK is not applicable (no shell). Savings come from the shared rules and from `--max-turns`/effort bounds.
- **Measurement**: `ai-team efficiency [task]` and an HTML report section show per-stage tokens, cache hit, tool-output bytes, top commands, repeated reads and whether RTK was applied.

## Security requirements
- No new network path: mounts are read-only files; containers keep their current egress and hardening (`--read-only`, `--cap-drop ALL`, `no-new-privileges`, non-root).
- RTK telemetry stays off. RTK ignores project-local filters outside CI (`RTK_TRUST_PROJECT_FILTERS` has no effect), so an untrusted repository cannot hide output; do not set it.
- RTK is a host binary executed in the stage: version and fingerprint are recorded; the operator owns updates. A changed binary changes the recorded fingerprint.
- Condensed output is advisory: agents rerun a single command without `rtk` if output looks empty, truncated or contradicts an exit code.

## Headroom (not enabled)
Routing stage traffic through the host proxy is deferred because it would (1) put per-stage subscription credentials and prompts behind a shared host process that keeps memory and statistics, weakening stage and project isolation; (2) require a container-to-host network path; (3) apply lossy compression to tool results, which can break exact-match edits in the implement stage. The host proxy also reports 0 requests, so its benefit is unproven here.

Acceptable experiment, only with explicit operator approval: an ephemeral per-task sidecar (memory disabled, no telemetry, pinned version) on an internal Docker network that is the only egress of read-only stages (validate, review), measured A/B with `ai-team efficiency` against this baseline before any wider use.

## Acceptance
- Prompts of all four stages contain the shared rules; Codex stages mount RTK read-only; Claude stages mount nothing new (unit tests).
- Real Codex run in the stage container read the mounted instructions and executed `rtk rg` and `rtk git log` (2026-10-04 probe).
- Follow-up: compare the next real task's `ai-team efficiency` against the baseline above (repeated reads, tool output, tokens).

## Advanced research (2026-10-04, measured on this project)
Question: what really drives agent token cost here, and what can be applied safely?

Measured on task bbdf40eb (baseline):
- **Fixed prompt overhead is negligible.** First-request context of a Claude stage is about 5.1k tokens. `--disable-slash-commands` and `--exclude-dynamic-system-prompt-sections` change it by about 50 tokens: not worth adopting. `--bare` is not usable (it does not read OAuth credentials).
- **The cost driver is turns x growing context.** Argus: 27 turns, context 6k -> 153k tokens (median 113k), 2.47M context tokens re-read (94% cache hits), US$ 3.20. Review: 14 turns, 902k. Output is about 53% estimated thinking in Argus (about 40k of 75k).
- **Claude agents are already efficient in behavior:** 0 identical re-reads, 19 of 27 turns with parallel tool calls, 3 reads after edits. An earlier "files read more than once" metric counted different windows of the same file and was wrong; it was replaced by `identical` (waste) versus `windows` (chunked reading).
- **Codex stages**: 27 and 23 commands, about 240 KB of shell output each, 95% from `cat`/`sed` of whole files, which RTK does not condense. Cache hits 82-86%.

External guidance confirms the model: cached prefix is cheap (about 10% of input price) but is read on every turn; Codex `model_reasoning_effort=xhigh` costs several times more tokens than medium; `tool_output_token_limit` would truncate file content that reviewers need, so it is not used.

Applied (data-backed, low risk): sharper shared rules (plan reads, parallel batches, no re-reads, few well-formed edits), Codex instructions to read several files per command and prefer one `cat` over many `sed` windows, quota warning before `ai-team run`, per-stage turns/context/thinking metrics, rule-based recommendations carrying their numbers, and the watch indicator strip.

Evaluated, not applied (each needs evidence or a decision):
| Option | Why not now |
|---|---|
| Split Argus into several sessions by plan tasks | Cost is quasi-quadratic in turns, so it could cut context re-read substantially, but later sessions must re-read files earlier ones wrote (e.g. global.css); needs a refactor of stage naming, logs and panels; validate with an A/B run first |
| Lower `--effort` for implement/review | About half of Argus output is thinking, but this is a quality trade-off for the operator (`ai-team init --implement-effort`); no evidence yet that medium preserves quality |
| Headroom proxy | See Headroom section; isolation and edit-exactness risks, no measured benefit |
| Codex `tool_output_token_limit` / `model_verbosity` | Truncates evidence reviewers need / output is already small (8k) |
| Claude `--fallback-model`, `--bare` | Silent model change conflicts with "no fallback"; `--bare` needs an API key |

## Indicators (watch)
`ai-team watch` now opens with a strip of indicators: health (OK/ATTENTION/CRITICAL with reasons: idle time, stage timeout, turn budget, correction cycle, Claude quota), progress bar with ETA from the median duration of finished tasks, real Claude subscription quota from the stream's `rate_limit_event` (5h and 7d windows with reset time), turns against the budget, current and peak context, estimated thinking, pace sparkline, stage timeout bar and token rate. Finished tasks freeze their elapsed time.

## RESULT of the validation run (task 8450b73e vs baseline bbdf40eb, same request, cycle 1)
| Stage | Baseline | With the new rules | Change |
|---|---|---|---|
| plan (Codex) | 27 commands, 396k tokens in | 12 commands, 482k | commands -56%; tokens +22% (larger batched reads: 296 KB vs 236 KB) |
| implement (Claude) | 27 turns, 2.47M, US$ 3.20, peak 152k | 18 turns, 1.55M, US$ 2.65, peak 131k | tokens -37%, cost -17% |
| validate (Codex) | 23 commands, 757k | 13 commands, 444k | tokens -41% |
| review (Claude) | 14 turns, 902k, US$ 1.18 | 7 turns, 338k, US$ 0.91 | tokens -63%, cost -23% |
| Cycle total | 4.53M in, US$ 4.38 Claude | 2.82M in, US$ 3.56 Claude | tokens -38%, Claude cost -19% |

Reading the result honestly:
- One sample per side. Plans differ between runs, so treat the figures as indicative, not as a guaranteed percentage.
- The gain comes from the shared rules (plan reads, parallel batches, one `cat` for several files), visible as fewer turns. RTK was used on the commands it fits (`rtk rg`, `rtk git`: 2-4 per Codex stage) but file reads stay `cat`, so its effect on bytes is not observable here.
- The new run needed a second cycle because Sentinel legitimately failed cycle 1 (mobile panel positioned over content in global.css), so total tokens for the whole run (4.44M) were similar to the baseline. The extra cycle was cheap (implement US$ 0.57). Quality gates stayed intact.
- The run was then stopped by the ChatGPT usage limit of the Codex account (resets 2026-10-05 01:32), so end-to-end completion of this run was not demonstrated. The Claude 5h window went from 25% to 58% during the run.

Follow-up from this result: exhausted limits are now surfaced (watch strip, health, warning before `ai-team run`) with the provider's reset time instead of a truncated reason.

## Argus in smaller sessions (implemented behind `implement_parts`, default 1)
Hypothesis from the measurements: cost is quasi-quadratic in turns times context, so several fresh sessions should re-read less than one long session.

Design: `ai-team init --implement-parts N` (1 to 4; configs without the key keep working and behave as 1). The plan tasks are split into contiguous balanced groups; each group runs as its own Argus session with a fresh context in the same workspace. Sessions after the first receive `/handoff/progress.md` (tasks done, changed files, diff summary and summaries of earlier sessions) so they do not rediscover the work, and are told to read only what they need. The last session makes the OpenSpec task list and validation report consistent for the whole plan. The host still commits once, after all sessions; repair cycles always use a single session. Each session has its own prompt, log, staging and handoff (`<cycle>p<part>-implement`), counted separately in `ai-team efficiency` (`1/implement#2`) and shown as "sessao k/N" in the watch.

Risks: a later session must re-read files written by earlier ones (for example global.css), which can erase part of the saving; coherence across sessions depends on the progress note and on the final session. Hence default 1 until an A/B run on the same task shows lower tokens and cost at equal gate results.

## Model per stage (2026-10-05)
Request: lower token use by choosing a model per stage. Proposed: plan `gpt-6.1-sol`, implement `claude-sonnet-5-5`, validate `gpt-6-Luna`, review `claude-terra`, all medium.

Investigation (catalogs read from the stage account volumes, plus real CLI probes):
- `claude-terra` does not exist in the Claude catalog (`terra` exists only as `gpt-5.6-terra`); the CLI answers `unrecognized_model`. `gpt-6-Luna` is `gpt-6-luna` (case). The framework only checked the ID format, so both would have been accepted and failed at their own stage after the earlier stages spent quota.
- Descriptions in the catalogs: `gpt-6.1-sol` "latest workhorse for coding", `gpt-6-astra` "frontier intelligence for the most demanding work", `gpt-6-luna` "fast and affordable for easier tasks", Sonnet 5.5 "most efficient for simpler tasks", Opus 5.5 "for complex work".
- Cost lever, measured: Opus 5.5 costs about twice Sonnet 5.5 per token (US$ 0.0078 vs 0.0038, same prompt, cached path); Argus is about 75% of Claude spend and about 53% of its output was thinking at high effort. Codex stages read 400-760k tokens and reason 2-4k, so Codex effort barely changes token volume.

Applied to the validation project (framework defaults unchanged): plan `gpt-6.1-sol` medium; implement `claude-sonnet-5-5` medium; validate `gpt-6-astra` medium (an independent, strong gate that differs from the planner; it caught a real defect at xhigh); review `claude-opus-5-5` medium (differs from the Argus model, cheaper than high). Principle: save on the producer, keep strong and diverse verifiers.

Framework change: `ai-team models`, and `init`/`run` validate models and efforts against each CLI's catalog, refuse credit-billed models (never changes billing) and suggest the right ID.

Open: quality of Sonnet 5.5 as producer is untested on this project; validate with an A/B run (tokens, cost and gate results) before changing the framework defaults. Combined with `implement_parts=2` the effects are confounded; run them one at a time if quota allows.
