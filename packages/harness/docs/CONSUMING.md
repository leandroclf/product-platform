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

## Python

Build/install the Python package from `packages/python`. For a published source
revision, pin the full Git SHA and select the subdirectory:

```text
product-platform-harness @ git+https://github.com/leandroclf/product-platform-harness.git@<full-commit-sha>#subdirectory=packages/python
```

The directory is introduced after the first TypeScript pilot SHA; do not use that
older SHA for Python. Until a new revision is published, validate local artifacts:

```bash
python -m pip wheel --no-deps ./packages/python --wheel-dir /tmp/harness-wheels
```

Install the resulting wheel in an isolated environment and verify its SHA-256
before adoption. Canonical import: `from product_platform_harness import ProductEvents`.
The initial Python package supplies events only, not payments or usage persistence.
