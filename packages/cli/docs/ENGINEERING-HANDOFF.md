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
  --envelope-out handoff.json \
  --repository-url https://github.com/leandroclf/<produto>.git --base-sha <sha da base> \
  --kit-ref <sha do kit> --harness-ref <sha do harness> --profile backend
ai-team run --handoff handoff.json \
  --registry packages/kit/contracts/capability-registry.yaml \
  --rules packages/kit/docs/PLATFORM-DELIVERY-FLOW.md 'Implemente conforme a proposta'
```

`--envelope-out` grava o envelope `PlatformHandoff` v1 completo (proposta, capacidades e referências de regras); `--handoff-out capacidades.json` continua disponível para só o JSON de capacidades. Os dois podem ser usados juntos.

- With `--portfolio-context`, every stage prompt asks the final document to end with two blocks, in this order: ```` ```capability-handoff ```` (JSON: `product` and `capabilities` with `name`, `decision`, `owner`, optional `version`/`reason`) and ```` ```engineering-handoff ```` (JSON: `objective`, `scope.allowed_paths`, `acceptance.criteria`, `risk.level`, `evidence.required`).
- `--handoff-out` extracts the last such block, validates it (decision in REUSE/EXTEND/CREATE, no duplicates, no unknown keys) and writes the `PortfolioCapabilityHandoff` JSON. `registry_fingerprint` is the sha256 of the registry file computed by OmniCLI, never taken from model text, so `ai-team run --registry` can detect a stale registry.
- `--envelope-out` also needs `--repository-url`, `--kit-ref`, `--harness-ref` and `--profile` (optionally `--base-ref`, default `main`, and `--base-sha`). These, the registry fingerprint and the `proposal_id` (the OmniCLI run id) come from the operator and the CLI, never from model text; refs must be full 40-character SHAs and are checked before any provider runs. If a block is missing or invalid, the proposal is kept and the command exits with code 1 without writing the JSON. Both options require `--portfolio-context`.
- Before `ai-team run`, check the JSON against the canonical registry with `python3 packages/kit/scripts/validate-platform-handoff.py handoff.json` (registry fingerprint, REUSE/EXTEND/CREATE decisions, owners, product-to-product dependencies).
- Human review of the proposal (and of the JSON) stays between the two commands.

## Current status

- Implemented: capability handoff and the full `PlatformHandoff` envelope (`src/omnicli/handoff.py`), consumed by `ai-team run --handoff`. A cross-package contract test (`scripts/test_handoff_contract.py` at the repository root) proves that the envelope passes the kit validator with the real registry and is accepted by `ai-team`.
- Capability names, owners and product-to-product dependencies are checked against the registry by the kit validator, not by OmniCLI itself.
- The model proposes objective, scope, criteria, risk and evidence; a human reviews them before `ai-team run`. The `risk.level` of the proposal (low to critical) is advisory: the plan risk (R0 to R3) is decided by the `ai-team` planner.
