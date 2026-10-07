# Skills

Canonical reusable engineering skills are owned by **ai-kit**.

This repository owns only engineering-agent orchestration (planner, implementer, validator, reviewer), skill selection/evaluation logic, and compatibility metadata required by the runtime.

## Migration rule

Do not add new generic skill content here. Add or update it in ai-kit, then consume the pinned ai-kit version/commit.

The existing skill files remain temporarily as compatibility snapshots until ai-kit distribution is versioned and the runtime can resolve external skills deterministically. CI must prevent new divergent copies during this transition.
