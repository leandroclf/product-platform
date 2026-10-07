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

The Python package lives in `packages/python` (`product_platform_harness`, events only: no payments or usage persistence). The release workflow does **not** publish a wheel yet. Until it does, validate a local wheel built from the tag and verify its SHA-256 before adoption:

```bash
git clone --branch harness-v0.2.0 https://github.com/leandroclf/product-platform.git
python -m pip wheel --no-deps ./product-platform/packages/harness/packages/python --wheel-dir /tmp/harness-wheels
sha256sum /tmp/harness-wheels/*.whl
```

Canonical import: `from product_platform_harness import ProductEvents`. Adding the wheel to the release assets is an open follow-up.
