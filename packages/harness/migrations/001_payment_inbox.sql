-- EXPAND only. Apply explicitly with the product's migration system; never at import/startup.
CREATE TABLE product_payment_inbox_v1 (
  product_id text NOT NULL,
  gateway text NOT NULL CHECK (gateway IN ('stripe', 'mercado_pago')),
  provider_account_id text NOT NULL,
  environment text NOT NULL CHECK (environment IN ('sandbox', 'staging', 'production')),
  external_event_id text NOT NULL,
  tenant_id text NOT NULL,
  external_resource_id text NOT NULL,
  payload jsonb NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
  state text NOT NULL DEFAULT 'pending' CHECK (state IN ('pending', 'processed', 'dead_letter')),
  attempts integer NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  received_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  processed_at timestamptz,
  last_error_code text CHECK (last_error_code IS NULL OR last_error_code = 'processor_failed'),
  PRIMARY KEY (product_id, gateway, provider_account_id, environment, external_event_id),
  CHECK ((state = 'processed') = (processed_at IS NOT NULL))
);
CREATE INDEX product_payment_inbox_pending_v1
  ON product_payment_inbox_v1 (product_id, gateway, provider_account_id, environment, available_at, received_at)
  WHERE state = 'pending';

-- Replay never removes historical attempts or its reason/actor.
CREATE TABLE product_payment_inbox_replay_v1 (
  replay_id text PRIMARY KEY,
  product_id text NOT NULL,
  gateway text NOT NULL,
  provider_account_id text NOT NULL,
  environment text NOT NULL,
  external_event_id text NOT NULL,
  actor_id text NOT NULL,
  reason_code text NOT NULL,
  replayed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  FOREIGN KEY (product_id, gateway, provider_account_id, environment, external_event_id)
    REFERENCES product_payment_inbox_v1
);
