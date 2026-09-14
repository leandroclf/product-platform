# Security Skill

## Activate when
Authentication, authorization, secrets, sensitive data, dependency exposure, public endpoints, file handling, parsers or release security are in scope.

## Review areas
- Trust boundaries and attacker-controlled inputs.
- Authentication versus authorization at every protected operation.
- Injection, SSRF, path traversal, unsafe deserialization and command execution risks.
- Secret exposure in code, logs, errors, build output and configuration.
- Data minimization and sensitive-data handling.
- Dependency and supply-chain risk.
- Abuse controls such as rate limiting/idempotency where relevant.
- Secure failure behavior and auditability.

## Rules
Security tools complement code review; they do not replace it. Validate findings before changing code and prioritize exploitable, evidence-backed issues. Never weaken a security control solely to make automation pass.

## Strix
Use the team's validated Strix integration for deeper security analysis when available. Pin the exact tool/package and permissions before automating installation.
