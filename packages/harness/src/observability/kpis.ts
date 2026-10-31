/** CI-01 v1: pure calculations over a consumer-supplied, deduplicated cohort.
 * The caller owns source verification, window selection and completeness.
 * No collection, persistence, inference of missing data or external export.
 */
export interface KpiEvidence {
  windowStart: string;
  windowEnd: string;
  source: string;
  coverage: 'complete' | 'partial';
}
export interface KpiResult extends KpiEvidence {
  value: number | null;
  reason: 'missing_data' | 'empty_denominator' | null;
}
export type KpiInput =
  | { kind: 'lead_time_ms'; durationsMs: readonly number[] | null }
  | { kind: 'change_failure_rate'; failedDeployments: number | null; deployments: number | null }
  | { kind: 'acceptance_rate'; accepted: number | null; submitted: number | null }
  | { kind: 'validated_demand_rate'; confirmed: number | null; evaluated: number | null }
  | { kind: 'cost_per_delivery_minor'; costMinor: number | null; accepted: number | null; currency: string }
  | { kind: 'contribution_margin_minor'; netRevenueMinor: number | null; variableCostMinor: number | null; currency: string };

function count(value: number | null): void {
  if (value !== null && (!Number.isSafeInteger(value) || value < 0)) {
    throw new Error('KPI counts and amounts must be nonnegative safe integers');
  }
}

function timestamp(value: string): number {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?(Z|[+-]\d{2}:\d{2})$/.exec(value);
  if (!match) return NaN;
  const [, y, m, d, h, min, s, zone] = match;
  const year = Number(y), month = Number(m), day = Number(d);
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (month < 1 || month > 12 || day < 1 || day > days[month - 1] || Number(h) > 23 || Number(min) > 59 || Number(s) > 59) return NaN;
  if (zone !== 'Z' && (Number(zone.slice(1, 3)) > 23 || Number(zone.slice(4)) > 59)) return NaN;
  return Date.parse(value);
}

/** Rates are fractions [0,1]. Money is in one explicit currency's minor units;
 * per-delivery averages may be fractional and must not be used for settlement.
 * A partial result always retains its partial coverage, including numeric zero.
 */
export function calculateKpi(input: KpiInput, evidence: KpiEvidence): KpiResult & { kind: KpiInput['kind']; currency?: string } {
  const start = timestamp(evidence.windowStart), end = timestamp(evidence.windowEnd);
  if (!Number.isFinite(start) || !Number.isFinite(end) || start >= end) {
    throw new Error('KPI requires an ordered window with explicit timezone');
  }
  if (!evidence.source.trim() || !['complete', 'partial'].includes(evidence.coverage)) throw new Error('KPI requires source and coverage');
  const monetary = input.kind === 'cost_per_delivery_minor' || input.kind === 'contribution_margin_minor';
  const currency = monetary ? input.currency : undefined;
  if (monetary && (typeof currency !== 'string' || !/^[A-Z]{3}$/.test(currency))) throw new Error('KPI requires an explicit currency code');
  const result = (value: number | null, reason: KpiResult['reason'] = null) => ({
    windowStart: evidence.windowStart, windowEnd: evidence.windowEnd,
    source: evidence.source, coverage: evidence.coverage, kind: input.kind,
    ...(currency === undefined ? {} : { currency }), value, reason,
  });
  if (input.kind === 'lead_time_ms') {
    if (input.durationsMs === null) return result(null, 'missing_data');
    if (!input.durationsMs.length) return result(null, 'empty_denominator');
    let total = 0;
    for (const duration of input.durationsMs) {
      if (typeof duration !== 'number') throw new Error('KPI duration must be a number');
      count(duration); total += duration;
      if (!Number.isSafeInteger(total)) throw new Error('KPI duration sum exceeds safe integer range');
    }
    return result(total / input.durationsMs.length);
  }
  let numerator: number | null, denominator: number | null;
  switch (input.kind) {
    case 'change_failure_rate': numerator = input.failedDeployments; denominator = input.deployments; break;
    case 'acceptance_rate': numerator = input.accepted; denominator = input.submitted; break;
    case 'validated_demand_rate': numerator = input.confirmed; denominator = input.evaluated; break;
    case 'cost_per_delivery_minor': numerator = input.costMinor; denominator = input.accepted; break;
    case 'contribution_margin_minor': numerator = input.netRevenueMinor; denominator = input.variableCostMinor; break;
    default: throw new Error('unsupported KPI');
  }
  count(numerator); count(denominator);
  if (numerator === null || denominator === null) return result(null, 'missing_data');
  if (input.kind === 'contribution_margin_minor') return result(numerator - denominator);
  if (input.kind !== 'cost_per_delivery_minor' && numerator > denominator) throw new Error('KPI numerator exceeds cohort denominator');
  if (denominator === 0) return result(null, 'empty_denominator');
  return result(numerator / denominator);
}
