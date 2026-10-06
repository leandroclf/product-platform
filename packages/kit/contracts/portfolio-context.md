# Portfolio context protocol

Every new-product proposal and implementation must resolve capabilities before code generation.

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

OmniCLI reasons over the packet. ai-engineering-team treats it as planning input and revalidates mutable repository state before writes.

## Anti-duplication gate

Implementation must stop when a proposed new module overlaps a registry capability without an explicit EXTEND decision against the canonical owner.
