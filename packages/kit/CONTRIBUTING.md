# Contributing to AI Kit

Thanks for helping make AI-assisted engineering more portable, predictable and safe.

## Good contributions

AI Kit especially welcomes:

- reusable engineering skills that are not tied to one private codebase;
- improvements to stack/profile detection;
- Codex and Claude Code adapters;
- safe integrations with developer tooling;
- tests and validation for the manifest/catalog;
- examples and documentation based on real engineering workflows.

## Design principles

Contributions should preserve these constraints:

1. Keep the default core small.
2. Do not grant privileges merely because a capability is relevant.
3. Keep shared policy in `skills/`, not duplicated across agent entry points.
4. Prefer repository-native verification over invented commands.
5. Keep machine-changing setup explicit and reviewable.
6. Never commit credentials, tokens or environment-specific secrets.
7. Avoid platform lock-in when policy can remain portable.

## Development workflow

Fork the repository or create a feature branch, make a focused change, and run the repository validation before opening a pull request.

```bash
bash scripts/doctor.sh .
bash scripts/bootstrap.sh
bash -n scripts/*.sh scripts/ai-kit
```

Bootstrap should remain non-mutating unless `AI_KIT_MODE=apply` is explicitly provided.

## Pull requests

A useful pull request explains:

- the problem being solved;
- why it belongs in the central kit rather than one project;
- behavior or policy changes;
- security/permission implications;
- verification performed;
- compatibility or migration considerations.

Keep PRs focused. Broad unrelated rewrites make central policy changes harder to review safely.

## Adding a skill

A skill should have a clear activation condition, portable guidance, observable quality expectations and no embedded secrets. It should complement rather than duplicate existing skills.

## Adding an integration

Before adding an external tool, verify its canonical source and installation method. Document what access it requires, whether it changes the machine, whether it can execute privileged actions and which profiles should expose it.

Optional or privileged integrations must not become globally enabled merely because they are available.

## Reporting bugs and proposing features

Open an issue with a minimal example, expected behavior, actual behavior and relevant environment information. For security vulnerabilities, do not publish exploit details in a public issue; follow the repository security policy once a private reporting channel is configured.

## Community expectations

Be constructive, technical and evidence-driven. Challenge designs rather than people, disclose assumptions, and prefer reproducible evidence when discussing agent behavior or tool compatibility.
