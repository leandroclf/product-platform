# Design

The CLI flag raises only the task's plan-risk ceiling from R1 to R2. The host stores the method, repository, base SHA and SHA-256 of the exact request in private task state. Before planning and each actual-change check, the coordinator verifies the stored authorization against that task identity.

`authorize_plan` rejects R3 and unknown risk values unconditionally. The existing path classifier remains independent: changed sensitive paths still require their named offline quality checks. Review handoffs omit only the host-generated `openspec/changes/ai-team-<task>/<cycle>/` files; product-owned OpenSpec changes remain visible. `deliver` continues to reject R2 and R3 plans, so authorization permits isolated execution and review only.
