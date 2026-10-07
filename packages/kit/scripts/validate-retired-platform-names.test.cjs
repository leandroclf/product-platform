const { test } = require('node:test');
const assert = require('node:assert/strict');
const { findRetiredNames } = require('./validate-retired-platform-names.cjs');

test('rejects old active references even beside canonical names', () => {
  assert.deepEqual(findRetiredNames('docs/current.md', 'ai-kit product-platform-ai-kit'), ['ai-kit']);
  assert.deepEqual(findRetiredNames('docs/current.md', 'https://github.com/leandroclf/ai-engineering-team.git'), ['ai-engineering-team']);
  assert.deepEqual(findRetiredNames('docs/current.md', 'OmniCLI product-harness'), ['OmniCLI', 'product-harness']);
});
test('preserves exact executable and configuration identifiers only', () => {
  assert.deepEqual(findRetiredNames('docs/current.md', '`scripts/ai-kit` and `ai-kit.yaml`'), []);
  assert.deepEqual(findRetiredNames('docs/current.md', 'scripts/ai-kit-old ai-kit.yaml.old ai-kit'), ['ai-kit']);
});
test('permits only the explicit migration rows in the historical mapping', () => {
  assert.deepEqual(findRetiredNames('docs/LEGACY-CUTOVER-GATE.md', '| ai-kit | product-platform-kit |'), []);
  assert.deepEqual(findRetiredNames('docs/current.md', '| ai-kit | product-platform-kit |'), ['ai-kit']);
  assert.deepEqual(findRetiredNames('docs/LEGACY-CUTOVER-GATE.md', '| ai-kit | wrong |'), ['ai-kit']);
});
test('preserves immutable evidence and the exact legacy schema identity', () => {
  assert.deepEqual(findRetiredNames('docs/evolution/baseline-before.json', 'ai-kit'), []);
  assert.deepEqual(findRetiredNames('docs/evolution/verification-after.json', 'OmniCLI'), []);
  assert.deepEqual(findRetiredNames('docs/evolution/other.json', 'ai-kit'), ['ai-kit']);
  assert.deepEqual(findRetiredNames('contracts/payment-event/v1.schema.json', '{"$id":"https://ai-kit/contracts/payment-event/v1.schema.json"}'), []);
  assert.deepEqual(findRetiredNames('contracts/payment-event/v1.schema.json', '{"description":"ai-kit"}'), ['ai-kit']);
});
