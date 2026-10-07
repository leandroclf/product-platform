# Consumer installation

Products live in their own repositories and consume the harness as an immutable **release artifact** of the platform repository (`leandroclf/product-platform`), tag `harness-v<version>`. They never depend on the source tree, on `main` or on an unpinned branch.

## TypeScript

Each release publishes `leandroclf-product-platform-harness-<version>.tgz` and `SHA256SUMS` (the release workflow requires the tag to match the TypeScript and Python versions, the commit to be on `main`, and the full validation to pass).

```bash
gh release download harness-v0.2.0 -R leandroclf/product-platform
sha256sum -c SHA256SUMS
```

Vendor the verified tarball in the product (`vendor/`), depend on it with `"@leandroclf/product-platform-harness": "file:vendor/leandroclf-product-platform-harness-<version>.tgz"` and record the release tag, the commit of the tag and the SHA-256 in a manifest that the product CI verifies. Reference implementation: the `vehicle-tracking` repository (`vendor/harness-artifact.json` and `scripts/validate-product-platform-artifact.cjs`).

Every commit that changes the harness also uploads a commit-addressed tarball with `SHA256SUMS` as a CI artifact (30 days); use it only for validation, not for production pins.

Migration rule: introduce the pinned dependency, switch imports, run product CI/integration tests, then delete the superseded local shared implementation.

## Python

The Python package (`product_platform_harness`, events only: no payments or usage persistence) is published from `harness-v0.2.1` on, as `product_platform_harness-<version>-py3-none-any.whl`, listed in the same `SHA256SUMS` as the TypeScript tarball.

```bash
gh release download harness-v0.2.1 -R leandroclf/product-platform
sha256sum -c SHA256SUMS
```

Vendor the verified wheel in the product (`vendor/`), install it from `requirements.txt` with its relative path, and record the release tag, the commit of the tag and the SHA-256 in a manifest that the product CI verifies. Reference implementation: the `ai-docs` repository (`vendor/harness-artifact.json` and `scripts/validate_harness_artifact.py`). Wheels are not byte-reproducible (the build embeds file times), so always pin the checksum of the published asset, never a local rebuild.

Canonical import: `from product_platform_harness import ProductEvents`. `harness-v0.2.0` has no wheel; do not use it for Python.
