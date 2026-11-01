# Deterministic model routing for low-risk documentation

## Objective

Reduce token and model cost for clearly small documentation requests while preserving configured profiles for ambiguous, code, production, security, and higher-risk work.

## Original request

Make the AI team choose models in proportion to task complexity and reduce unnecessary use of the most expensive models.

## Out of scope

- Learned or external model router, extra classifier inference, gateway, or service.
- Automatic provider/model fallback after an inference failure.
- Changing existing project configurations without an explicit upgrade.
- Reducing review independence or bypassing acceptance and risk gates.

## Acceptance

- New configurations enable a deterministic economy profile only for short, explicit documentation requests.
- The profile is checked against all four CLI catalogs before provider inference.
- The accepted plan must confirm R0/R1 and remain within two tasks and three criteria before downstream stages use the economy profile.
- Higher-risk, ambiguous, unavailable, or explicitly customized configurations keep their configured models.
- The route decision, reason, and exact model/effort selection are recorded in task state and visible in status.
