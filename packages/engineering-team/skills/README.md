# Skills

The canonical reusable engineering skills are in `leandroclf/product-platform/packages/kit/skills`. The `packages/engineering-team/skills` copies are compatibility snapshots until versioned distribution is available.

## Update contract

1. Change the canonical skill in `packages/kit/skills/<skill>/SKILL.md`.
2. Update the matching team snapshot **in the same PR**, preserving exact file contents.
3. Run `python3 packages/engineering-team/scripts/validate_skills.py` from the monorepo root or the package CI. The validator fails on missing sources, divergent content, and any new divergence waiver.
4. Review security-related skill edits as policy-sensitive changes; confirm the kit and team consumers before merge. Snapshot parity does not prove safe behavior by a model.

## Security reconciliation

The former security exception has been removed. Both consumers now use the same structured security skill with the original kit's threat categories and guarded optional analyzer usage plus the team's Inputs/Outputs/Boundaries/Validation sections. Third-party scanners (including Strix) are never installed or enabled implicitly: verify exact origin/version/permissions and obtain explicit operator authorization. Keep the canonical kit as the only source for subsequent changes.

Do not add duplicate generic skill content to the engineering-team without first modifying the kit. Remove snapshots only after a versioned runtime distribution and consumer compatibility validation are in place.

## Distribuição candidata

`scripts/policy_bundle.py` na raiz já empacota as skills canônicas com versão,
commit e hashes e testa instalação/igualdade de bytes. Esse piloto não altera
a resolução de skills do runtime local nem autoriza remover os snapshots.
A migração do consumidor precisa preservar catálogo, precedência, pins e rollback
e passar por uma tarefa autenticada antes da remoção das cópias.
