"""
Divergence projection — what Normalized Divergence does over the next days under a
scenario (all rest, or repeated easy sessions), computed deterministically.

Why this exists: divergence reduces to acute vs chronic TRIMP-per-load-mile,
    Ext ACWR / Int ACWR = r_chronic / r_acute,  r = TRIMP / Total Load Miles
so a rest day (zero load, zero TRIMP) leaves r_acute unchanged. Rest moves divergence
only as older sessions leave the 7-day window, and can deepen a breach. When the acute
window empties, divergence is 0/0 — undefined (None), not 0. The model is given this
projection as stated fact so it never promises that rest will normalize divergence.

Uses the same windows as production: 7-day acute sum / 7, and either the standard
28-day sum / 28 chronic or the enhanced per-calendar-day exponentially decayed chronic
(ExponentialDecayEngine). Divergence comes from the canonical calculation.

See .scratch/divergence-rest-projection/spec.md.
"""
from datetime import date, datetime, timedelta

from exponential_decay_engine import ActivityData, ExponentialDecayEngine
from unified_metrics_service import UnifiedMetricsService

ACUTE_DAYS = 7
STANDARD_CHRONIC_DAYS = 28

_engine = ExponentialDecayEngine()


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()


def _acwr_on(day, loads, trimps, method):
    """External and internal ACWR on `day` from per-date load/TRIMP totals."""
    acute_load = sum(loads.get(day - timedelta(days=i), 0.0) for i in range(ACUTE_DAYS)) / ACUTE_DAYS
    acute_trimp = sum(trimps.get(day - timedelta(days=i), 0.0) for i in range(ACUTE_DAYS)) / ACUTE_DAYS

    if method['kind'] == 'enhanced':
        period = method['chronic_period_days']
        window = [ActivityData(date=day - timedelta(days=i),
                               total_load_miles=loads.get(day - timedelta(days=i), 0.0),
                               trimp=trimps.get(day - timedelta(days=i), 0.0))
                  for i in range(period)]
        chronic = _engine.calculate_weighted_averages(window, day, method['decay_rate'], period)
        chronic_load, chronic_trimp = chronic.weighted_load_avg, chronic.weighted_trimp_avg
    elif method['kind'] == 'standard':
        chronic_load = sum(loads.get(day - timedelta(days=i), 0.0)
                           for i in range(STANDARD_CHRONIC_DAYS)) / STANDARD_CHRONIC_DAYS
        chronic_trimp = sum(trimps.get(day - timedelta(days=i), 0.0)
                            for i in range(STANDARD_CHRONIC_DAYS)) / STANDARD_CHRONIC_DAYS
    else:
        raise ValueError(f"unknown ACWR method: {method['kind']}")

    external = acute_load / chronic_load if chronic_load > 0 else 0.0
    internal = acute_trimp / chronic_trimp if chronic_trimp > 0 else 0.0
    return external, internal


def project_divergence(daily_rows, as_of, method, scenario, horizon=7):
    """Project External/Internal ACWR and Normalized Divergence from `as_of` forward.

    Args:
        daily_rows: iterable of (date, total_load_miles, trimp); several rows on one
            date are summed, a date with no row is a zero-load day.
        as_of: last day of real data (day 0 of the projection).
        method: {'kind': 'standard'} or
                {'kind': 'enhanced', 'chronic_period_days': int, 'decay_rate': float}
        scenario: {'kind': 'rest'} or
                  {'kind': 'easy', 'load': float, 'trimp_per_load': float} — one easy
                  session per projected day.
        horizon: number of projected days after as_of.

    Returns:
        list of {'date', 'external_acwr', 'internal_acwr', 'normalized_divergence'} for
        as_of .. as_of + horizon. normalized_divergence is None when the acute window is
        empty (undefined).
    """
    as_of = _as_date(as_of)
    loads, trimps = {}, {}
    for row_date, load, trimp in daily_rows:
        d = _as_date(row_date)
        if d > as_of:
            continue
        loads[d] = loads.get(d, 0.0) + (load or 0.0)
        trimps[d] = trimps.get(d, 0.0) + (trimp or 0.0)

    if scenario['kind'] not in ('rest', 'easy'):
        raise ValueError(f"unknown scenario: {scenario['kind']}")

    path = []
    for i in range(horizon + 1):
        day = as_of + timedelta(days=i)
        if i > 0 and scenario['kind'] == 'easy':
            loads[day] = scenario['load']
            trimps[day] = scenario['load'] * scenario['trimp_per_load']
        external, internal = _acwr_on(day, loads, trimps, method)
        path.append({
            'date': day,
            'external_acwr': round(external, 3),
            'internal_acwr': round(internal, 3),
            'normalized_divergence': UnifiedMetricsService._calculate_normalized_divergence(external, internal),
        })
    return path
