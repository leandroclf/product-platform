# Engineering handoff boundary

OmniCLI owns discovery and proposal quality. It hands implementation to ai-engineering-team through the versioned EngineeringProposalHandoff contract.

OmniCLI must not embed planner/implementer/validator/reviewer runtime logic. The receiving engineering runtime may enrich the handoff into its internal TaskEnvelope, but must preserve repository base, scope, risk, acceptance criteria and evidence requirements.
