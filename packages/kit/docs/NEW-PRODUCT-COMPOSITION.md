# New product composition protocol

A new product starts from capabilities, not copied repositories.

## 1. Conceive

Provide the idea plus `contracts/capability-registry.yaml` to OmniCLI.

```bash
omnicli conceive "<idea>" --refine --loops 3 \
  --portfolio-context /path/to/ai-kit/contracts/capability-registry.yaml
```

The proposal must produce a REUSE / EXTEND / CREATE resolution.

## 2. Handoff

Persist the registry SHA-256 and capability decisions in the AI Team handoff. If the registry changes before implementation, re-resolve affected decisions.

## 3. Execute

For EXTEND:
- change the canonical owner first;
- validate and release an immutable version;
- update the product consumer;
- remove any superseded local implementation only after consumer validation.

For REUSE:
- pin an immutable version and add only product-specific configuration/adapters.

For CREATE:
- create only product-domain behavior and assign ownership.

## 4. Shared platform

Expected reusable composition:

```
new-product
  -> ai-kit contracts/policies
  -> product-harness/core
  -> product-harness/growth (optional)
  -> product-harness/commerce (optional)
  -> product-harness/economics (optional)
  -> product-harness/observability
  -> product-specific domain
```

No product may source-depend on another product.

## 5. Definition of done

A new product is composition-complete when:
- every requested capability has a resolution;
- no duplicate registered capability exists in product source;
- shared dependencies are immutable/pinned;
- contract/conformance tests pass;
- product integration tests pass;
- deployment follows expand -> deploy -> observe -> later contract.
