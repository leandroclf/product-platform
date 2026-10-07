# Consumer installation

Prefer immutable release artifacts after a `v*` release exists.

Before the first tagged release, consumers may pin an exact Git commit:

```json
{
  "dependencies": {
    "@leandroclf/product-platform-harness": "github:leandroclf/product-platform-harness#<full-commit-sha>"
  }
}
```

The `prepare` script builds `dist` during Git dependency installation. Never depend on `main` or an unpinned branch in a product.

Migration rule: introduce the pinned dependency, switch imports, run product CI/integration tests, then delete the superseded local shared implementation.

## Private repository CI

Do not depend on the private Git repository URL from another repository CI. The Harness CI produces a commit-addressed npm tarball plus SHA256SUMS. Cross-repository consumers must use an authenticated artifact/package distribution mechanism and pin the immutable digest/version. Keep compatibility wrappers until that path is configured and validated.
