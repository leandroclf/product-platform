# Portfolio-aware product conception

OmniCLI remains the proposal stage. It does not become a portfolio control plane.

Before proposing implementation for a new product, a portfolio context packet SHOULD be supplied from the canonical product-platform-kit capability registry.

Every architecture/master-proposal stage must classify requested capabilities:

- REUSE: consume the canonical owner/version.
- EXTEND: change the canonical owner once, then consume it.
- CREATE: new product-domain capability with explicit owner.

The proposal must not recommend copying reusable code from another product repository. If useful reusable behavior currently exists only inside a product, the proposal must identify extraction/promotion to its canonical platform owner.

The resulting handoff to product-platform-engineering-team includes the capability resolution table and registry fingerprint so the execution stage can detect stale context.
