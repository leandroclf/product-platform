# SDK distribution

The canonical runtime is the `harness` package of the platform repository (`packages/harness`). The kit owns schemas, policy and conformance and does not ship runtime code.

The legacy kit SDKs (`harness-ts` and `harness-python`) were removed during the consolidation into the platform repository; no product depended on them and their history is preserved. `releases/harness-v1.0.0.yaml` remains as historical evidence of that legacy release, not of the canonical runtime.

The harness builds the TypeScript package from `packages/harness` and the Python package from `packages/harness/packages/python`. Releases use tags `harness-v<version>`; the release workflow requires the tag to match the TypeScript and Python versions and the tagged commit to be on `main`, then publishes the tarball with `SHA256SUMS`. Every commit that changes the harness also uploads a commit-addressed tarball as a CI artifact.

Consumers (products, which live in their own repositories) must pin a released artifact by its checksum, or an immutable commit. They must not copy SDK source, depend on the source tree of the platform repository, or follow a floating branch. The first pilot (vehicle-tracking) still pins an earlier artifact and must move to a `harness-v*` release before adopting new runtime changes.

Publishing to a public package registry is intentionally not required for the initial zero-cost workflow; GitHub release/workflow artifacts provide the build evidence while registry publication can be added when distribution outside the repository set is needed.
