<div align="center">

# AI Kit

### A portable control plane for AI-assisted software engineering

**One engineering policy. Multiple coding agents. The right capabilities, only when your project needs them.**

[![CI](https://github.com/leandroclf/ai-kit/actions/workflows/validate.yml/badge.svg)](https://github.com/leandroclf/ai-kit/actions/workflows/validate.yml)
[![GitHub stars](https://img.shields.io/github/stars/leandroclf/ai-kit?style=flat)](https://github.com/leandroclf/ai-kit/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/leandroclf/ai-kit?style=flat)](https://github.com/leandroclf/ai-kit/network/members)
[![Issues](https://img.shields.io/github/issues/leandroclf/ai-kit)](https://github.com/leandroclf/ai-kit/issues)

Built for **OpenAI Codex**, **Claude Code**, and agent-driven engineering workflows.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Token efficiency](#token-efficiency) · [Architecture](docs/ARCHITECTURE.md) · [Distribution](docs/DISTRIBUTION.md) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why AI Kit?

Coding agents are becoming part of the engineering toolchain, but teams quickly hit a new class of problems: instructions drift between repositories, every agent receives different context, always-on tools increase context/permissions, developers must remember which skills to activate, and shared standards turn into giant prompt files.

**AI Kit treats agent configuration as engineering infrastructure.** It provides a small central policy layer that detects project needs, routes agents toward reusable skills, recommends task-specific capabilities and keeps privileged integrations disabled until required.

```text
                    ┌──────────────────────────┐
                    │         AI Kit           │
                    │ central engineering      │
                    │ policy + token policy    │
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
        frontend    backend    devops    security   fullstack
                                 │
                     relevant skills + tools
```

## Core ideas

**Portable policy** — reusable engineering rules live in skills instead of being duplicated across agent configurations.

**Progressive activation** — browser, database, infrastructure and security capabilities are loaded only when relevant.

**Token-aware by default** — small entry points, on-demand skills/tools, concise output and adaptive reasoning reduce wasted context without weakening verification.

**Agent-native adapters** — Codex and Claude share policy without forcing both into an artificial lowest common denominator.

**Verification over confidence** — agents discover and run the repository's own lint, typecheck and tests.

**Least privilege** — automatic detection recommends capabilities; it does not grant credentials or authorization.

## Quick start

```bash
git clone https://github.com/leandroclf/ai-kit.git
cd ai-kit
bash scripts/doctor.sh .
bash scripts/ai-kit /path/to/project
```

Preview bootstrap without modifying your machine:

```bash
bash scripts/bootstrap.sh
```

Applying machine changes requires explicit opt-in:

```bash
AI_KIT_MODE=apply bash scripts/bootstrap.sh
```

## Token efficiency

AI Kit includes `config/token-policy.yaml`, a portable policy derived from current official OpenAI and Anthropic guidance.

The default strategy is deliberately simple:

- keep `AGENTS.md` and `CLAUDE.md` short;
- load skills and optional tools on demand;
- use concise output for routine coding work;
- start routine work at low reasoning/effort and escalate when complexity or failed verification justifies it;
- compact long-running sessions at meaningful milestones;
- prefer durable filesystem/git state over repeatedly injecting large summaries;
- optimize for **tokens per successfully verified task**, not tokens per individual call.

The last point matters: forcing minimum reasoning everywhere can create retries and consume *more* tokens. AI Kit uses adaptive escalation instead.

See [Token-efficient agent configuration](docs/TOKEN_EFFICIENCY.md) for the Codex and Claude policies and links to the official platform guidance.

## How it works

| Layer | Responsibility |
| --- | --- |
| Agent entry points | `AGENTS.md` and `CLAUDE.md` enter the policy system with minimal always-on context. |
| Project manifest | `ai-kit.yaml` declares project preferences and capability policy. |
| Token policy | `config/token-policy.yaml` defines portable efficiency defaults and escalation rules. |
| Skills | `skills/*/SKILL.md` contains reusable guidance loaded when relevant. |
| Profiles | `profiles/*.md` groups capabilities by engineering task. |
| Tool catalog | `config/tools.yaml` describes core, optional and privileged integrations. |

## Profiles

| Profile | Typical use | Capabilities |
| --- | --- | --- |
| `core` | Any repository | repository workflow, current documentation, engineering/testing policy |
| `frontend` | React, Next.js, Vue, Svelte, Angular | UI guidance, browser inspection, Playwright |
| `backend` | APIs, services, persistence, messaging | contracts, integrations, data guidance |
| `devops` | CI/CD, containers, Kubernetes, cloud | infrastructure guidance and validation |
| `security` | security reviews and sensitive changes | security skill, Strix, browser verification where relevant |
| `fullstack` | cross-boundary product work | frontend + backend with progressive activation |

## Security model

Capability selection and authorization are separate concerns. A profile may determine that database access would help; that does not authorize production database access. Loading security guidance does not authorize intrusive testing.

Baseline: no credentials in this repository, optional tools only when relevant, privileged operations require explicit intent, bootstrap previews changes, and production mutation is never implied by analysis.

## Repository structure

```text
.
├── AGENTS.md
├── CLAUDE.md
├── ai-kit.yaml
├── adapters/
├── config/
│   ├── token-policy.yaml
│   └── tools.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DISTRIBUTION.md
│   ├── GETTING_STARTED.md
│   └── TOKEN_EFFICIENCY.md
├── profiles/
├── scripts/
└── skills/
```

## For teams

The intended model is a versioned central AI Kit consumed by many repositories. Projects retain local business rules while inheriting common engineering and token-efficiency policy. Updates should be versioned and reviewable instead of silently following `main`.

See [Team distribution](docs/DISTRIBUTION.md).

## What AI Kit is not

AI Kit is not another coding agent, an autonomous production deployment system, or a reason to enable every MCP/tool globally. It is the policy and capability-routing layer around coding agents.

## Roadmap

Near-term priorities include native configuration generators for Codex and Claude Code, idempotent project initialization/update, manifest schema validation, release pinning, richer stack detection and example projects.

See [ROADMAP.md](ROADMAP.md).

## Contributing

Contributions are welcome, especially portable skills, profiles, stack detectors, token-efficiency improvements and safe integrations. Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

If AI Kit solves a problem in your workflow, consider starring the repository — it helps other engineers discover the project.

## License

A license has not yet been selected. Before broad external adoption, the project should add an explicit open-source license. Until then, standard copyright rules apply.
