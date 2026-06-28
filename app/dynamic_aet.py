"""
dynamic_aet.py — Effective (dynamic) Aerobic Threshold.

Treats AeT as dynamic: it shifts day to day with autonomic readiness. A baseline AeT
(measured drift test when fresh, else formula VT1) is modulated by an HRV-derived offset
to produce today's *effective* AeT, which downstream (a) moves the Z2/Z3 classification
boundary (Effect A) and (b) feeds a dynamic internal-load metric (Effect B).

This module is the category-1 single source of truth for that value: deterministic,
injected into prompts as fact, never re-derived by the LLM (see
.claude/rules/llm-determinism.md). Design decisions (2026-06-27 session,
docs/design_dynamic_aet_2026-06-27.md):

  - Only the Z2/Z3 (VT1) boundary moves. VT2 and all other boundaries are anchored — we
    have a daily proxy for the aerobic threshold (HRV) but none for the lactate threshold,
    so rescaling all zones would fabricate unmeasured VT2 movement. (decision d)
  - Offset shape is continuous, asymmetric, dead-banded, clamped. Downward gain exceeds
    upward gain as a SAFETY property: a suppressed autonomic state should lower the aerobic
    ceiling more readily than a good reading raises it. (decision c)
  - Parasympathetic-overdrive / overreaching states must never RAISE AeT, regardless of
    raw hrv_z (the high-HRV + low-RHR "deep hole" inversion). Hard guard, not a tunable.
  - Missing/stale HRV: reuse readiness_engine's 7-day-acute hrv_z (already smooths single
    gaps); UNKNOWN -> offset 0; a staleness ceiling decays the offset toward 0; the
    fallback is surfaced as an honest fact rather than implying a live measurement.

The offset parameters are personalized per athlete in athlete_models and seeded with the
DEFAULT_* constants below; calibration is deferred to drift-test anchoring. The constants
are documented defaults / NULL-column fallbacks, not magic numbers buried in logic.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Population-default offset parameters (mirror the athlete_models column defaults).
DEFAULT_DEADBAND = 0.5        # sigma; no shift within +/- this z-score band
DEFAULT_SLOPE_NEG = 4.0       # bpm per sigma below the dead-band (downward)
DEFAULT_SLOPE_POS = 1.5       # bpm per sigma above the dead-band (upward, gentler)
DEFAULT_CAP_NEG = -8.0        # max downward offset (bpm)
DEFAULT_CAP_POS = 3.0         # max upward offset (bpm)
DEFAULT_STALENESS_DAYS = 3    # latest HRV older than this -> decay offset toward 0

# Readiness states that forbid RAISING AeT regardless of raw hrv_z (parasympathetic-
# overdrive inversion). Hard guard — see readiness_engine.classify_readiness_state.
_NO_RAISE_STATES = frozenset({'RED', 'YELLOW_PARASYMPATHETIC'})


@dataclass
class OffsetParams:
    """Per-athlete offset function parameters (seeded with population defaults)."""
    deadband: float = DEFAULT_DEADBAND
    slope_neg: float = DEFAULT_SLOPE_NEG
    slope_pos: float = DEFAULT_SLOPE_POS
    cap_neg: float = DEFAULT_CAP_NEG
    cap_pos: float = DEFAULT_CAP_POS
    staleness_days: int = DEFAULT_STALENESS_DAYS

    @classmethod
    def from_athlete_model(cls, am):
        """Build from an athlete_models dict, falling back to defaults for NULL/missing."""
        if not am:
            return cls()

        def _v(key, default):
            v = am.get(key)
            return default if v is None else v

        return cls(
            deadband=float(_v('aet_offset_deadband', DEFAULT_DEADBAND)),
            slope_neg=float(_v('aet_offset_slope_neg', DEFAULT_SLOPE_NEG)),
            slope_pos=float(_v('aet_offset_slope_pos', DEFAULT_SLOPE_POS)),
            cap_neg=float(_v('aet_offset_cap_neg', DEFAULT_CAP_NEG)),
            cap_pos=float(_v('aet_offset_cap_pos', DEFAULT_CAP_POS)),
            staleness_days=int(_v('aet_offset_staleness_days', DEFAULT_STALENESS_DAYS)),
        )


def staleness_factor(days_since_hrv, staleness_days):
    """Linear decay weight: 1.0 up to staleness_days, ramping to 0.0 at 2*staleness_days.

    days_since_hrv is the age of the most recent HRV reading feeding the acute window.
    None (no reading at all) -> 0.0.
    """
    if days_since_hrv is None:
        return 0.0
    if days_since_hrv <= staleness_days:
        return 1.0
    over = days_since_hrv - staleness_days
    return max(0.0, 1.0 - over / float(staleness_days))


def compute_aet_offset(hrv_z, state, days_since_hrv, params=None):
    """Pure: HRV z-score + readiness state + data age -> AeT offset in bpm (float).

    - hrv_z is None (UNKNOWN baseline)        -> 0.0
    - within +/- deadband                     -> 0.0
    - below the dead-band: slope_neg ramp, floored at cap_neg
    - above the dead-band: slope_pos ramp, capped at cap_pos
    - RED / YELLOW_PARASYMPATHETIC states      -> clamped to <= 0 (never raise AeT)
    - stale HRV                                -> decayed toward 0
    """
    params = params or OffsetParams()

    if hrv_z is None:
        return 0.0

    if abs(hrv_z) < params.deadband:
        offset = 0.0
    elif hrv_z < 0:
        offset = max(params.slope_neg * (hrv_z + params.deadband), params.cap_neg)
    else:
        offset = min(params.slope_pos * (hrv_z - params.deadband), params.cap_pos)

    # Hard safety guard: parasympathetic overdrive / overreaching must never raise AeT.
    if state in _NO_RAISE_STATES:
        offset = min(offset, 0.0)

    return offset * staleness_factor(days_since_hrv, params.staleness_days)


def compute_effective_aet(baseline_aet, hrv_z, state, days_since_hrv,
                          vt2=None, z1z2_floor=None, params=None):
    """Pure: baseline AeT + readiness offset -> today's effective AeT (int), with clamps.

    Only the VT1 / Z2 ceiling moves; the caller leaves VT2 and other boundaries fixed.
    Sanity clamps keep the effective AeT strictly between the Z1/Z2 floor and VT2.

    Returns dict: effective_aet, baseline_aet, offset, state, fallback_reason.
    fallback_reason is 'no_hrv_baseline' | 'hrv_stale' | None — surfaced honestly in the
    Rx rather than implying a live measurement.
    """
    params = params or OffsetParams()
    offset = compute_aet_offset(hrv_z, state, days_since_hrv, params)

    if hrv_z is None:
        fallback_reason = 'no_hrv_baseline'
    elif staleness_factor(days_since_hrv, params.staleness_days) < 1.0:
        fallback_reason = 'hrv_stale'
    else:
        fallback_reason = None

    effective = baseline_aet + offset

    # Category-1 sanity clamps: never cross the anchored boundaries.
    if z1z2_floor is not None:
        effective = max(effective, z1z2_floor + 1)
    if vt2 is not None:
        effective = min(effective, vt2 - 1)

    return {
        'effective_aet': int(round(effective)),
        'baseline_aet': int(round(baseline_aet)),
        'offset': round(offset, 1),
        'state': state,
        'fallback_reason': fallback_reason,
    }


def calculate_dynamic_internal_acwr(user_id, activity_date):
    """Parallel internal ACWR from trimp_dynamic (Effect B, dual-track) — DARK.

    Mirrors update_moving_averages_standard exactly: 7d and 28d windows ending at
    activity_date, summed then divided by 7 and 28. The ratio is the dynamic internal ACWR.
    Applying the SAME window logic to BOTH windows is the consistency requirement — never
    mix methods across acute/chronic. Not fed to the live divergence until cutover.

    Caveat (resolve at B-validate): activities without an HR stream have NULL trimp_dynamic
    and contribute 0 here, which can deflate the dynamic load. See dynamic_acwr_cutover_ready.

    Returns dict or None on error.
    """
    from db_utils import execute_query
    from datetime import datetime, timedelta
    try:
        d = activity_date if hasattr(activity_date, 'year') else datetime.strptime(activity_date, '%Y-%m-%d').date()
        ds = d.strftime('%Y-%m-%d')
        seven = (d - timedelta(days=6)).strftime('%Y-%m-%d')
        twentyeight = (d - timedelta(days=27)).strftime('%Y-%m-%d')

        def _avg(start, n):
            r = execute_query(
                "SELECT COALESCE(SUM(trimp_dynamic), 0) AS s FROM activities "
                "WHERE user_id = %s AND date BETWEEN %s AND %s",
                (user_id, start, ds), fetch=True
            )
            return float(r[0]['s'] or 0) / n

        a7 = _avg(seven, 7.0)
        c28 = _avg(twentyeight, 28.0)
        ratio = round(a7 / c28, 2) if c28 > 0 else 0.0
        return {
            'seven_day_avg_trimp_dynamic': round(a7, 2),
            'twentyeight_day_avg_trimp_dynamic': round(c28, 2),
            'internal_acwr_dynamic': ratio,
        }
    except Exception as e:
        logger.warning(f"dynamic internal ACWR failed for user {user_id} @ {activity_date}: {e}")
        return None


def dynamic_divergence(external_acwr, internal_acwr_dynamic):
    """Normalized divergence using the dynamic internal ACWR.

    Identical formula to UnifiedMetricsService._calculate_normalized_divergence so the
    cutover is a pure input swap: (external - internal) / avg. Positive = external exceeds
    internal (recovery/detraining); negative = hidden internal stress (overtraining risk).
    """
    if external_acwr is None or internal_acwr_dynamic is None:
        return None
    if external_acwr == 0 and internal_acwr_dynamic == 0:
        return 0.0
    avg = (external_acwr + internal_acwr_dynamic) / 2
    if avg == 0:
        return None
    return round((external_acwr - internal_acwr_dynamic) / avg, 4)


def dynamic_acwr_cutover_ready(user_id, as_of_date=None):
    """Gate for switching live divergence to the dynamic track.

    True only when the trailing 28-day chronic window is fully represented by the dynamic
    method — so the cutover never mixes Banister and Edwards across windows:
      (a) dynamic coverage spans >= 28 days (earliest trimp_dynamic is old enough), AND
      (b) no stream-bearing activity in the last 28 days is still missing trimp_dynamic.
    """
    from db_utils import execute_query
    from timezone_utils import get_app_current_date
    from datetime import timedelta
    try:
        ref = as_of_date or get_app_current_date()
        ref_s = ref.strftime('%Y-%m-%d')
        window_start = (ref - timedelta(days=27)).strftime('%Y-%m-%d')

        earliest = execute_query(
            "SELECT MIN(date) AS m FROM activities WHERE user_id = %s AND trimp_dynamic IS NOT NULL",
            (user_id,), fetch=True
        )
        m = earliest[0]['m'] if earliest else None
        if not m:
            return False
        if (ref - m).days < 28:
            return False

        # Stream-bearing activities in the window that haven't been dynamic-scored yet.
        gap = execute_query(
            """SELECT COUNT(*) AS n
               FROM activities a
               JOIN hr_streams h ON h.activity_id = a.activity_id
               WHERE a.user_id = %s AND a.date BETWEEN %s AND %s
                 AND a.activity_id > 0 AND a.trimp_dynamic IS NULL""",
            (user_id, window_start, ref_s), fetch=True
        )
        return int(gap[0]['n'] or 0) == 0
    except Exception as e:
        logger.warning(f"cutover-ready check failed for user {user_id}: {e}")
        return False


def format_effective_aet_block(eff):
    """Authoritative prompt block stating today's effective AeT (category-1 fact).

    Parallel to format_metric_verdict_block — the model uses this value, never re-derives
    it. Honest about the fallback path so the prose never implies a live measurement that
    isn't there. Returns '' when eff is None.
    """
    if not eff:
        return ''
    baseline = eff['baseline_aet']
    effective = eff['effective_aet']
    offset = eff.get('offset') or 0
    fb = eff.get('fallback_reason')

    lines = [
        "### TODAY'S EFFECTIVE AeT (authoritative — computed server-side from overnight HRV; use this value, do NOT re-derive)",
        f"Baseline AeT: {baseline} bpm (last calibrated value — fresh drift test > lab > formula).",
    ]
    if fb == 'no_hrv_baseline':
        lines.append(f"Effective AeT today: {effective} bpm — HRV baseline unavailable, so AeT is held at baseline (no autonomic adjustment).")
    elif fb == 'hrv_stale':
        lines.append(f"Effective AeT today: {effective} bpm — recent HRV is stale, so the autonomic adjustment is reduced toward baseline.")
    elif offset != 0:
        direction = 'lowered' if offset < 0 else 'raised'
        lines.append(f"Effective AeT today: {effective} bpm — {direction} {abs(offset):.0f} bpm from baseline by overnight HRV readiness (Oura rMSSD).")
    else:
        lines.append(f"Effective AeT today: {effective} bpm — overnight HRV is near baseline, so no adjustment today.")
    lines.append(f"Use {effective} bpm as today's Zone 2 ceiling for all easy/aerobic HR targets. HR above {effective} bpm is Zone 3 (moderate), not easy.")
    return "\n".join(lines) + "\n"


def get_effective_aet(user_id, as_of_date=None):
    """Integration wrapper: gather baseline + readiness + per-athlete params and compute
    a user's effective AeT, for today or — when as_of_date is given — as it was on a past
    date (the autopsy anchor: classify a completed session against the AeT that applied on
    its own date).

    Baseline AeT = get_user_hr_thresholds(user_id)['vt1_bpm'] (precedence: fresh drift test
    -> custom lab AeT -> formula VT1). NOTE: the baseline anchor is always the *current*
    calibrated value; only the HRV offset is reconstructed historically. The offset models
    that day's autonomic deviation relative to the athlete's established AeT — reconstructing
    a historical baseline (e.g. past drift-test freshness) would be over-engineering.

    Returns the compute_effective_aet dict, or None if HR thresholds are unavailable.
    """
    from llm_recommendations_module import get_user_hr_thresholds
    from readiness_engine import get_ans_readiness
    from db_utils import get_athlete_model

    hr = get_user_hr_thresholds(user_id)
    if not hr or hr.get('vt1_bpm') is None:
        return None

    zones = hr.get('zones') or {}
    z1z2_floor = (zones.get('zone2') or {}).get('min')

    readiness = get_ans_readiness(user_id, as_of_date=as_of_date)
    params = OffsetParams.from_athlete_model(get_athlete_model(user_id))

    return compute_effective_aet(
        baseline_aet=hr['vt1_bpm'],
        hrv_z=readiness.get('hrv_z'),
        state=readiness.get('state'),
        days_since_hrv=readiness.get('days_since_hrv'),
        vt2=hr.get('vt2_bpm'),
        z1z2_floor=z1z2_floor,
        params=params,
    )
