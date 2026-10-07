export type ProductEventName='signup_completed'|'activation_completed'|'feature_used'|'limit_reached'|'upgrade_intent'|'subscription_changed'|'feedback_submitted';
export interface ProductEvent { schema_version:'1.0'; event:ProductEventName; product_id:string; environment:string; release_sha:string; occurred_at:string; user_id?:string|null; account_id?:string|null; plan_id?:string|null; session_id?:string|null; feature?:string|null; outcome?:string|null; }
export interface ProductEventContext { productId:string; environment:string; releaseSha:string; now?:()=>Date; }
type Fields=Partial<Omit<ProductEvent,'schema_version'|'event'|'product_id'|'environment'|'release_sha'|'occurred_at'>>;
const names = new Set<ProductEventName>(['signup_completed', 'activation_completed', 'feature_used', 'limit_reached', 'upgrade_intent', 'subscription_changed', 'feedback_submitted']);
const required = ['schema_version', 'event', 'product_id', 'environment', 'release_sha', 'occurred_at'];
const optional = ['user_id', 'account_id', 'plan_id', 'session_id', 'feature', 'outcome'];
const allowed = new Set([...required, ...optional]);

/** Validate untyped callers against the ProductEvent v1 wire contract. */
export function validateProductEvent(value: unknown): ProductEvent {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('product event must be an object');
  const event = value as Record<string, unknown>;
  if (Object.keys(event).some(key => !allowed.has(key))) throw new Error('unknown product event field');
  for (const key of required) {
    if (typeof event[key] !== 'string' || event[key].length === 0) throw new Error('invalid product event metadata: ' + key);
  }
  if (event.schema_version !== '1.0' || !names.has(event.event as ProductEventName)) throw new Error('invalid product event version or name');
  for (const key of optional) {
    if (key in event && event[key] !== null && typeof event[key] !== 'string') throw new Error('invalid product event field: ' + key);
  }
  const time = event.occurred_at as string;
  if (!/^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$/.test(time) || Number.isNaN(Date.parse(time))) throw new Error('invalid product event timestamp');
  const localDate = new Date(time.slice(0, 19).toUpperCase() + 'Z');
  if (Number.isNaN(localDate.getTime()) || localDate.toISOString().slice(0, 19) !== time.slice(0, 19).toUpperCase()) throw new Error('invalid product event calendar date');
  return value as ProductEvent;
}

export function createProductEvent(context: ProductEventContext, event: ProductEventName, fields: Fields = {}): ProductEvent {
  return validateProductEvent({ ...fields, schema_version: '1.0', event, product_id: context.productId, environment: context.environment, release_sha: context.releaseSha, occurred_at: (context.now?.() ?? new Date()).toISOString() });
}
