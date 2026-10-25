import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { StripeAdapter } from './stripe.js';
import { gatewayFetch } from './http.js';
import type { WebhookInput } from './gateway.js';

const secret='synthetic-webhook-test';
const rawBody=JSON.stringify({id:'evt_fixture',type:'payment_intent.succeeded',created:1,data:{object:{id:'pi_fixture',status:'succeeded'}}});
function signature(timestamp:number, body=rawBody):string {
  return crypto.createHmac('sha256',secret).update(timestamp+'.'+body).digest('hex');
}
function input(header:string,body=rawBody):WebhookInput {
  return {rawBody:body,headers:new Headers({'stripe-signature':header}),url:new URL('https://example.invalid/webhook')};
}
test('rejects stale, future and malformed delivery timestamps without rejecting old events re-signed now',async(t)=>{
  const adapter=new StripeAdapter('unused',secret), now=1_700_000_000;
  t.mock.method(Date,'now',()=>now*1000);
  for(const timestamp of [1,now-301,now+301]) assert.equal(await adapter.verifyWebhook(input(`t=${timestamp},v1=${signature(timestamp)}`)),false);
  for(const timestamp of [now-300,now+300]) assert.equal(await adapter.verifyWebhook(input(`t=${timestamp},v1=${signature(timestamp)}`)),true);
  assert.equal(await adapter.verifyWebhook(input(`t=${now},v1=${signature(now)}`)),true);
  for(const t of ['NaN','1e20','-1','999999999999999999999']) assert.equal(await adapter.verifyWebhook(input(`t=${t},v1=${'0'.repeat(64)}`)),false);
  assert.equal(await adapter.verifyWebhook(input(`t=${now},t=${now},v1=${signature(now)}`)),false);
});
test('supports rotated v1 signatures and rejects tampering, truncation and empty secrets',async()=>{
  const adapter=new StripeAdapter('unused',secret),now=Math.floor(Date.now()/1000);
  assert.equal(await adapter.verifyWebhook(input(`t=${now}, v1=${'0'.repeat(64)}, v1=${signature(now)}, v0=ignored`)),true);
  assert.equal(await adapter.verifyWebhook(input(`t=${now},v1=${signature(now)}`,'{}')),false);
  assert.equal(await adapter.verifyWebhook(input(`t=${now},v1=${signature(now)}zz`)),false);
  assert.equal(await new StripeAdapter('unused','').verifyWebhook(input(`t=${now},v1=${signature(now)}`)),false);
});
test('normalization cannot bypass authentication and retains event-created time on a valid retry',async()=>{
  const adapter=new StripeAdapter('unused',secret), now=Math.floor(Date.now()/1000);
  await assert.rejects(()=>adapter.normalizeWebhook(input('t=1,v1=bad')),/invalid stripe webhook/);
  const result=await adapter.normalizeWebhook(input(`t=${now},v1=${signature(now)}`));
  assert.equal(result.status,'paid');
  assert.equal(result.occurredAt,'1970-01-01T00:00:01.000Z');
});
test('customer retries retain a scoped key; subscription requires persisted purchase identity',async()=>{
  const original=globalThis.fetch, requests:RequestInit[]=[];
  globalThis.fetch=async(_url,init)=>{requests.push(init!);return Response.json({id:'fixture',status:'incomplete'});};
  try {
    const adapter=new StripeAdapter('unused',secret);
    const customer={tenantId:'a',userId:'same',email:'fixture@example.invalid'};
    await adapter.createCustomer(customer); await adapter.createCustomer(customer);
    await adapter.createCustomer({...customer,tenantId:'b'});
    const key=(i:number)=>new Headers(requests[i].headers).get('Idempotency-Key');
    assert.equal(key(0),key(1)); assert.notEqual(key(0),key(2));
    const sub={tenantId:'a',customerExternalId:'cus_fixture',planExternalId:'price_fixture',email:customer.email};
    await assert.rejects(()=>adapter.createSubscription(sub),/persisted purchase/);
    assert.equal(requests.length,3);
    await adapter.createSubscription({...sub,idempotencyKey:'purchase-fixture'});
    assert.equal(key(3),'purchase-fixture');
    assert.ok(requests.every(x=>x.signal instanceof AbortSignal));
  } finally {globalThis.fetch=original;}
});
test('HTTP requests retain caller cancellation and do not retry ambiguous failures',async()=>{
  const original=globalThis.fetch, controller=new AbortController(); let count=0;
  controller.abort();
  globalThis.fetch=async(_url,init)=>{count++; assert.equal(init?.signal?.aborted,true); throw new Error('ambiguous timeout');};
  try {await assert.rejects(()=>gatewayFetch('https://example.invalid',{signal:controller.signal}),/ambiguous timeout/);assert.equal(count,1);}
  finally {globalThis.fetch=original;}
});
