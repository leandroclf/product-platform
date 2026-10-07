# Testing Skill

## Verification ladder
Use the cheapest reliable feedback first:
1. Static analysis / formatting for changed files.
2. Type checking or compilation.
3. Focused unit tests.
4. Integration/contract tests for affected boundaries.
5. Browser/E2E tests when user-visible flows are affected.
6. Broader regression suite when practical.

## Rules
- Discover commands from project files; never invent them.
- Test behavior, not implementation details, where practical.
- Add or update regression tests for defects.
- Do not delete or relax a valid test simply because a change breaks it.
- Distinguish failures introduced by the change from pre-existing failures.
- If a check cannot be run, say exactly what remains unverified and why.

## Browser verification
Activate Playwright for real browser flows, accessibility smoke checks, navigation, forms and critical UI regressions. Prefer deterministic selectors and avoid brittle sleeps.
