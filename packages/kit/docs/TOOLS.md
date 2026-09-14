# Verified tooling

This document records external integrations that have been verified against their canonical upstream documentation.

## Context7

Purpose: retrieve current library/framework documentation for coding agents.

Setup:

```bash
npx ctx7 setup
```

The setup is client-aware. Do not commit API keys generated or requested during setup.

Canonical source: `upstash/context7`.

## Playwright CLI

Purpose: browser automation for coding agents, UI verification and E2E workflows.

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
```

Prefer CLI + skills for ordinary coding-agent browser work. Use a richer persistent browser integration only when the workflow specifically benefits from it.

Canonical source: `microsoft/playwright-cli`.

## Strix

Purpose: authorized application-security testing and remediation workflows.

Install agent skills:

```bash
npx skills add usestrix/strix
```

Optional self-hosted CLI:

```bash
pipx install strix-agent
```

The CLI requires Docker plus an explicitly configured LLM provider/key. Never hardcode or commit credentials. Security scans are not automatically run by AI Kit. Only test systems you own or have explicit authorization to test.

Canonical source: `usestrix/strix`.

## UI skill

The originally discussed UI skill is still intentionally unresolved. AI Kit includes its own neutral `skills/ui/SKILL.md`, but no third-party package is installed until its exact canonical name/repository is confirmed.

## Activation policy

`core` is the baseline. Browser, database, infrastructure and security tooling is capability-scoped. Profile detection is advisory; it never grants credentials, executes a deployment or starts a security scan.
