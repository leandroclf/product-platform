# AGENTS.md

## Mission
Use this repository as a portable AI-engineering control layer. Prefer more-specific project-local instructions.

## Default workflow
1. Inspect the target repository, stack, build/test commands and local instructions.
2. Read `skills/engineering/SKILL.md` and `skills/testing/SKILL.md` for implementation work.
3. Load specialized skills only when relevant; do not preload unrelated guidance.
4. Verify commands, dependencies and APIs from the repository or authoritative documentation.
5. Make the smallest cohesive change that follows existing architecture.
6. Run the narrowest useful checks first, then broader project checks when practical.
7. Report changed files, verification, remaining risks and unverified assumptions concisely.

## Token efficiency
Follow `config/token-policy.yaml`. Keep routine responses concise, avoid repeating repository context already available in files, and use the lowest reasoning effort that reliably completes and verifies the task. Escalate reasoning for genuinely complex work or after a low-effort attempt fails. For long-running work, compact/refresh context at meaningful milestones rather than carrying irrelevant history indefinitely.

## Capability activation
- Core: repository inspection, GitHub and current documentation.
- Browser/E2E: Playwright only when browser interaction or UI verification is needed.
- UI: UI guidance only for interface work.
- Security: Strix/security tooling only for authorized security analysis or sensitive changes.
- Data/Infra: database/cloud/Kubernetes capabilities only when required.

Relevance is not authorization. Privileged operations still require explicit intent and appropriate credentials.

## Source of truth
Reusable guidance belongs in `skills/`; profiles select task-relevant capabilities. Do not duplicate detailed policy in this entry point.
