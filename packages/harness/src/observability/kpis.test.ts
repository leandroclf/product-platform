import test from 'node:test';
import assert from 'node:assert/strict';
import { calculateKpi, type KpiEvidence, type KpiInput } from './kpis.js';

const evidence: KpiEvidence = { windowStart: '2026-10-01T00:00:00Z', windowEnd: '2026-11-01T00:00:00Z', source: 'fixture-only', coverage: 'complete' };
test('rates use the cohort denominator, not CI executions', () => {
  assert.equal(calculateKpi({ kind: 'change_failure_rate', failedDeployments: 2, deployments: 10 }, evidence).value, 0.2);
  assert.equal(calculateKpi({ kind: 'acceptance_rate', accepted: 3, submitted: 4 }, evidence).value, 0.75);
  assert.equal(calculateKpi({ kind: 'validated_demand_rate', confirmed: 1, evaluated: 5 }, evidence).value, 0.2);
});
test('missing, empty and observed zero are distinct', () => {
  assert.equal(calculateKpi({ kind: 'acceptance_rate', accepted: null, submitted: 4 }, evidence).reason, 'missing_data');
  assert.equal(calculateKpi({ kind: 'acceptance_rate', accepted: 0, submitted: 0 }, evidence).reason, 'empty_denominator');
  const observed = calculateKpi({ kind: 'acceptance_rate', accepted: 0, submitted: 4 }, { ...evidence, coverage: 'partial' });
  assert.equal(observed.value, 0); assert.equal(observed.coverage, 'partial'); assert.equal(observed.reason, null);
});
test('lead time is mean execution-to-acceptance duration in milliseconds', () => {
  assert.equal(calculateKpi({ kind: 'lead_time_ms', durationsMs: [1000, 3000] }, evidence).value, 2000);
  assert.equal(calculateKpi({ kind: 'lead_time_ms', durationsMs: [] }, evidence).reason, 'empty_denominator');
  assert.equal(calculateKpi({ kind: 'lead_time_ms', durationsMs: null }, evidence).reason, 'missing_data');
  for (const durationsMs of [[-1], [NaN], [1.5], [Number.MAX_SAFE_INTEGER, 1]]) assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs }, evidence));
});
test('money retains currency, allows negative margin and fractional average', () => {
  const cost = calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: 101, accepted: 2, currency: 'BRL' }, evidence);
  assert.equal(cost.value, 50.5); assert.equal(cost.currency, 'BRL');
  assert.equal(calculateKpi({ kind: 'contribution_margin_minor', netRevenueMinor: 100, variableCostMinor: 200, currency: 'BRL' }, evidence).value, -100);
  assert.equal(calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: null, accepted: 2, currency: 'USD' }, evidence).value, null);
  assert.equal(calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: 100, accepted: 0, currency: 'USD' }, evidence).reason, 'empty_denominator');
});
test('invalid counts, cohorts, windows and provenance fail closed', () => {
  for (const accepted of [-1, NaN, Infinity, 1.5, Number.MAX_SAFE_INTEGER + 1, 5]) assert.throws(() => calculateKpi({ kind: 'acceptance_rate', accepted, submitted: 4 }, evidence));
  for (const windowEnd of ['invalid', evidence.windowStart, '2026-09-01T00:00:00Z', '2026-11-01T00:00:00']) assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs: [1] }, { ...evidence, windowEnd }));
  assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs: [1] }, { ...evidence, source: ' ' }));
  assert.throws(() => calculateKpi({ kind: 'contribution_margin_minor', netRevenueMinor: 1, variableCostMinor: -1, currency: 'BRL' }, evidence));
  assert.throws(() => calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: 1, accepted: 1, currency: 'brl' }, evidence));
});
test('untyped callers cannot turn missing durations into zero or omit money currency', () => {
  for (const durationsMs of [[null], [undefined], ['1']]) {
    assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs } as unknown as KpiInput, evidence));
  }
  for (const currency of [undefined, null, 123]) {
    assert.throws(() => calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: 100, accepted: 1, currency } as unknown as KpiInput, evidence));
    assert.throws(() => calculateKpi({ kind: 'contribution_margin_minor', netRevenueMinor: 100, variableCostMinor: 1, currency } as unknown as KpiInput, evidence));
  }
});
test('windows reject impossible calendar dates and compare timezone instants', () => {
  const input: KpiInput = { kind: 'lead_time_ms', durationsMs: [1] };
  for (const windowStart of ['2026-02-30T00:00:00Z', '2025-02-29T00:00:00Z', '2026-10-01T24:00:00Z']) {
    assert.throws(() => calculateKpi(input, { ...evidence, windowStart }));
  }
  assert.equal(calculateKpi(input, { ...evidence, windowStart: '2024-02-29T00:00:00-03:00' }).value, 1);
  assert.throws(() => calculateKpi(input, { ...evidence, windowStart: '2026-10-01T00:00:00Z', windowEnd: '2026-09-30T21:00:00-03:00' }));
});
