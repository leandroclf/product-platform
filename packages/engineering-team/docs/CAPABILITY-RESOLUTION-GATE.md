# Portfolio capability resolution gate

Before PLAN for a new product or cross-cutting capability, resolve requested capabilities against the canonical product-platform-kit capability registry.

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

A bounded change may require multiple repositories. Treat each repository mutation as an isolated work item with its own branch/validation/PR. Sequence canonical-owner changes before consumer adoption. Do not copy code temporarily into the consumer as an integration shortcut.

Typical sequence:

product-platform-kit contract (if needed) -> product-platform-harness capability -> immutable release -> product consumer -> remove superseded local copy.

Ver também a esteira completa e os gates G0-G6 em `product-platform-kit/docs/PLATFORM-DELIVERY-FLOW.md`.
