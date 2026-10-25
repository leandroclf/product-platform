import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { PGlite } from '@electric-sql/pglite';
import { PostgresPaymentInbox } from '../dist/index.js';

// PGlite runs actual PostgreSQL SQL with disk persistence, but a single backend.
// Serializing client leases models a one-connection pool, not multi-host locking.
function poolFor(db, loseCommit=()=>false) {
  let tail=Promise.resolve();
  return { async connect() {
    const previous=tail; let unlock; tail=new Promise(resolve=>{unlock=resolve;});
    await previous;
    return {query:async(sql,values)=>{
      const result=await db.query(sql,values);
      if(sql==='COMMIT' && loseCommit()) throw new Error('synthetic lost acknowledgement');
      return result;
    },release:unlock};
  }};
}
const scope={productId:'fixture-product',providerAccountId:'fixture-account',gateway:'stripe',environment:'sandbox'};
const event=(id,overrides={})=>({idempotencyKey:'stripe:'+id,gateway:'stripe',externalEventId:id,externalResourceId:'pi_fixture',type:'payment',action:'payment_intent.succeeded',status:'paid',amountMinor:100,currency:'BRL',tenantId:'tenant-a',occurredAt:'2026-10-25T12:00:00.000Z',...overrides});
const gateway=(value,verified=true)=>({name:value.gateway,verifyWebhook:async()=>verified,normalizeWebhook:async()=>value});
const input={rawBody:'synthetic',headers:new Headers(),url:new URL('https://example.invalid/webhook')};
let db,dir,pool;
before(async()=>{
  dir=await mkdtemp(join(tmpdir(),'payment-inbox-'));db=new PGlite(dir);await db.waitReady;
  await db.exec(await readFile(new URL('../migrations/001_payment_inbox.sql',import.meta.url),'utf8'));
  await db.exec('CREATE TABLE fixture_effects (id text PRIMARY KEY, amount integer NOT NULL)');
  pool=poolFor(db);
});
after(async()=>{await db.close();await rm(dir,{recursive:true,force:true});});
const ingest=(inbox,value,sc=scope,tenant='tenant-a')=>inbox.ingest(sc,tenant,gateway(value),input);
const effect=async(tx,e)=>{await tx.query('INSERT INTO fixture_effects VALUES ($1,$2)',[e.externalEventId,e.amountMinor]);};

test('rejects unauthenticated events before opening a database connection',async()=>{
  const inbox=new PostgresPaymentInbox({connect:()=>{throw new Error('must not connect');}});
  await assert.rejects(()=>inbox.ingest(scope,'tenant-a',gateway(event('unauth'),false),input),/unauthenticated/);
});
test('duplicate deliveries are atomic and effects run once',async()=>{
  const inbox=new PostgresPaymentInbox(pool),e=event('duplicate');
  const results=await Promise.all(Array.from({length:8},()=>ingest(inbox,e)));
  assert.equal(results.filter(x=>x==='accepted').length,1);
  assert.equal(results.filter(x=>x==='duplicate').length,7);
  assert.equal(await inbox.processNext(scope,effect),'processed');
  assert.equal(await inbox.processNext(scope,effect),'idle');
  assert.equal((await db.query('SELECT * FROM fixture_effects WHERE id=$1',['duplicate'])).rows.length,1);
});
test('event identity conflicts cannot move tenants or overwrite the original amount',async()=>{
  const inbox=new PostgresPaymentInbox(pool),e=event('conflict');await ingest(inbox,e);
  await assert.rejects(()=>ingest(inbox,{...e,amountMinor:101}),/identity collision/);
  await assert.rejects(()=>ingest(inbox,{...e,tenantId:'tenant-b'},scope,'tenant-b'),/identity collision/);
  assert.equal((await db.query('SELECT payload FROM product_payment_inbox_v1 WHERE external_event_id=$1',['conflict'])).rows[0].payload.amountMinor,100);
  await inbox.processNext(scope,effect);
});
test('environment and provider account isolate identical provider event IDs',async()=>{
  const inbox=new PostgresPaymentInbox(pool),e=event('scoped');
  const other={...scope,providerAccountId:'account-b'}, prod={...scope,environment:'production'};
  assert.equal(await ingest(inbox,e),'accepted');assert.equal(await ingest(inbox,e,other),'accepted');assert.equal(await ingest(inbox,e,prod),'accepted');
  for(const s of [scope,other,prod]) assert.equal(await inbox.processNext(s,async()=>{}),'processed');
});
test('callback failure rolls back product effects before bounded retries',async()=>{
  const inbox=new PostgresPaymentInbox(pool,{retryDelaySeconds:0,maxAttempts:2});await ingest(inbox,event('rollback'));
  assert.equal(await inbox.processNext(scope,async(tx,e)=>{await effect(tx,e);throw new Error('secret must not be persisted');}),'retry');
  assert.equal((await db.query('SELECT * FROM fixture_effects WHERE id=$1',['rollback'])).rows.length,0);
  assert.equal(await inbox.processNext(scope,effect),'processed');
  const row=(await db.query('SELECT * FROM product_payment_inbox_v1 WHERE external_event_id=$1',['rollback'])).rows[0];
  assert.equal(row.attempts,2);assert.equal(row.state,'processed');assert.equal(row.last_error_code,null);
});
test('dead-letter replay is audited and does not erase historical attempts',async()=>{
  const inbox=new PostgresPaymentInbox(pool,{retryDelaySeconds:0,maxAttempts:2});await ingest(inbox,event('dead'));
  const failure=async()=>{throw new Error('sensitive-error');};
  assert.equal(await inbox.processNext(scope,failure),'retry');assert.equal(await inbox.processNext(scope,failure),'dead_letter');assert.equal(await inbox.processNext(scope,failure),'idle');
  const request={replayId:'replay-1',actorId:'operator-id',reasonCode:'dependency-restored'};
  assert.equal(await inbox.replay(scope,'dead',request),'replayed');assert.equal(await inbox.replay(scope,'dead',request),'duplicate');
  await assert.rejects(()=>inbox.replay(scope,'dead',{...request,actorId:'another-operator'}),/identity collision/);
  assert.equal(await inbox.processNext(scope,effect),'processed');
  const row=(await db.query('SELECT * FROM product_payment_inbox_v1 WHERE external_event_id=$1',['dead'])).rows[0];
  assert.equal(row.attempts,3);
  const audit=(await db.query('SELECT actor_id,reason_code FROM product_payment_inbox_replay_v1 WHERE replay_id=$1',['replay-1'])).rows[0];
  assert.deepEqual(audit,{actor_id:'operator-id',reason_code:'dependency-restored'});
  await assert.rejects(()=>inbox.replay(scope,'dead',{...request,replayId:'new-replay'}),/only a dead-letter/);
});
test('ambiguous successful commit requires reconciliation without duplicating effects',async()=>{
  let lose=false;
  const inbox=new PostgresPaymentInbox(poolFor(db,()=>{if(!lose)return false;lose=false;return true;}));
  await ingest(inbox,event('ambiguous'));lose=true;
  await assert.rejects(()=>inbox.processNext(scope,effect),/requires reconciliation/);
  assert.equal(await inbox.processNext(scope,effect),'idle');
  assert.equal((await db.query('SELECT * FROM fixture_effects WHERE id=$1',['ambiguous'])).rows.length,1);
});
test('only allowlisted fields persist and invalid monetary/tenant data fails closed',async()=>{
  const inbox=new PostgresPaymentInbox(pool);
  await ingest(inbox,event('allowlist',{metadata:{email:'synthetic-sensitive-value'}}));
  const row=(await db.query('SELECT payload FROM product_payment_inbox_v1 WHERE external_event_id=$1',['allowlist'])).rows[0];
  assert.equal(JSON.stringify(row).includes('synthetic-sensitive-value'),false);
  await assert.rejects(()=>ingest(inbox,event('invalid-amount',{amountMinor:1.5})),/minor units/);
  await assert.rejects(()=>ingest(inbox,event('invalid-tenant',{tenantId:'tenant-b'})),/tenant does not match/);
  await inbox.processNext(scope,async()=>{});
});
test('accepted pending events survive a database close and reopen',async()=>{
  let inbox=new PostgresPaymentInbox(pool);await ingest(inbox,event('restart'));
  await db.close();db=new PGlite(dir);await db.waitReady;pool=poolFor(db);inbox=new PostgresPaymentInbox(pool);
  assert.equal(await inbox.processNext(scope,effect),'processed');
  assert.equal(await ingest(inbox,event('restart')),'duplicate');
});
test('operational stats are aggregate-only and scoped to the account/environment',async()=>{
  const inbox=new PostgresPaymentInbox(pool);
  const stats=await inbox.stats(scope);
  assert.ok(stats.processed>=1);assert.equal(stats.pending,0);assert.equal(stats.oldestPendingAgeSeconds,null);
  assert.deepEqual(Object.keys(stats).sort(),['deadLetter','oldestPendingAgeSeconds','pending','processed']);
  assert.equal((await inbox.stats({...scope,providerAccountId:'never-used'})).processed,0);
});
