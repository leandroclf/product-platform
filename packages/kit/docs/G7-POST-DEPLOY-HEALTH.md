# G7 — Post-deploy health evidence (read-only)

G6 validates the *local* checkout and release artifact. It does **not** establish that
the artifact was deployed. G7 adds a bounded check against an explicitly configured
HTTPS health URL **after** a product-specific deployment has completed.

## Usage

Run from a trusted product CI runner after a **staging** deployment:

```bash
python3 packages/kit/scripts/verify-post-deploy-health.py \
  --url "https://staging.example.com/health" --attempts 5 --interval 3 --timeout 5 --consecutive-successes 3
```

Exit status 0 indicates that the endpoint returned the configured number of consecutive HTTP 200 responses (default 1 for backward compatibility; recommend 3 for staging);
status 2 means block, including malformed input, redirects, 4xx/5xx, timeouts
and transport failures. Output is machine-readable JSON, no response bodies or
URL (which could contain sensitive query values) are printed. Only HTTPS on the
standard port is supported. Requests do not carry credentials or follow redirects.

Run offline tests:

```bash
python3 packages/kit/scripts/verify-post-deploy-health.test.py
```

## Integration boundary

1. The **product repository** builds and tests from a pinned commit and calls G6
   against the actual packaged bytes in the same trusted CI provenance chain.
2. The product's existing deploy adapter publishes the **same** artifact to staging.
   No credentials, deployment commands, or provider adapter belong in G7.
3. Only after deploy completes, call G7 using a **fixed trusted endpoint from CI
   configuration** (never an endpoint supplied by untrusted PR content).
4. Confirm the deployed revision separately through an authenticated
   provider-native deployment identifier or an independently trusted release
   metadata endpoint. HTTP 200 alone does not prove which revision is running.
5. Promotion to production requires existing GitHub protected environments,
   human approval where mandated, release identity verification, and provider-
   specific rollback. Never infer approval or rollback correctness from G7.

## Security and operational limitations

- The endpoint is not an identity proof. A green response may come from an
  old replica, cached gateway, or unrelated deployment.
- The script deliberately does **not** authorize deploy, orchestrate rollback,
  or modify GitHub workflow permissions.
- Operators must control the destination: do not pass endpoints extracted from
  user input or pull requests. A CI runner with network access could otherwise
  be used to probe unintended services. DNS resolution is not pinned here.
- A single successful check indicates point-in-time reachability, **not**
  sustained availability; production acceptance should also use normal
  monitoring and release-specific smoke tests.
- Implement rollback in the product's established hosting provider, using a
  verified previous revision and a follow-up health/identity check.

## Stable health threshold

Use `--consecutive-successes 3 --attempts 5` for staging. Any timeout, HTTP
error or transport failure resets the streak. A single successful probe is not
evidence of recovery stability. The threshold is bounded by the attempt count
and is still not proof of the deployed release identity or production readiness.
