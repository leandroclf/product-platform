# Payment hardening increment

Stripe delivery authentication now rejects timestamps outside a five-minute
window in either direction, malformed signatures and ambiguous timestamps. It
accepts multiple v1 signatures during rotation and validates the raw body again
before normalization. Synchronize the host clock. Event creation time is not
delivery time: an old event re-signed by Stripe for a retry remains valid.

This is not durable replay protection: consumers must persist and atomically
claim provider/account/environment/event identity before applying effects.
Inbox, ledger, reconciliation and transactional entitlement effects remain
tracked in platform issue #102; do not enable production based on this fix.

Customer creation defaults to a hash of tenant/user identity for retry safety.
Consumers must scope tenant identity by product and persist the resulting
Stripe customer ID. Stripe's retention of idempotency keys is finite: this
header is not a replacement for a unique local customer mapping.

Subscription creation now fails before any request unless the consumer passes
`idempotencyKey` from a persisted purchase intent. Reuse the same key and payload
after a timeout; use a new intent for a new subscription, including resubscribe.
This intentionally closes an unsafe legacy path. Existing consumers must be
migrated before adopting the next release. Mercado Pago behavior is unchanged.

Gateway HTTP requests have a 15-second timeout, preserving caller cancellation.
There is no automatic write retry: an aborted request may have reached the
provider. Reconcile or retry the same intent/key, never create a new purchase.

Tests use synthetic payloads and intercepted HTTP only. They do not prove a
sandbox/live integration. Publish a new immutable release after review and
version updates; never replace the existing harness-v0.2.1 assets.
