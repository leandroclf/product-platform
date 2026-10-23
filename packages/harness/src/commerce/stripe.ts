import crypto from 'node:crypto';
import type { IPaymentGateway, WebhookInput } from './gateway.js';
import type { ChargeInput, CustomerInput, GatewayRef, NormalizedPaymentEvent, SubscriptionInput } from './types.js';
import { formBody, gatewayFetch } from './http.js';

export class StripeAdapter implements IPaymentGateway {
  readonly name = 'stripe' as const;
  constructor(private readonly secretKey: string, private readonly webhookSecret: string) {}
  private headers(idempotencyKey?: string): HeadersInit {
    if (idempotencyKey !== undefined && (!idempotencyKey.trim() || idempotencyKey.length > 255)) throw new Error('invalid stripe idempotency key');
    return { authorization: 'Bearer ' + this.secretKey, 'content-type': 'application/x-www-form-urlencoded', ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}) };
  }
  async createCustomer(input: CustomerInput): Promise<GatewayRef> {
    if (!input.tenantId?.trim() || !input.userId?.trim()) throw new Error('stripe customer requires tenant and user identity');
    const idempotencyKey = input.idempotencyKey ?? 'customer-v1:' + crypto.createHash('sha256').update(JSON.stringify([input.tenantId, input.userId])).digest('hex');
    const body=formBody({email:input.email,name:input.name,'metadata[tenant_id]':input.tenantId,'metadata[user_id]':input.userId});
    const r=await gatewayFetch<any>('https://api.stripe.com/v1/customers',{method:'POST',headers:this.headers(idempotencyKey),body}); return {id:r.id};
  }
  async createSubscription(input: SubscriptionInput): Promise<GatewayRef> {
    if (!input.idempotencyKey?.trim()) throw new Error('stripe subscription requires a persisted purchase idempotency key');
    const body=formBody({customer:input.customerExternalId,'items[0][price]':input.planExternalId,'metadata[tenant_id]':input.tenantId,payment_behavior:'default_incomplete'});
    const r=await gatewayFetch<any>('https://api.stripe.com/v1/subscriptions',{method:'POST',headers:this.headers(input.idempotencyKey),body}); return {id:r.id,status:r.status};
  }
  async processCharge(input: ChargeInput): Promise<GatewayRef> {
    const body=formBody({amount:input.amountMinor,currency:input.currency.toLowerCase(),customer:input.customerExternalId,payment_method:input.paymentMethodId,confirm:Boolean(input.paymentMethodId),'automatic_payment_methods[enabled]':!input.paymentMethodId,'metadata[tenant_id]':input.tenantId,description:input.description});
    const r=await gatewayFetch<any>('https://api.stripe.com/v1/payment_intents',{method:'POST',headers:this.headers(input.idempotencyKey),body}); return {id:r.id,status:r.status,clientSecret:r.client_secret};
  }
  async cancelSubscription(id:string):Promise<void>{ await gatewayFetch('https://api.stripe.com/v1/subscriptions/'+encodeURIComponent(id),{method:'DELETE',headers:this.headers()}); }
  async verifyWebhook({rawBody,headers}:WebhookInput):Promise<boolean>{
    const sig=headers.get('stripe-signature');
    if (!sig || sig.length > 8192 || !this.webhookSecret) return false;
    const entries=sig.split(',').map(v=>v.trim().split('=',2));
    const timestamps=entries.filter(x=>x[0]==='t').map(x=>x[1]);
    if (timestamps.length !== 1 || !/^\d+$/.test(timestamps[0] ?? '')) return false;
    const t=timestamps[0], timestamp=Number(t);
    // Verify the delivery timestamp, not event.created: Stripe re-signs retries.
    if (!Number.isSafeInteger(timestamp) || Math.abs(Date.now()/1000-timestamp) > 300) return false;
    const expected=crypto.createHmac('sha256',this.webhookSecret).update(t+'.'+rawBody).digest();
    // During rotation Stripe may send multiple v1 signatures; ignore other schemes.
    return entries.filter(([scheme])=>scheme==='v1').some(([,value])=>
      /^[a-fA-F0-9]{64}$/.test(value ?? '') && crypto.timingSafeEqual(expected,Buffer.from(value,'hex')));
  }
  async normalizeWebhook(input:WebhookInput):Promise<NormalizedPaymentEvent>{
    if (!await this.verifyWebhook(input)) throw new Error('invalid stripe webhook signature or delivery timestamp');
    const e=JSON.parse(input.rawBody); const o=e.data?.object||{}; const isSub=String(e.type).startsWith('customer.subscription.');
    const map:Record<string,string>={succeeded:'paid',requires_payment_method:'failed',active:'active',past_due:'past_due',canceled:'canceled',unpaid:'failed'};
    return {idempotencyKey:'stripe:'+e.id,gateway:this.name,externalEventId:e.id,externalResourceId:o.id,type:isSub?'subscription':'payment',action:e.type,status:(map[o.status]||'unknown') as any,amountMinor:o.amount_received??o.amount,currency:o.currency?.toUpperCase(),tenantId:o.metadata?.tenant_id,occurredAt:new Date((e.created||Math.floor(Date.now()/1000))*1000).toISOString(),rawType:e.type};
  }
}
