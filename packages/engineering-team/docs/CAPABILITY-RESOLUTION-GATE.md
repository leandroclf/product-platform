# Portfolio capability resolution gate

Before PLAN for a new product or cross-cutting capability, resolve requested capabilities against the canonical registry at `product-platform/packages/kit/contracts/capability-registry.yaml`.

`product-platform` is a monorepo: `packages/kit`, `packages/harness`, `packages/cli`, `packages/engineering-team` and `packages/design-system` are packages, not separate Git repositories. The historical repositories `leandroclf/product-platform-kit` and `leandroclf/product-platform-harness` are archived; use the corresponding package paths in this repository as the current source of truth.

Decision order:
1. REUSE canonical capability.
2. EXTEND canonical owner.
3. CREATE only if no compatible capability exists.

The plan must record capability, decision, owner, pinned version/commit when applicable, and product-specific adapter/domain work.

## Stop conditions

Stop before implementation when:
- a proposed module duplicates a registered capability;
- a product attempts to source-depend on another product;
- an EXTEND decision targets the consuming product instead of the canonical owner;
- registry context is stale relative to the handoff and materially changes ownership.

## Cross-repository execution

A bounded change may span this platform repository and one or more product repositories. Changes among platform packages belong to this repository and can share one branch and PR. Treat each product-repository mutation as a separate work item with its own branch, validation and PR. Sequence canonical-owner changes before consumer adoption. Do not copy code temporarily into a consumer as an integration shortcut.

Typical sequence when a product needs a new reusable capability:

`product-platform/packages/kit` contract (if needed) -> `product-platform/packages/harness` capability -> immutable harness release -> product-repository consumer -> remove superseded local copy.

See the delivery flow and G0–G6 gates in `packages/kit/docs/PLATFORM-DELIVERY-FLOW.md`.
