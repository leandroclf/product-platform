# Agent adapters

Adapters are the platform-specific edge of AI Kit. Shared engineering policy stays in `skills/` and must not be duplicated here.

## Codex
`AGENTS.md` is the repository entry point. It should remain small and route Codex toward the manifest, selected profile and relevant skills.

## Claude Code
`CLAUDE.md` is the repository entry point. It should apply the same central policy and manifest while preserving Claude-specific capabilities when useful.

## Adapter rule
Do not force both platforms into an artificial lowest common denominator. Keep business/engineering policy portable, but let each adapter use native platform features when they improve reliability or developer experience.

## Planned generator
A generator can eventually render/update project-local entry points from templates while preserving a clearly marked project-owned section. It must be idempotent and show a diff before overwriting existing instructions.
