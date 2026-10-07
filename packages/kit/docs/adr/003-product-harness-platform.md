# ADR 003: Product Harness reusable platform

## Decision

Reusable product infrastructure is owned by a single repository named `product-platform-harness`.

product-platform-kit remains the shared contract/policy/skill kernel. Product repositories own domain logic only.

## Logical modules

- core: product identity, tenant/account context, plans, entitlements, usage/metering
- growth: analytics, sales signals, CRM adapters and durable outbox delivery
- commerce: subscriptions, payment gateway contract/adapters, webhook inbox/idempotency and financial ledger
- economics: FinOps projections and unit economics derived from authoritative usage/payment data
- observability: OpenTelemetry instrumentation and safe attributes

Logical modules do not imply independent services. The default physical topology is one product runtime, one optional shared worker process and one PostgreSQL database/pool per product deployment.

## Dependency direction

product -> product-platform-harness -> product-platform-kit contracts

product-platform-kit must not depend on product-platform-harness. product-platform-harness must not depend on any product.

## Data

Products keep their own database ownership. Harness migrations are versioned artifacts applied by the product deployment. No central Harness database is required. No cross-product operational database is introduced.

## Async processing

PostgreSQL transactional outbox/inbox is the default. Kafka/SQS/RabbitMQ are not baseline dependencies.

## Extraction

vehicle-tracking is the reference implementation source. Generic code moves to product-platform-harness only after product-specific assumptions are removed and tests cover the generic behavior. The product then consumes an immutable Harness release before its local copy is deleted.

## Deployment

Harness is released as packages, not deployed as a mandatory central service. Products pin immutable versions. Database evolution uses expand/deploy/contract migrations.
