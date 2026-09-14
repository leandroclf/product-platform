# AI Kit

Portable AI engineering environment for software projects using **OpenAI Codex** and **Claude Code**.

The goal is to keep a small, safe core enabled by default and activate specialized capabilities only when a project needs them.

## Principles

- Repository instructions first: agents read project context before changing code.
- Progressive activation: UI, browser, security, database and infrastructure tooling are opt-in.
- One source of truth: shared engineering rules live under `skills/`; `AGENTS.md` and `CLAUDE.md` stay thin.
- Verification over assumption: changes are validated with the project's own lint, typecheck and tests.
- Least privilege: external tools get only the access required for the current task.

## Suggested profiles

| Profile | Capabilities | Default |
| --- | --- | --- |
| Core | GitHub, Context7/documentation, repository skills | On |
| Frontend | UI/UX guidance and browser inspection | Off |
| E2E | Playwright CLI | Off |
| Security | Strix/security review | Off |
| Backend | API, database and integration guidance | Off |
| DevOps | Docker, Kubernetes and cloud guidance | Off |

> Exact package/plugin identifiers for Strix and the UI skill must be validated before automated installation is added. The kit deliberately avoids installing an ambiguous package by name.

## Structure

```text
.
├── AGENTS.md
├── CLAUDE.md
├── README.md
├── profiles/
│   ├── core.md
│   ├── frontend.md
│   ├── backend.md
│   ├── devops.md
│   └── security.md
└── skills/
    ├── engineering/SKILL.md
    ├── testing/SKILL.md
    ├── ui/SKILL.md
    └── security/SKILL.md
```

## Usage

1. Clone or reference this kit from a project.
2. Keep `core` active.
3. Select the smallest additional profile required by the task.
4. Read the relevant `SKILL.md` files before implementation.
5. Run the project's native verification commands before considering work complete.

## Activation examples

- Backend API: `core + backend`
- React/Next.js: `core + frontend`; use Playwright when browser verification is required
- Infrastructure: `core + devops`
- Security review: `core + security`
- Full-stack release: combine only the profiles actually required

The next evolution can add reproducible installers and configuration generators for Codex and Claude after the exact plugin/package identifiers are validated.
