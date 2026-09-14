<div align="center">

# AI Kit

### A portable control plane for AI-assisted software engineering

**One engineering policy. Multiple coding agents. The right capabilities, only when your project needs them.**

[![CI](https://github.com/leandroclf/ai-kit/actions/workflows/validate.yml/badge.svg)](https://github.com/leandroclf/ai-kit/actions/workflows/validate.yml)
[![GitHub stars](https://img.shields.io/github/stars/leandroclf/ai-kit?style=flat)](https://github.com/leandroclf/ai-kit/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/leandroclf/ai-kit?style=flat)](https://github.com/leandroclf/ai-kit/network/members)
[![Issues](https://img.shields.io/github/issues/leandroclf/ai-kit)](https://github.com/leandroclf/ai-kit/issues)

Built for **OpenAI Codex**, **Claude Code**, and agent-driven engineering workflows.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Profiles](#profiles) · [Architecture](docs/ARCHITECTURE.md) · [Distribution](docs/DISTRIBUTION.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why AI Kit?

Coding agents are becoming part of the engineering toolchain, but teams quickly hit a new class of problems:

- instructions drift between repositories and developers;
- every agent receives different context;
- too many always-on tools increase noise and permissions;
- developers have to remember which skill, MCP or browser tool to activate;
- shared engineering standards become giant prompt files that are hard to maintain;
- updates to AI workflows are difficult to distribute safely across many projects.

**AI Kit treats agent configuration as engineering infrastructure.**

It provides a small central policy layer that can detect project needs, route agents toward reusable skills, recommend task-specific capabilities and keep privileged integrations disabled until they are actually required.

```text
                    ┌──────────────────────────┐
                    │         AI Kit           │
                    │  central engineering     │
                    │       policy layer       │
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
            AGENTS.md       ai-kit.yaml      CLAUDE.md
                 │               │               │
                 └───────────────┼───────────────┘
                                 │
                        project detection
                                 │
                     smallest useful profile
                                 │
           ┌──────────┬──────────┼──────────┬──────────┐
           │          │          │          │          │
        frontend    backend    devops    security   fullstack
           │          │          │          │          │
           └──────────┴──────────┼──────────┴──────────┘
                                 │
                     relevant skills + tools
```

## Core ideas

**Portable policy** — engineering rules live in reusable skills instead of being duplicated across agent-specific configuration.

**Progressive activation** — browser, database, infrastructure and security capabilities are activated only when relevant.

**Agent-native adapters** — Codex and Claude can share policy without forcing both platforms into an artificial lowest common denominator.

**Verification over confidence** — agents are instructed to discover and run the repository's own lint, typecheck, tests and other validation commands.

**Least privilege** — automatic detection recommends capabilities; it does not grant credentials or authorization.

**Central governance without central friction** — teams can evolve policy centrally while projects pin compatible versions and retain local instructions.

## Quick start

Clone the repository and inspect the environment:

```bash
git clone https://github.com/leandroclf/ai-kit.git
cd ai-kit
bash scripts/doctor.sh .
```

Ask AI Kit which profile best matches a repository:

```bash
bash scripts/ai-kit /path/to/project
```

Preview the bootstrap process without modifying your machine:

```bash
bash scripts/bootstrap.sh
```

The bootstrap is intentionally **plan-only by default**. Applying machine changes requires explicit opt-in:

```bash
AI_KIT_MODE=apply bash scripts/bootstrap.sh
```

> Review commands and integrations before applying them in managed or production environments.

## How it works

AI Kit separates concerns into five layers:

| Layer | Responsibility |
| --- | --- |
| Agent entry points | `AGENTS.md` and `CLAUDE.md` tell each coding agent how to enter the policy system. |
| Project manifest | `ai-kit.yaml` declares project preferences, compatible kit versions and capability policy. |
| Skills | `skills/*/SKILL.md` contains reusable engineering, testing, UI and security guidance. |
| Profiles | `profiles/*.md` groups capabilities by type of engineering task. |
| Tool catalog | `config/tools.yaml` describes integrations and whether they are core, optional or privileged. |

The project detector inspects common repository markers and recommends the smallest useful profile. This recommendation is context selection, **not permission escalation**.

## Profiles

| Profile | Typical use | Capabilities |
| --- | --- | --- |
| `core` | Any repository | repository workflow, current documentation, engineering/testing policy |
| `frontend` | React, Next.js, Vue, Svelte, Angular | UI guidance, browser inspection, Playwright |
| `backend` | APIs, services, persistence, messaging | contracts, integrations, data guidance |
| `devops` | CI/CD, containers, Kubernetes, cloud | infrastructure guidance and validation |
| `security` | security reviews and sensitive changes | security skill, Strix integration, browser verification where relevant |
| `fullstack` | cross-boundary product work | frontend + backend capabilities with progressive activation |

### Example project manifest

```yaml
version: 1
kit:
  channel: stable
  update_policy: notify
  pin: "^0.1"

project:
  profile: auto
  agents:
    codex: true
    claude: true

capabilities:
  github: auto
  context7: auto
  playwright: auto
  strix: off
  database: off
  infrastructure: off
```

`auto` means *the task/profile may recommend this capability*. It does not mean an agent may silently obtain credentials or execute privileged operations.

## Integrations

AI Kit's catalog currently models capabilities around:

- GitHub-aware engineering workflows;
- Context7/current documentation;
- Playwright browser and E2E verification;
- Strix-assisted security analysis;
- UI engineering guidance;
- browser diagnostics;
- project-specific database access;
- Docker, Kubernetes and cloud infrastructure.

Not every integration belongs in every repository. The point of AI Kit is to make **selective activation the default**.

## Repository structure

```text
.
├── AGENTS.md                 # Codex / generic agent entry point
├── CLAUDE.md                 # Claude Code entry point
├── ai-kit.yaml               # project policy contract
├── adapters/                 # platform-specific adapter boundary
├── config/
│   └── tools.yaml            # declarative capability registry
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DISTRIBUTION.md
│   ├── SECURITY.md
│   └── TOOLING.md
├── profiles/                 # task-oriented capability profiles
├── scripts/
│   ├── ai-kit                # project/profile detector
│   ├── bootstrap.sh          # safe environment bootstrap
│   └── doctor.sh             # environment diagnostics
└── skills/
    ├── engineering/SKILL.md
    ├── security/SKILL.md
    ├── testing/SKILL.md
    └── ui/SKILL.md
```

## Security model

AI coding tools can interact with source code, browsers, credentials and infrastructure. AI Kit therefore assumes that **capability selection and authorization are different concerns**.

A profile may determine that database access would help. That does not authorize an agent to connect to a production database. Likewise, loading security guidance does not authorize intrusive testing.

The baseline is:

- no credentials in this repository;
- optional tools disabled until relevant;
- privileged operations require explicit intent;
- bootstrap previews changes before applying them;
- security findings must be validated before code is changed;
- production mutation is never implied by analysis.

See [Security](docs/SECURITY.md).

## For teams

The intended distribution model is a central AI Kit release consumed by many repositories:

```text
AI Kit release
     │
     ├── service-a  → backend profile
     ├── web-app    → frontend profile
     ├── platform   → devops profile
     └── product-x  → fullstack profile
```

Projects can keep local business rules while inheriting common engineering policy. Updates should be versioned and reviewable instead of silently following `main`.

See [Team distribution](docs/DISTRIBUTION.md).

## What AI Kit is not

AI Kit is **not** another coding agent, an autonomous production deployment system, or a reason to enable every MCP/tool globally.

It is the policy and capability-routing layer around coding agents: a way to make their behavior more predictable, portable and maintainable across real engineering teams.

## Roadmap

Near-term priorities include:

- native configuration generators for Codex and Claude Code;
- idempotent project initialization and updates;
- manifest schema validation;
- release/version pinning and update diffing;
- richer stack detection;
- reusable profile packs;
- project-local overrides without policy duplication;
- examples for frontend, backend and platform repositories.

See [ROADMAP.md](ROADMAP.md).

## Contributing

Contributions are welcome — especially new profiles, portable engineering skills, stack detectors, documentation improvements and safe agent integrations.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

If AI Kit solves a problem in your workflow, consider starring the repository. It helps other engineers discover the project and gives the project a useful signal about community interest.

## License

A license has not yet been selected. Before broad external adoption, the project should add an explicit open-source license. Until then, standard copyright rules apply.
