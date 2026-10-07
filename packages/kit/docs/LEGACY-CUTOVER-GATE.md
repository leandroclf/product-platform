# Legacy repository cutover gate

The following repositories are superseded by the canonical Product Platform namespace:

| Legacy | Canonical |
|---|---|
| ai-kit | product-platform-kit |
| ai-engineering-team | product-platform-engineering-team |
| OmniCLI | product-platform-cli |
| product-harness | product-platform-harness |

A legacy repository is safe to delete only when all conditions are true:

- canonical `main` contains the complete source-file set;
- canonical CI is green;
- relevant open PR work is migrated or intentionally rejected;
- active repositories contain no dependency or documentation link to the legacy repository;
- package/install instructions point only to canonical repositories;
- Capability Registry, ownership and repository boundaries use canonical names;
- no deployment, release or automation workflow targets the legacy repository.

Deletion is a separate explicit operation. This gate never deletes repositories.
