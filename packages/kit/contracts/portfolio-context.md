# Portfolio context protocol

Every new-product proposal and implementation must resolve capabilities before code generation.

Current evolution scope is `contracts/portfolio-products.json`: four platform
repositories and eight product candidates. Historical products are not new
adoption targets. `implementation_status`, `implemented` and `planned` in the
registry distinguish existing behavior from roadmap capabilities. An allowed
dependency does not require a product to install every runtime module.

## Resolution

For each requested capability:
1. REUSE an existing canonical capability when it satisfies the requirement.
2. EXTEND its canonical owner when a generic gap exists.
3. CREATE only when no compatible capability/owner exists.

A product-to-product source dependency is forbidden. Reusable behavior discovered inside a product must be promoted to its platform owner first.

## Context packet

The proposal handoff must carry:
- product intent and bounded requirements;
- capability-registry version/hash;
- requested capabilities;
- resolution for each: REUSE/EXTEND/CREATE;
- canonical owner and version when reused;
- gaps requiring owner changes;
- product-only domain capabilities;
- migration/deployment implications;
- unresolved decisions.

product-platform-cli reasons over the packet. product-platform-engineering-team treats it as planning input and revalidates mutable repository state before writes.

## Anti-duplication gate

Implementation must stop when a proposed new module overlaps a registry capability without an explicit EXTEND decision against the canonical owner.
