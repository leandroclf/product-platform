# Team distribution

## Goal
Developers should not need to understand every AI integration before they can use the organization's engineering guidance.

AI Kit therefore uses a central policy plus a small project manifest.

## Project contract
Copy `ai-kit.yaml` to a project and keep `project.profile: auto` unless the repository needs an explicit override.

Capability values:
- `auto`: profile/task may recommend activation.
- `off`: never activate automatically.
- `on`: project explicitly requires the capability, subject to credentials and platform permissions.

Security-sensitive capabilities should default to `off`. `auto` is a recommendation mechanism, not authorization.

## Agent behavior
Both agent entry points should:
1. inspect repository-local instructions;
2. inspect `ai-kit.yaml` when present;
3. infer the smallest relevant profile;
4. load only relevant skills;
5. request/require explicit intent before privileged operations;
6. verify work using repository-native commands.

This removes manual skill selection from the common path without enabling every tool globally.

## Versioning
Use semantic releases for the central kit. Projects should pin a compatible range or release and receive update notifications. Do not silently consume `main` in production development environments.

Recommended policy:
- patch: safe automatically reviewable fixes;
- minor: new backward-compatible skills/capabilities;
- major: behavior, manifest or security-policy breaking changes.

## Rollout
1. Validate the kit itself in CI.
2. Tag a release.
3. Pilot it in one backend and one frontend repository.
4. Compare agent behavior and developer friction.
5. Roll out to the wider team only after the pilot.

## Update model
A future updater should fetch release metadata, show the diff/policy changes, run `doctor`, and only then update the pinned version. Automatic forced updates are intentionally avoided because central AI instructions can materially change agent behavior.
