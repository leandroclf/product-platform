# Ideal Product Harness Architecture

Status: proposed canonical product-delivery contract.

This is **not** a new control plane. It is a small set of contracts that products can adopt independently while `ai-engineering-team` remains the engineering runtime and `ai-kit` remains the reusable policy/skills source.

## Executive gap analysis

| Pillar | Current evidence | Gap | Target |
|---|---|---|---|
| Developers | CI exists in core repos; OmniCLI has CI/release; FiveM has CI; Yukz Flow has broad CI/CD; vehicle-tracking has validate scripts and tracker-server CI | inconsistent gates, deploys and runtime telemetry; some pipelines contain placeholder deploy steps | reusable CI contract + preview/staging + OpenTelemetry/error tracking |
| Entrepreneurs | vehicle-tracking has domain analytics; site-yukz-v2 has GA4 events; Bússola has insight feedback data | no cross-product event taxonomy, activation/funnel/retention contract or feature-value dashboard | canonical product-event schema + product analytics |
| Sellers | site-yukz-v2 already has HubSpot lead capture | CRM is website-specific; product usage is not connected to account/plan/lead signals | account-level usage signals -> backend sales trigger -> CRM |
| Users | product-specific UI/feedback exists in places | no common in-product feedback contract, session diagnostics or safe rollout/kill switch | feedback events + session/error context + feature flags |

## Harness contracts

### 1. Product identity

Every product event and commercial trigger uses:

- `product_id`
- `environment`
- `user_id` when authenticated
- `account_id` for B2B/multi-tenant products
- `plan_id`
- `session_id` where relevant
- `release_sha`

Do not put email, CPF/CNPJ, raw document contents, GPS coordinates or other unnecessary personal/sensitive payloads in analytics events.

### 2. Product event envelope

Canonical event:

```json
{
  "event": "feature_used",
  "product_id": "vehicle-tracking",
  "user_id": "opaque-id",
  "account_id": "opaque-account-id",
  "plan_id": "free",
  "feature": "geofence",
  "outcome": "success",
  "release_sha": "git-sha",
  "occurred_at": "RFC3339"
}
```

Minimum business events:

- `signup_completed`
- `activation_completed`
- `feature_used`
- `limit_reached`
- `upgrade_intent`
- `subscription_changed`
- `feedback_submitted`

Domain events remain product-owned.

### 3. Entitlement boundary

Paywall decisions belong to the backend/domain boundary, never only to the UI.

A product implements:

`checkEntitlement(account, capability) -> { allowed, plan, limit, usage, reason }`

When a meaningful limit is reached:

1. backend denies or degrades according to product policy;
2. emit `limit_reached` once per bounded window/idempotency key;
3. frontend receives structured upgrade metadata;
4. sales integration consumes the business event asynchronously.

CRM failure must never fail the product request.

### 4. Sales signal adapter

Products emit internal business events; they do **not** call a CRM from arbitrary domain code.

Initial adapter target: HubSpot because `site-yukz-v2` already contains a working integration pattern.

Examples:

- activated account with high-value feature usage;
- free account reaches 80% usage;
- hard limit reached;
- repeated upgrade intent;
- trial nearing expiry with recent activity.

The adapter owns deduplication, retry, rate limiting and CRM field mapping.

### 5. Observability

Server runtimes should expose OpenTelemetry-compatible traces/metrics and structured logs. Browser telemetry should remain deliberately smaller: errors, Web Vitals and product/session correlation, avoiding duplicate SDKs.

Required correlation fields:

- `trace_id`
- `product_id`
- `release_sha`
- opaque `account_id` when appropriate
- domain operation name

### 6. Feedback and safe delivery

Use the same product-event identity for:

- in-product feedback;
- surveys;
- feature flags/experiments;
- session replay/error correlation.

A feature flag is a delivery control, not an authorization mechanism. Entitlements remain server-side.

## Repository injection map

### vehicle-tracking — first reference implementation

- global frontend provider/layout: initialize product analytics and error/session correlation;
- authentication/session boundary: identify/reset opaque user/account identity;
- API/domain middleware: attach `product_id/account_id/release_sha/trace_id`;
- usage-sensitive API routes: call entitlement service before expensive/premium operations;
- existing analytics service: keep fleet/domain analytics separate; add product-event adapter beside it;
- upgrade UI: react to structured `limit_reached` response;
- tracker-server: OpenTelemetry/server error instrumentation; never send raw GPS coordinates to product analytics.

### site-yukz-v2

- preserve existing GA4 + HubSpot lead capture;
- normalize its event names into the canonical event vocabulary;
- route CRM writes through one server-side adapter;
- remove unsupported marketing KPI claims from code/docs unless backed by measured data.

### bussola-financeira

- FastAPI middleware: trace/release/product correlation;
- service layer: emit activation/feature events after successful deterministic operations;
- existing insight feedback table: map explicit feedback to `feedback_submitted`;
- never send portfolio positions or financial identifiers as generic analytics properties.

### professional-english-coach

- application bootstrap: product analytics;
- learning engine: activation, lesson completion and reusable-feature events;
- AI feedback boundary: error/latency telemetry without storing raw learner text in generic analytics by default.

### ai-docs

- FastAPI middleware and async processing boundary: tracing + release/task correlation;
- callback pipeline: operational telemetry, not product analytics payloads;
- emit product events from API/service outcomes, never raw OCR/document content.

### fivem-server-monitor-pro

- backend/dashboard boundary: activation and monitored-server feature usage;
- preserve privacy contract: no player identifiers in generic analytics;
- CI/release evidence remains the primary developer harness.

### yukz-flow

- existing CI/CD is a useful reference, but placeholder deploy commands are not considered continuous deployment;
- runtime/studio should share event identity and trace correlation;
- workflow execution metrics remain operational telemetry, while workflow creation/activation are product events.

## Adoption sequence

### Phase 0 — contract only
No shared service. Keep this document and a JSON Schema/test fixture for event compatibility.

### Phase 1 — reference implementation
Implement identity + product events + entitlement/limit event in `vehicle-tracking`.

### Phase 2 — management visibility
Build activation/funnel/retention dashboards from canonical events. Product decisions must cite observed events rather than repository activity.

### Phase 3 — PLG/sales
Connect `limit_reached` and high-intent events to the existing HubSpot pattern through an async adapter.

### Phase 4 — reliability
Standardize server OpenTelemetry and error correlation. Add preview/staging/smoke/rollback only where deployment infrastructure is real.

### Phase 5 — reuse
Only after at least two products implement the same contract, extract a small library into `ai-kit` or a dedicated package. Do not create a service prematurely.

## Quick wins

1. Add canonical product-event JSON Schema + CI validation and implement 5–7 events in `vehicle-tracking`.
2. Add server-side `limit_reached` business event and async HubSpot adapter; use the existing site integration as the first CRM target.
3. Add release SHA + account/product correlation to server logs/traces and error reporting in `vehicle-tracking` and `ai-docs`.

## Success metrics

Developer: deployment lead time, change failure rate, MTTR, CI pass rate.

Product: activation rate, weekly activated accounts, feature adoption, retention by activated capability.

Sales: product-qualified leads, limit-to-upgrade conversion, time from signal to CRM task/contact update.

User: error-free sessions, p95 key-flow latency, feedback rate, rollback/kill-switch time.
