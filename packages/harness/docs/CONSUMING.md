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
