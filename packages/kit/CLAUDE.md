# CLAUDE.md

This repository provides shared engineering guidance for Claude Code and other coding agents.

## Start here
- Inspect the target project and obey its local conventions.
- Read `skills/engineering/SKILL.md` and `skills/testing/SKILL.md` before implementation.
- Use `skills/ui/SKILL.md` only for interface work.
- Use `skills/security/SKILL.md` when security is in scope.
- Use the matching document under `profiles/` to choose optional capabilities.

## Guardrails
- Do not duplicate business rules between this file and the skills.
- Do not guess dependency APIs; use current authoritative documentation.
- Do not perform broad rewrites when a focused change solves the problem.
- Do not bypass tests, typing, linting or security controls to obtain a green build.
- Treat destructive commands, production changes and credential handling as high-risk operations requiring explicit intent.
- Finish with evidence: commands/checks run, results, risks and any unverified assumptions.
