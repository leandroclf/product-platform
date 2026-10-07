# SDK distribution

Harness SDK source is versioned in ai-kit. Release tags matching `harness-v*` build immutable npm and Python package artifacts in GitHub Actions.

Consumers must pin a released artifact/version or immutable commit. They must not copy SDK source or depend on a floating branch.

Publishing to a public package registry is intentionally not required for the initial zero-cost workflow; GitHub release/workflow artifacts provide the build evidence while registry publication can be added when distribution outside the repository set is needed.
