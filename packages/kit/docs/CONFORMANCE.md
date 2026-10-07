# Consumer conformance

Consumers pin a product-platform-kit release/commit and run the canonical conformance runner or validate their emitted fixture against `contracts/product-event/v1.schema.json`.

The conformance kit owns event vocabulary, required metadata and forbidden additional fields. Product repositories own only their event emission points, sinks and domain-specific policy.

Do not fork the schema into a new product-owned contract. Compatibility copies must declare the pinned product-platform-kit contract version and are transitional.
