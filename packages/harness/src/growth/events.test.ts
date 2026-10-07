import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import * as events from './events.js';

test('matches the canonical kit compatibility corpus', () => {
  const fixtures = process.env.PRODUCT_EVENT_CASES ?? path.resolve('tests/fixtures/product-event-cases.json');
  const cases = JSON.parse(fs.readFileSync(fixtures, 'utf8'));
  const validate = events.validateProductEvent;
  for (const item of cases) {
    if (item.valid) assert.doesNotThrow(() => validate(item.event), item.name);
    else assert.throws(() => validate(item.event), Error, item.name);
  }
});

test('rejects arbitrary analytics payload even from an untyped caller', () => {
  assert.throws(() => events.createProductEvent({ productId: 'pilot', environment: 'test', releaseSha: 'sha' }, 'feature_used', { email: 'private@example.invalid' } as never));
});
