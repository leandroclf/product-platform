# SDK distribution

Canonical runtime evolution belongs to `product-platform-harness`. This repository
owns schemas, policy and conformance. Existing `packages/harness-ts` and
`packages/harness-python` are legacy compatibility snapshots: retain existing
consumers until a validated immutable replacement is available; do not add new
runtime features here. Historical release manifests remain historical evidence.

The harness builds the TypeScript package from its root and the Python package
from `packages/python`. The first vehicle-tracking pilot pins an existing full
harness SHA; new local runtime changes need a subsequent immutable release.

Legacy release tags matching `harness-v*` build the previous compatibility packages
in the existing workflows. These are not releases of the new canonical runtime.

Consumers must pin a released artifact/version or immutable commit. They must not copy SDK source or depend on a floating branch.

Publishing to a public package registry is intentionally not required for the initial zero-cost workflow; GitHub release/workflow artifacts provide the build evidence while registry publication can be added when distribution outside the repository set is needed.
