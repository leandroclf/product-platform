# Frontend Profile

Activate for web UI work.

Adds:
- `skills/ui/SKILL.md`
- Browser interaction and visual review for every new or materially changed user flow, through a browser-capable runner.
- Playwright CLI for responsive, interaction, accessibility and regression checks when installed in that runner.

Keep backend/database/infra tooling disabled unless the feature crosses those boundaries.

In the canonical `ai-team` workflow, the implementation stage has no Bash or MCP access. Browser checks must run in the host-controlled, offline `quality_checks.frontend` environment. The current workflow hands text logs to validation/review, not screenshot files; until visual artifacts can be handed off for direct inspection, mark visual acceptance as not evaluated or blocked. A passing build or textual check summary is not visual acceptance.

If the task only changes copy or another non-visual detail, keep verification scoped to that change.