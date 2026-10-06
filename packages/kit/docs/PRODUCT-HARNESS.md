# Product Harness contract

This contract was extracted only after equivalent provider-neutral event envelopes were implemented in two different products: `vehicle-tracking` (TypeScript/Next.js) and `ai-docs` (Python/FastAPI).

## Reuse boundary

`ai-kit` owns the cross-product schema and policy. It does **not** own a network service, analytics gateway or shared language runtime.

Each product implements a small idiomatic adapter for its stack and may connect that adapter to PostHog, another analytics provider, or structured logs.

## Required behavior

- product requests must not fail because analytics/CRM delivery failed;
- entitlement decisions are server-side;
- CRM writes are downstream of business/product events;
- generic product events must not contain raw documents, OCR text, GPS coordinates, IMEI, credentials, access tokens or unnecessary PII;
- `release_sha` and `product_id` are required for production correlation;
- vendor-specific fields must not leak into domain APIs.

## Current evidence

- `vehicle-tracking`: provider-neutral sink plus server-side entitlement decision and `limit_reached` path.
- `ai-docs`: provider-neutral sink plus accepted async-processing `feature_used` signal with document payload excluded.

This evidence supports schema/policy reuse, not a new control plane.
