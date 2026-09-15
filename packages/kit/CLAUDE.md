# CLAUDE.md

Shared engineering guidance for Claude Code. Prefer more-specific project-local instructions.

## Default workflow
- Inspect the target project and obey its local conventions.
- Read engineering/testing skills for implementation work; load UI/security skills only when relevant.
- Use the matching profile to select optional capabilities instead of enabling everything.
- Verify dependency APIs with authoritative documentation and use repository-native checks.
- Prefer focused changes over broad rewrites.
- Finish with concise evidence: checks run, results, risks and unverified assumptions.

## Token efficiency
Follow `config/token-policy.yaml`. Keep this entry point small and load detailed guidance on demand. Prefer durable project state in files/git over repeatedly carrying large summaries. For long tasks, use context compaction when useful; after a clean milestone, a fresh context that reconstructs state from the filesystem may be cheaper and clearer. Use low effort for routine work and escalate only when task complexity or failed verification justifies it.

## Guardrails
- Do not duplicate business rules between this file and skills.
- Do not bypass tests, typing, linting or security controls to save tokens or obtain a green build.
- Destructive commands, production changes and credential handling require explicit intent.
- Capability relevance never implies authorization.
