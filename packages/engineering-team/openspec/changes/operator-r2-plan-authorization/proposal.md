# Operator-authorized R2 plans

## Why

The local coordinator currently blocks every R2 plan before implementation, although repository governance permits an explicit operator waiver. This prevents read-only audits from reaching validation even when the operator authorizes their exact request.

## What changes

- Add an explicit `ai-team run --authorize-r2` option; default runs remain capped at R1.
- Bind the authorization record to repository, base SHA and request hash.
- Keep R3 blocked, independently classify actual changed paths, require specialized quality checks for sensitive paths, and keep R2 delivery blocked.

## Non-goals

- Authorize R3, credentials, production, destructive or external actions.
- Lower actual path risk or infer authorization from a task request, model output or CI result.
- Add automatic delivery or merge behavior.

## Acceptance

- An R2 plan is stopped before implementation by default and can proceed only when the exact task was started with `--authorize-r2`.
- A tampered or mismatched authorization record is rejected.
- R3 remains blocked under every authorization setting.
- Actual R2 change paths continue to require configured specialized quality checks; R2 tasks cannot be delivered.
