# Tasks

- [x] Implement fixed stage profiles and explicit CLI model/effort flags.
- [x] Implement planning/implementation/assessment contracts and OpenSpec handoff.
- [x] Enforce stage-specific mounts, sessions, tools and login paths in command construction.
- [x] Implement bounded repair/replanning and evidence checks at delivery.
- [x] Cover new lifecycle, legacy migration and failures in controlled tests.
- [x] Update current local documentation and bootstrap; distinguish historical harness.
- [x] Run required repository checks and review final diff.
- [x] Run real offline Docker stage mount canaries and pinned CLI/install checks in CI (run 37107965577 on implementation commit 6c239b2).

## External acceptance

- [x] On operator Linux, rebuild runtime, authenticate all four stage contexts, verify account model access, and execute a small real target task through all stages. This cannot be certified by mocked providers or offline checks. EVIDENCE 2026-10-04: four logins confirmed by `ai-team doctor`; task bbdf40eb (UX refinement of an Astro site, 14 files) reached REVIEWED in one cycle (plan 4m20s, implement 12m48s, offline checks incl. Pages build, Sentinel PASS_WITH_FINDINGS, Atlas/Claude review PASS_WITH_FINDINGS), the diff was inspected (src/ and openspec/ only, no dependency or config changes) and delivered as a draft PR (leandroclf/pshhospitalar#1); merge left to the operator. Real-run defects found and fixed: plan schema `uniqueItems` rejected by the API, Claude stream result discarded (`null`), 30-turn and 1 MB limits, and one Claude subscription session limit (surfaced, not bypassed). Both host-specific relaxations are now explicit per-project opt-ins with secure defaults, recorded in the frozen task config: `init --test-exec` (checks tmpfs with `exec`, needed for node_modules/.bin because Docker mounts tmpfs noexec) and `init --codex-sandbox danger-full-access` (Codex bwrap cannot create namespaces in the container); the container hardening stays the boundary in both cases. Visual browser verification of the delivered change remains a manual operator check.
