# AGENTS.md

## Mission
Use this repository as a portable AI-engineering control layer. Prefer project-local instructions when they are more specific.

## Operating rules
1. Inspect the target repository before proposing or changing code.
2. Identify stack, package manager, build system, tests and repository-specific instructions.
3. Read `skills/engineering/SKILL.md` and `skills/testing/SKILL.md` for implementation work.
4. Load specialized skills only when relevant: UI for frontend work and security for security-sensitive work.
5. Do not invent commands, dependencies, APIs or requirements. Verify them from the repository or authoritative documentation.
6. Prefer minimal, reversible changes that follow existing architecture and conventions.
7. Never weaken tests, linting, typing or security controls merely to make a check pass.
8. Validate changed behavior with the narrowest useful checks, then run broader project checks when practical.
9. Summarize changed files, verification performed, remaining risks and follow-up work.

## Tool activation
- Core: repository inspection, GitHub and current documentation.
- Browser/E2E: activate Playwright only for tasks that need browser interaction or UI verification.
- UI: activate UI/UX guidance for visual/interface work.
- Security: activate Strix/security tooling for explicit security analysis, sensitive changes or pre-release review.
- Data/Infra: activate database/cloud/Kubernetes capabilities only when the task requires them.

## Source of truth
Reusable guidance belongs in `skills/`. Profiles under `profiles/` describe which capabilities should be active for a class of task.
