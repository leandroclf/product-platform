# PostgreSQL payment inbox (candidate)

This increment extends the existing harness. It creates no shared service,
central database, mandatory queue or runtime database dependency. A product
supplies its existing PostgreSQL pool, an authenticated account/tenant mapping,
its domain handler and its worker lifecycle.

Durable ingestion is initially enabled only for Stripe. The existing Mercado
Pago adapter remains unchanged: it resolves current resource state during
normalization rather than an immutable event snapshot, and its signed resource
identity must be bound to routing before adopting these stronger guarantees.
This inbox fails closed for that provider until its adapter/acceptance are
extended; it does not silently treat it as equivalent to Stripe.

## Explicit adoption

1. Review and integrate the R2 change and publish a **new** immutable release.
   Do not replace harness-v0.2.1 assets or migrate all consumers automatically.
2. Apply `migrations/001_payment_inbox.sql` once through the product migration
   system as an EXPAND change. Importing or constructing the class never runs DDL.
   Preserve the two tables during rollback. CONTRACT/removal is a separate release.
3. Wrap the product's pool in `PaymentSqlPool`; every `connect()` must lease one
   exclusive session until `release()`. Never multiplex an active transaction.
   Configure statement/idle-in-transaction timeouts at the product/database layer.
4. Resolve product, provider account, environment and tenant from authenticated
   configuration/local customer mappings. Do not trust routing metadata alone.
   Ensure the gateway signing secret belongs to that account/environment.
5. Call `ingest()` with the existing gateway adapter and the exact raw body.
   Acknowledge a delivery only after `accepted`/`duplicate` returns. Authentication,
   identity collision and DB errors are not successful acceptance.
6. A product-owned worker calls `processNext()` with a bounded retry policy.
   Its callback uses the same SQL session for ledger/entitlement/domain writes;
   failures roll everything back. It must not commit, release the session or make
   external calls. External delivery needs a transactionally written outbox.

## Guarantees and boundaries

The database primary key scopes event identity by product, provider, provider
account and environment. A tenant/payload conflict is rejected instead of routing
the same provider event to a new tenant. Only allowlisted normalized scalar fields
are stored; no raw webhook, headers, arbitrary metadata or error messages persist.

`FOR UPDATE SKIP LOCKED` claims an eligible event in the processing transaction.
A PostgreSQL advisory transaction lock serializes different events for the same
resource. Database session loss releases locks and rolls back unfinished writes.
There is no external lease to expire and accidentally allow two concurrent owners.

Serialization is **not chronological ordering or reconciliation**. A consumer must
apply authoritative state/version checks before changing an existing resource;
older deliveries must not revoke or restore access by event timestamp alone.
The module does not yet implement reconciliation, checkout or a financial ledger.
Processing may be attempted repeatedly. Only DB effects participating in this
transaction are atomic with the processed marker; there is no exactly-once claim
for HTTP, email, provider calls or any external side effect.

A successful COMMIT with lost acknowledgement is ambiguous. The worker never
resets a processed event and surfaces `requires reconciliation` if its guarded
failure update finds no pending record. Re-check state before retrying any effect.

Failures are delayed and bounded before dead-lettering. Attempts are cumulative.
An authorized explicit `replay()` reopens only a dead-letter event and records
actor/reason/request identity atomically; it never erases history. A replay grants
one further attempt if the cumulative retry budget was already exhausted. Retrying
the same replay request is idempotent; reusing its identity with different data is
rejected. Product-side authorization/audit access remains mandatory.

`stats(scope)` provides pending/processed/dead-letter counts and oldest pending
age without tenant IDs, event IDs or payload. Export through existing telemetry
only under the product's configuration; nothing is sent externally by default.
Alert on pending age, dead letters and processing/reconciliation errors.

## Validation

`npm run validate` builds TypeScript, runs existing TS/Python tests and then runs
`tests/postgres-inbox.test.mjs`. PGlite 0.5.11 is an exactly pinned **development**
dependency: it executes PostgreSQL SQL and checks file-backed reopen persistence,
rollback, collisions, retry budgets, audited replay and lost commit acknowledgement.
It is not imported by runtime code or bundled as a production dependency.

The embedded test adapter serializes session leases because PGlite uses one
backend. Its Promise.all tests prove duplicate handling under that adapter, not
contention/fairness or failure behavior across independent PostgreSQL processes.
Before production, test with the product's real driver/server: two worker sessions,
SKIP LOCKED contention, transaction termination, connection loss, migration rights,
permissions/tenant isolation, recovery and resource ordering/reconciliation.

No Stripe sandbox/live request or production migration was executed. The registry
remains partial until consumer adoption and acceptance establish the broader
financial lifecycle. Python financial parity, durable ledger, domain adapters,
checkout/billing and real reconciliation remain tracked in #102–#105.

References:
- https://www.postgresql.org/docs/current/sql-select.html
- https://www.postgresql.org/docs/current/sql-insert.html
- https://pglite.dev/docs/
