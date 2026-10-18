# Adversarial container boundary canaries — ai-team

This validation uses **real Docker containers**, but synthetic files and no provider authentication. It is executed from `local_stage_isolation_smoke.py` in the existing `engineering-team` CI runtime-smoke job, without changing protected GitHub workflows.

## Boundaries tested

- Inject synthetic `GH_TOKEN`, `GITHUB_TOKEN`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY` in the host process, confirm that the spawned container receives none of them.
- Confirm non-root UID 1001, missing Docker socket, empty agent account home, and denied outbound TCP in a `--network none` container.
- Verify that planning receives a read-only workspace, while implementation can write only the permitted source file.
- Attempt writes through symlinks targeting the read-only Git metadata and handoff mounts, and an out-of-workspace symlink read.
- Confirm that protected Git metadata, handoff, and synthetic out-of-workspace files remain unchanged on the host.

A test passes **only when every attempted prohibited operation is denied** and host markers stay unchanged.

## What this does not certify

This is not a test of real Claude/Codex tool behavior, prompt-injection resistance of authenticated models, live subscription access, Docker daemon compromise, or POSIX ACL enforcement on the operator's own Linux filesystem. Both agent containers have network access for provider calls in the real workflow; the canaries intentionally disable network to test that boundary. Real-provider tests and an ACL-specific pilot on the operator host remain acceptance work.

Run on Linux from `packages/engineering-team` after building the local provider-runtime image:

```bash
AI_TEAM_SMOKE_IMAGE=ai-eng-provider-cli:validation \
  python3 scripts/local_adversarial_isolation_smoke.py
```

The program never sends tokens to a provider, publishes results, merges PRs, or deploys. Its sentinel is synthetic and must never be replaced with a real credential.
