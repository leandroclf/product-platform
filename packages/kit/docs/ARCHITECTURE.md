# Architecture

AI Kit separates **instructions**, **capabilities** and **project-specific configuration**.

## Layers

### 1. Agent entry points
`AGENTS.md` and `CLAUDE.md` are intentionally thin. They define startup behavior and route agents toward reusable skills.

### 2. Skills
`skills/*/SKILL.md` contains reusable engineering policy. Skills describe how to work, not credentials or machine-specific setup.

### 3. Profiles
`profiles/*.md` describes task-oriented capability sets. A profile is a recommendation and must not be interpreted as blanket authorization.

### 4. Tool catalog
`config/tools.yaml` is the declarative inventory. Optional integrations are disabled by default. Ambiguous external tools remain unpinned until their canonical package/repository is verified.

### 5. Detection
`scripts/ai-kit` inspects common project markers and recommends a profile. Detection never grants permissions or modifies the target project.

## Why not enable everything globally?

A permanently enabled toolset increases context noise, attack surface, credential exposure and the chance an agent selects the wrong capability. The kit therefore keeps documentation/repository awareness in the core and makes browser, database, infrastructure and security capabilities task-scoped.

## Distribution model

Recommended evolution:

1. Keep this repository as the canonical source.
2. Version releases using semantic versioning.
3. Let projects pin a kit version rather than silently consuming `main`.
4. Provide installers/adapters for Codex and Claude that generate native configuration from `config/tools.yaml`.
5. Add CI validation for YAML, shell scripts, Markdown links and required skill structure.
6. Add an update command that shows changes before applying a newer kit version.

This avoids forcing developers to manually choose individual skills while still preventing uncontrolled automatic activation.
