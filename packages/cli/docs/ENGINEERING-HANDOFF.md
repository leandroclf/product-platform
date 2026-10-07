# Engineering handoff boundary

OmniCLI owns discovery and proposal quality. It hands implementation to `product-platform-engineering-team` (`ai-team`) through the versioned EngineeringProposalHandoff contract (`contracts/engineering-proposal-handoff.v1.schema.json`).

OmniCLI must not embed planner/implementer/validator/reviewer runtime logic. The receiving engineering runtime may enrich the handoff into its internal TaskEnvelope, but must preserve repository base, scope, risk, acceptance criteria and evidence requirements.

## Platform rules in the handoff

The target product must be delivered under the rules of `product-platform-kit` and `product-platform-harness`. The canonical flow and gates are in `product-platform-kit/docs/PLATFORM-DELIVERY-FLOW.md`. A proposal ready for handoff must carry:

- the capability resolution table (REUSE / EXTEND / CREATE with owner and version) and the `portfolio_fingerprint` from the run manifest (`PortfolioCapabilityHandoff`, schema in `product-platform-engineering-team/contracts/`);
- the kit and harness versions or SHAs whose rules apply, and the kit profile;
- EXTEND items as separate work in the canonical owner repository, sequenced before the consumer.

## Generating the capability handoff

```bash
omnicli conceive "<ideia>" --refine --loops 3 \
  --portfolio-context packages/kit/contracts/capability-registry.yaml \
  --handoff-out capacidades.json
ai-team run --handoff capacidades.json \
  --registry packages/kit/contracts/capability-registry.yaml \
  --rules packages/kit/docs/PLATFORM-DELIVERY-FLOW.md 'Implemente conforme a proposta'
```

- With `--portfolio-context`, every stage prompt asks the final document to end with one ```` ```capability-handoff ```` block (JSON: `product` and `capabilities` with `name`, `decision`, `owner`, optional `version`/`reason`).
- `--handoff-out` extracts the last such block, validates it (decision in REUSE/EXTEND/CREATE, no duplicates, no unknown keys) and writes the `PortfolioCapabilityHandoff` JSON. `registry_fingerprint` is the sha256 of the registry file computed by OmniCLI, never taken from model text, so `ai-team run --registry` can detect a stale registry.
- If the block is missing or invalid, the proposal is kept and the command exits with code 1 without writing the JSON. `--handoff-out` requires `--portfolio-context`.
- Before `ai-team run`, check the JSON against the canonical registry with `python3 packages/kit/scripts/validate-platform-handoff.py capacidades.json` (registry fingerprint, REUSE/EXTEND/CREATE decisions, owners, product-to-product dependencies).
- Human review of the proposal (and of the JSON) stays between the two commands.

## Current status

- Implemented: capability handoff generation (`src/omnicli/handoff.py`) consumed by `ai-team run --handoff`.
- Still not generated: the full `EngineeringProposalHandoff` v1 (repository, scope, acceptance, risk, evidence). Its schema has `additionalProperties: false`, so rules references and capability resolution need v1.1 or an envelope composing both schemas.
- Capability names and owners are checked against the registry by the kit validator, not by OmniCLI itself. The canonical contract is the kit's `PlatformHandoff` envelope; OmniCLI still emits only the capability part of it.
