import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { calculateKpi, type KpiEvidence, type KpiInput } from './kpis.js';
import { calculateKpi as rootCalculateKpi } from '../index.js';

const evidence: KpiEvidence = { windowStart: '2026-10-01T00:00:00Z', windowEnd: '2026-11-01T00:00:00Z', source: 'fixture-only', coverage: 'complete' };
test('matches the cross-language KPI contract', () => {
  const cases = JSON.parse(readFileSync(new URL('../../fixtures/kpi-cases.json', import.meta.url), 'utf8'));
  for (const item of cases) {
    const context = item.evidence === null ? null : { ...evidence, ...item.evidence };
    if (item.error) assert.throws(() => calculateKpi(item.input, context), item.name);
    else {
      const result = calculateKpi(item.input, context);
      assert.equal(result.value, item.value, item.name);
      assert.equal(result.reason, item.reason, item.name);
      assert.equal(result.coverage, context.coverage, item.name);
      assert.equal(result.windowStart, context.windowStart, item.name);
      assert.equal(result.windowEnd, context.windowEnd, item.name);
      assert.equal(result.source, context.source, item.name);
      assert.equal(result.kind, item.input.kind, item.name);
      assert.equal(result.currency, item.currency, item.name);
    }
  }
});
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
  assert.equal(calculateKpi(input, { ...evidence, windowStart: '9999-12-31T23:59:59.999+23:59', windowEnd: '9999-12-31T23:59:59.999Z' }).value, 1);
});
test('public root export is the documented TypeScript entry point', () => {
  assert.equal(rootCalculateKpi, calculateKpi);
  assert.equal(rootCalculateKpi({ kind: 'acceptance_rate', accepted: 1, submitted: 2 }, evidence).value, 0.5);
});
test('values JSON cannot represent stay rejected and never become empty or zero', () => {
  const lead = (durationsMs: unknown) => calculateKpi({ kind: 'lead_time_ms', durationsMs } as unknown as KpiInput, evidence);
  for (const durationsMs of [undefined, {}, { length: 0 }, '', 0, new Set<number>(), new Float64Array(0), [Infinity], [-Infinity], [1n]]) {
    assert.throws(() => lead(durationsMs));
  }
  for (const accepted of [-Infinity, 2n, undefined]) {
    assert.throws(() => calculateKpi({ kind: 'acceptance_rate', accepted, submitted: 4 } as unknown as KpiInput, evidence));
  }
  const coerced = { toString: () => evidence.windowStart };
  assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs: [1] }, { ...evidence, windowStart: coerced } as unknown as KpiEvidence));
  assert.throws(() => calculateKpi({ kind: 'lead_time_ms', durationsMs: [1] }, { ...evidence, source: ['x'] } as unknown as KpiEvidence));
  const margin = calculateKpi({ kind: 'contribution_margin_minor', netRevenueMinor: -0, variableCostMinor: 0, currency: 'BRL' }, evidence);
  assert.ok(Object.is(margin.value, 0));
  assert.ok(Object.is(calculateKpi({ kind: 'cost_per_delivery_minor', costMinor: -0, accepted: 3, currency: 'BRL' }, evidence).value, 0));
});
test('malformed top-level arguments fail with the documented error', () => {
  assert.throws(() => calculateKpi(null as unknown as KpiInput, evidence), { name: 'Error', message: 'KPI requires input and evidence' });
  assert.throws(() => calculateKpi({ kind: 'acceptance_rate', accepted: 1, submitted: 2 }, null as unknown as KpiEvidence), { name: 'Error', message: 'KPI requires input and evidence' });
  assert.throws(() => calculateKpi({ kind: 'unknown' } as unknown as KpiInput, evidence), { name: 'Error', message: 'unsupported KPI' });
});
