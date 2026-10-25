import { createHash } from 'node:crypto';
import type { IPaymentGateway, WebhookInput } from './gateway.js';
import type { NormalizedPaymentEvent, PaymentGatewayName } from './types.js';

/** Structural adapter: the product supplies its existing PostgreSQL pool. */
export interface PaymentSqlTransaction {
  query<T extends Record<string, unknown> = Record<string, unknown>>(sql: string, values?: unknown[]): Promise<{ rows: T[] }>;
}
export interface PaymentSqlClient extends PaymentSqlTransaction {
  release(): void;
}
export interface PaymentSqlPool { connect(): Promise<PaymentSqlClient>; }
export interface PaymentInboxScope {
  productId: string;
  providerAccountId: string;
  gateway: PaymentGatewayName;
  environment: 'sandbox' | 'staging' | 'production';
}
export interface PaymentInboxPolicy { maxAttempts?: number; retryDelaySeconds?: number; }
type InboxRow = Record<string, unknown> & { external_event_id: string; tenant_id: string; external_resource_id: string; payload: NormalizedPaymentEvent; attempts: number };
const predicate = 'product_id=$1 AND gateway=$2 AND provider_account_id=$3 AND environment=$4';

function identifier(value: string): string {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,254}$/.test(value)) throw new Error('invalid payment inbox identifier');
  return value;
}
function parameters(scope: PaymentInboxScope): unknown[] {
  if (!['stripe', 'mercado_pago'].includes(scope.gateway) || !['sandbox', 'staging', 'production'].includes(scope.environment)) throw new Error('invalid payment inbox scope');
  return [identifier(scope.productId), scope.gateway, identifier(scope.providerAccountId), scope.environment];
}
function normalized(event: NormalizedPaymentEvent, tenantId: string): NormalizedPaymentEvent {
  if (event.tenantId !== undefined && event.tenantId !== tenantId) throw new Error('payment event tenant does not match trusted mapping');
  if (!['payment', 'subscription'].includes(event.type) || !['pending', 'authorized', 'paid', 'failed', 'refunded', 'canceled', 'active', 'past_due', 'paused', 'unknown'].includes(event.status)) throw new Error('invalid normalized payment event');
  if (!Number.isFinite(Date.parse(event.occurredAt))) throw new Error('invalid payment event time');
  if (event.amountMinor !== undefined && (!Number.isSafeInteger(event.amountMinor) || event.amountMinor < 0)) throw new Error('invalid payment minor units');
  if (event.currency !== undefined && !['BRL', 'USD', 'EUR'].includes(event.currency)) throw new Error('invalid payment currency');
  if (event.amountMinor !== undefined && !event.currency) throw new Error('payment amount requires currency');
  // Deliberate allowlist: never persist raw webhook payloads, arbitrary metadata or headers.
  return {
    idempotencyKey: identifier(event.idempotencyKey), gateway: event.gateway,
    externalEventId: identifier(event.externalEventId), externalResourceId: identifier(event.externalResourceId),
    type: event.type, action: identifier(event.action), status: event.status,
    ...(event.amountMinor === undefined ? {} : { amountMinor: event.amountMinor }),
    ...(event.currency === undefined ? {} : { currency: event.currency }),
    tenantId, occurredAt: new Date(event.occurredAt).toISOString(),
    ...(event.rawType === undefined ? {} : { rawType: identifier(event.rawType) }),
  };
}

export class PostgresPaymentInbox {
  private readonly maxAttempts: number;
  private readonly retryDelaySeconds: number;
  constructor(private readonly pool: PaymentSqlPool, policy: PaymentInboxPolicy = {}) {
    this.maxAttempts = policy.maxAttempts ?? 3;
    this.retryDelaySeconds = policy.retryDelaySeconds ?? 30;
    if (!Number.isInteger(this.maxAttempts) || this.maxAttempts < 1 || this.maxAttempts > 100 || !Number.isInteger(this.retryDelaySeconds) || this.retryDelaySeconds < 0 || this.retryDelaySeconds > 86400) throw new Error('invalid payment inbox retry policy');
  }

  /** Resolve scope/tenant from a trusted local mapping, not unverified webhook metadata. */
  async ingest(scope: PaymentInboxScope, tenantId: string, gateway: IPaymentGateway, input: WebhookInput): Promise<'accepted' | 'duplicate'> {
    const scopeParams = parameters(scope); identifier(tenantId);
    // The existing Mercado Pago adapter resolves mutable remote resource state;
    // it does not yet provide the immutable authenticated event snapshot required
    // by this inbox. Preserve it, but do not opt it into a stronger guarantee.
    if (scope.gateway !== 'stripe') throw new Error('gateway not yet supported by durable payment ingestion');
    if (gateway.name !== scope.gateway || !await gateway.verifyWebhook(input)) throw new Error('unauthenticated payment event');
    const event = normalized(await gateway.normalizeWebhook(input), tenantId);
    if (event.gateway !== scope.gateway) throw new Error('payment provider mismatch');
    const payload = JSON.stringify(event), hash = createHash('sha256').update(payload).digest('hex');
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const inserted = await client.query(`INSERT INTO product_payment_inbox_v1
        (product_id,gateway,provider_account_id,environment,external_event_id,tenant_id,external_resource_id,payload,payload_sha256)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8::jsonb,$9) ON CONFLICT DO NOTHING RETURNING external_event_id`,
      [...scopeParams, event.externalEventId, tenantId, event.externalResourceId, payload, hash]);
      if (!inserted.rows.length) {
        const existing = await client.query(`SELECT payload_sha256 FROM product_payment_inbox_v1 WHERE ${predicate} AND external_event_id=$5`, [...scopeParams, event.externalEventId]);
        if (existing.rows[0]?.payload_sha256 !== hash) throw new Error('payment event identity collision');
      }
      await client.query('COMMIT');
      return inserted.rows.length ? 'accepted' : 'duplicate';
    } catch (error) { await client.query('ROLLBACK'); throw error; }
    finally { client.release(); }
  }

  /** Handler may only perform product DB writes via tx. External effects require an outbox. */
  async processNext(scope: PaymentInboxScope, handler: (tx: PaymentSqlTransaction, event: Readonly<NormalizedPaymentEvent>) => Promise<void>): Promise<'idle' | 'processed' | 'retry' | 'dead_letter'> {
    const args = parameters(scope), client = await this.pool.connect();
    let row: InboxRow | undefined;
    try {
      await client.query('BEGIN');
      row = (await client.query<InboxRow>(`SELECT external_event_id,tenant_id,external_resource_id,payload,attempts
        FROM product_payment_inbox_v1 WHERE ${predicate} AND state='pending' AND available_at<=clock_timestamp()
        ORDER BY received_at,external_event_id LIMIT 1 FOR UPDATE SKIP LOCKED`, args)).rows[0];
      if (!row) { await client.query('COMMIT'); return 'idle'; }
      // Serialize effects for the same resource across distinct provider events.
      await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))', [JSON.stringify([...args, row.external_resource_id])]);
      await handler(Object.freeze({query:client.query.bind(client)}), Object.freeze(row.payload));
      await client.query(`UPDATE product_payment_inbox_v1 SET state='processed',attempts=attempts+1,
        processed_at=clock_timestamp(),last_error_code=NULL WHERE ${predicate} AND external_event_id=$5`, [...args, row.external_event_id]);
      await client.query('COMMIT');
      return 'processed';
    } catch (error) {
      await client.query('ROLLBACK');
      // Failure to commit is ambiguous. Do not reset processed state or repeat effects:
      // this guarded update only schedules an event still pending after rollback.
      if (!row) throw error;
      const result = await client.query(`UPDATE product_payment_inbox_v1 SET attempts=attempts+1,
        state=CASE WHEN attempts+1 >= $6 THEN 'dead_letter' ELSE 'pending' END,
        available_at=clock_timestamp()+($7::integer*interval '1 second'),last_error_code='processor_failed'
        WHERE ${predicate} AND external_event_id=$5 AND state='pending' RETURNING state`,
      [...args, row.external_event_id, this.maxAttempts, this.retryDelaySeconds]);
      if (!result.rows.length) throw new Error('payment processing outcome requires reconciliation');
      return result.rows[0].state === 'dead_letter' ? 'dead_letter' : 'retry';
    } finally { client.release(); }
  }

  /** Privileged operation: authorize the actor in the product before calling. */
  async replay(scope: PaymentInboxScope, eventId: string, request: { replayId: string; actorId: string; reasonCode: string }): Promise<'replayed' | 'duplicate'> {
    const args = parameters(scope); identifier(eventId);
    identifier(request.replayId); identifier(request.actorId); identifier(request.reasonCode);
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('SELECT pg_advisory_xact_lock(hashtextextended($1,0))', ['replay:'+request.replayId]);
      const prior = await client.query(`SELECT product_id,gateway,provider_account_id,environment,external_event_id,actor_id,reason_code
        FROM product_payment_inbox_replay_v1 WHERE replay_id=$1`, [request.replayId]);
      if (prior.rows.length) {
        const p=prior.rows[0];
        if (JSON.stringify([p.product_id,p.gateway,p.provider_account_id,p.environment,p.external_event_id,p.actor_id,p.reason_code]) !== JSON.stringify([...args,eventId,request.actorId,request.reasonCode])) throw new Error('replay request identity collision');
        await client.query('COMMIT'); return 'duplicate';
      }
      const updated = await client.query(`UPDATE product_payment_inbox_v1 SET state='pending',available_at=clock_timestamp(),last_error_code=NULL
        WHERE ${predicate} AND external_event_id=$5 AND state='dead_letter' RETURNING external_event_id`, [...args,eventId]);
      if (!updated.rows.length) throw new Error('only a dead-letter event may be replayed');
      await client.query(`INSERT INTO product_payment_inbox_replay_v1
        (replay_id,product_id,gateway,provider_account_id,environment,external_event_id,actor_id,reason_code)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)`, [request.replayId,...args,eventId,request.actorId,request.reasonCode]);
      await client.query('COMMIT'); return 'replayed';
    } catch (error) { await client.query('ROLLBACK'); throw error; }
    finally { client.release(); }
  }

  /** Aggregate-only operational signals. No event, tenant or payload is exported. */
  async stats(scope: PaymentInboxScope): Promise<{ pending: number; processed: number; deadLetter: number; oldestPendingAgeSeconds: number | null }> {
    const args=parameters(scope), client=await this.pool.connect();
    try {
      const row=(await client.query(`SELECT COUNT(*) FILTER (WHERE state='pending') AS pending,
        COUNT(*) FILTER (WHERE state='processed') AS processed, COUNT(*) FILTER (WHERE state='dead_letter') AS dead_letter,
        EXTRACT(EPOCH FROM (clock_timestamp()-(MIN(received_at) FILTER (WHERE state='pending')))) AS age
        FROM product_payment_inbox_v1 WHERE ${predicate}`,args)).rows[0];
      const count=(value:unknown)=>{const n=Number(value);if(!Number.isSafeInteger(n)||n<0)throw new Error('invalid payment inbox count');return n;};
      return {pending:count(row.pending),processed:count(row.processed),deadLetter:count(row.dead_letter),oldestPendingAgeSeconds:row.age===null?null:Math.max(0,Number(row.age))};
    } finally {client.release();}
  }
}
