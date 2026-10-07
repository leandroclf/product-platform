# product-harness bootstrap specification

This directory is a temporary bootstrap source only until the dedicated repository exists. It is not a runtime package and must be removed from ai-kit after repository materialization.

## Required repository layout

```
product-harness/
  packages/
    core/
    growth/
    commerce/
    economics/
    observability/
    adapters/
  migrations/
    expand/
    contract/
  examples/
    minimal-product/
  tests/
    contract/
    integration/
    e2e/
  .github/workflows/
    ci.yml
    release.yml
  package.json
  pnpm-workspace.yaml
  README.md
```

## CI gate

1. frozen dependency install
2. lint/typecheck
3. unit tests
4. ai-kit contract conformance
5. PostgreSQL integration tests
6. migration from empty DB
7. migration from previous Harness release
8. package build
9. minimal-product E2E

## Release

Release one immutable version for the workspace. Consumers pin the version. No package may depend on a product repository.

## Deployment contract

The Harness itself has no production deployment. A consuming product performs:

validate -> build immutable artifact -> EXPAND migrations -> deploy -> health -> smoke -> synthetic Harness checks -> observe.

CONTRACT migrations are a later release after old application versions are no longer in service.
