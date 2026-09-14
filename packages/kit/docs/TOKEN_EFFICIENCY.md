# Token-efficient agent configuration

AI Kit keeps token efficiency as a first-class engineering constraint. The objective is not to minimize tokens at any cost; it is to avoid spending context and reasoning on information or capabilities that are irrelevant to the current task.

This policy is based on current official OpenAI and Anthropic guidance. Platform-specific settings should remain in adapters while the shared principles stay portable.

## Shared defaults

1. Keep `AGENTS.md` and `CLAUDE.md` small. Put reusable detail in skills and load only the skill relevant to the task.
2. Keep optional tools disabled until required. Tool definitions and tool output consume useful context even when the task does not need them.
3. Prefer concise final responses for routine coding work. Increase explanation depth only when the task or reviewer needs it.
4. Use the lowest reasoning effort that reliably passes project verification. Escalate for architecture, ambiguous debugging, migrations, security-sensitive work or failed attempts.
5. Do not repeatedly inject large repository summaries. Re-discover durable state from files/git when that is cheaper and more reliable.
6. Compact or refresh long-running sessions around meaningful milestones rather than carrying an ever-growing transcript indefinitely.
7. Preserve stable instruction prefixes where the platform can cache them; avoid rewriting global instructions on every turn.

## OpenAI / Codex policy

OpenAI's current model guidance explicitly exposes reasoning effort and output verbosity as cost/latency controls. Lower reasoning effort uses fewer reasoning tokens; low verbosity produces shorter output. OpenAI also recommends intentional compaction for long-running, tool-heavy agent workflows and preserving stable prompts/state to benefit from caching.

AI Kit therefore recommends this operational policy for Codex-compatible workflows:

```yaml
codex:
  token_policy:
    reasoning:
      default: low
      escalate_to: medium
      high_only_when: complex_or_eval_justified
    output:
      verbosity: low
    context:
      compact_at_milestones: true
      keep_entry_instructions_small: true
      load_skills_on_demand: true
      preserve_stable_instruction_prefix: true
```

This is a policy contract, not a promise that every Codex client exposes every key above with identical configuration syntax. Native adapters must map only settings supported by the installed Codex version.

### Escalation rule

Use `low` for routine repository discovery, focused implementation, tests and mechanical refactoring. Move to `medium` when the task requires non-trivial planning or a low-effort attempt fails. Use `high`/`xhigh` only when task difficulty or evaluation evidence justifies the additional reasoning cost.

Do not force the lowest possible effort when doing so increases retries: a failed cheap run followed by repeated re-reading can consume more tokens than one appropriately reasoned run.

## Anthropic / Claude Code policy

Anthropic's current guidance emphasizes context-aware long-running workflows and explicitly discusses Claude Code environments that compact context or persist state externally. It notes that, depending on the task, starting a fresh context and reconstructing state from the filesystem can be preferable to carrying compacted history. Anthropic also recommends lowering effort to reduce thinking/token usage when high effort is unnecessary.

AI Kit therefore recommends:

```yaml
claude:
  token_policy:
    effort:
      default: low
      escalate_when: task_complexity_requires
    context:
      prefer_filesystem_state: true
      compact_long_sessions: true
      fresh_context_after_clean_milestone: preferred
      keep_claude_md_small: true
      load_skills_on_demand: true
```

Again, this is the portable policy. The Claude adapter should map it to native Claude Code settings/features only when they are officially supported by the installed version.

## What belongs in entry-point files

`AGENTS.md` / `CLAUDE.md` should contain only rules that are useful on almost every task:

- inspect the repository and local instructions;
- select the smallest relevant profile;
- load specialized skills only when required;
- use repository-native verification;
- keep responses concise by default;
- escalate reasoning/context only when task complexity requires it.

Large architecture explanations, framework tutorials, examples and tool manuals should not be copied into every agent turn. Keep them in project docs or skills and retrieve them when relevant.

## Token budget anti-patterns

Avoid:

- enabling all MCP/tools globally;
- duplicating the same policy in `AGENTS.md`, `CLAUDE.md`, profiles and skills;
- embedding entire architecture documents in agent entry points;
- requesting high reasoning for every task;
- verbose progress narration during routine implementation;
- repeatedly asking the agent to summarize files it can inspect directly;
- retaining obsolete debugging output in long-running context;
- compacting every turn instead of at useful boundaries.

## Quality guardrail

Token efficiency is subordinate to correctness. The optimization target is **tokens per successfully verified task**, not tokens per individual model call. If low effort causes regressions, repeated tool calls or failed tests, the adapter/profile should escalate reasoning for that class of task.

## Official references

- OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI compaction reference: https://developers.openai.com/api/reference/resources/responses/methods/compact
- Anthropic prompting / agentic context guidance: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/prompt-templates-and-variables
