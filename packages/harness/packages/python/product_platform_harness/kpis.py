"""CI-01 calculations over a consumer-supplied cohort; no collection or export."""
from __future__ import annotations

import math
import re
from typing import Any

_MAX_SAFE = 2**53 - 1
_TIMESTAMP = re.compile(r"^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})(?:\.([0-9]{1,3}))?(Z|[+-][0-9]{2}:[0-9]{2})$")
_JS_WHITESPACE = "\t\n\v\f\r \u00a0\u1680" + "".join(map(chr, range(0x2000, 0x200B))) + "\u2028\u2029\u202f\u205f\u3000\ufeff"
_FIELDS = {
    'change_failure_rate': ('failedDeployments', 'deployments'),
    'acceptance_rate': ('accepted', 'submitted'),
    'validated_demand_rate': ('confirmed', 'evaluated'),
    'cost_per_delivery_minor': ('costMinor', 'accepted'),
    'contribution_margin_minor': ('netRevenueMinor', 'variableCostMinor'),
}


def _timestamp(value: Any) -> int:
    match = _TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError('KPI requires an ordered window with explicit timezone')
    year, month, day, hour, minute, second = map(int, match.group(1, 2, 3, 4, 5, 6))
    fraction, zone = match.group(7, 8)
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not 1 <= month <= 12 or not 1 <= day <= days[month - 1] or hour > 23 or minute > 59 or second > 59:
        raise ValueError('invalid KPI timestamp')
    offset = 0
    if zone != 'Z':
        zone_hour, zone_minute = int(zone[1:3]), int(zone[4:6])
        if zone_hour > 23 or zone_minute > 59:
            raise ValueError('invalid KPI timezone')
        offset = (zone_hour * 60 + zone_minute) * (1 if zone[0] == '+' else -1)
    elapsed_days = 365 * year + (year + 3) // 4 - (year + 99) // 100 + (year + 399) // 400
    elapsed_days += sum(days[:month - 1]) + day - 1
    return ((elapsed_days * 24 * 60 + hour * 60 + minute - offset) * 60 + second) * 1000 + int((fraction or '').ljust(3, '0'))


def _count(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('KPI counts and amounts must be nonnegative safe integers')
    if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
        raise ValueError('KPI counts and amounts must be nonnegative safe integers')
    if value < 0 or value > _MAX_SAFE:
        raise ValueError('KPI counts and amounts must be nonnegative safe integers')
    return int(value)


def calculate_kpi(input: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Return the same CI-01 fields and missing-data semantics as the TS runtime."""
    if not isinstance(input, dict) or not isinstance(evidence, dict):
        raise ValueError('KPI requires input and evidence')
    start, end = _timestamp(evidence.get('windowStart')), _timestamp(evidence.get('windowEnd'))
    if start >= end:
        raise ValueError('KPI requires an ordered window')
    source, coverage = evidence.get('source'), evidence.get('coverage')
    if not isinstance(source, str) or not source.strip(_JS_WHITESPACE) or coverage not in ('complete', 'partial'):
        raise ValueError('KPI requires source and coverage')
    kind = input.get('kind')
    if not isinstance(kind, str) or (kind != 'lead_time_ms' and kind not in _FIELDS):
        raise ValueError('unsupported KPI')
    result = {key: evidence[key] for key in ('windowStart', 'windowEnd', 'source', 'coverage')}
    result['kind'] = kind
    if kind in ('cost_per_delivery_minor', 'contribution_margin_minor'):
        currency = input.get('currency')
        if not isinstance(currency, str) or not re.fullmatch(r'[A-Z]{3}', currency):
            raise ValueError('KPI requires an explicit currency code')
        result['currency'] = currency

    def finish(value: int | float | None, reason: str | None = None) -> dict[str, Any]:
        return {**result, 'value': value, 'reason': reason}

    if kind == 'lead_time_ms':
        if 'durationsMs' not in input:
            raise ValueError('KPI durations are required')
        durations = input['durationsMs']
        if durations is None:
            return finish(None, 'missing_data')
        if not isinstance(durations, (list, tuple)):
            raise ValueError('KPI durations must be an array')
        if not durations:
            return finish(None, 'empty_denominator')
        total = 0
        for duration in durations:
            if duration is None:
                raise ValueError('KPI duration must be a number')
            total += _count(duration)
            if total > _MAX_SAFE:
                raise ValueError('KPI duration sum exceeds safe integer range')
        return finish(total / len(durations))

    fields = _FIELDS[kind]
    if any(field not in input for field in fields):
        raise ValueError('KPI requires both inputs')
    numerator, denominator = (_count(input[field]) for field in fields)
    if numerator is None or denominator is None:
        return finish(None, 'missing_data')
    if kind == 'contribution_margin_minor':
        return finish(numerator - denominator)
    if kind != 'cost_per_delivery_minor' and numerator > denominator:
        raise ValueError('KPI numerator exceeds cohort denominator')
    if denominator == 0:
        return finish(None, 'empty_denominator')
    return finish(numerator / denominator)
