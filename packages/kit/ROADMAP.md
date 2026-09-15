# AI Kit Roadmap

AI Kit is evolving from a portable policy repository into a lightweight control plane for AI-assisted engineering teams.

This roadmap communicates direction, not guaranteed dates.

## Foundation — current

- Shared engineering/testing/UI/security skills
- Codex and Claude Code entry points
- Capability profiles
- Declarative tool catalog
- Safe bootstrap planning
- Project/profile detection
- CI validation
- Project manifest contract
- Environment doctor

## Next — distribution and automation

- Manifest JSON Schema and CI validation
- `init` workflow for adopting AI Kit in an existing repository
- Idempotent adapter generation
- Safe `update` workflow with policy diff before changes
- Release pinning and compatibility checks
- Expanded stack detection
- Example projects for frontend, backend and infrastructure

## Later — ecosystem

- Community profile/skill packs
- Integration metadata and compatibility matrix
- Policy composition and organization overlays
- Machine-readable capability risk levels
- Automated documentation/catalog generation
- Metrics for evaluating agent workflow quality without collecting source code

## Design constraints

Features should not trade away the principles that make the project useful:

- small default context;
- least privilege;
- explicit production/destructive intent;
- portable engineering policy;
- platform-native adapters where beneficial;
- versioned, reviewable updates;
- evidence-based verification.

## Proposing roadmap items

Open an issue describing the user problem first. Solutions that apply to multiple repositories and agents are more likely to belong in AI Kit than highly project-specific behavior.
