# Skills

The canonical reusable engineering skill source is **`leandroclf/product-platform/packages/kit/skills`**, inside the same monorepo as the `engineering-team`. The local `packages/engineering-team/skills` catalog and skill files are compatibility snapshots consumed by the existing team tooling.

## Update contract

1. Update generic skill content in `packages/kit/skills/<skill>/SKILL.md` first.
2. Refresh the matching `packages/engineering-team/skills/<skill>/SKILL.md` snapshot in the same proposed PR, or provide a reviewed cutover path.
3. Run `python3 packages/engineering-team/scripts/validate_skills.py` from the repository root (or run the corresponding CI). The validator rejects missing canonical skills or newly divergent snapshots.
4. Keep both copies only until versioned runtime skill distribution is established. Avoid a second long-term source of truth.

## Known exception requiring a separate decision

**`security` is the sole documented divergence**, tracked explicitly in `skills/ownership.yaml`. The canonical kit currently contains a legacy Security Skill document (including conditional Strix guidance), while the engineering-team snapshot has structured frontmatter and `Inputs/Outputs/Boundaries/Validation` contract sections. Blind copying in either direction could break consumers or discard security guidance. The validator blocks *additional* undocumented drift but does not certify this exception as resolved or equivalent.

Reconcile that skill only in a follow-up with affected consumer checks, security review and compatibility tests. The exception is not a waiver to bypass other security policy, GitHub branch protection or human PR review.
