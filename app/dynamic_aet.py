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
from dataclasses import dataclass

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


def get_effective_aet(user_id):
    """Integration wrapper: gather baseline + readiness + per-athlete params and compute
    today's effective AeT for a user.

    Baseline AeT = get_user_hr_thresholds(user_id)['vt1_bpm'] (already measured-AeT-aware
    via the <=42d freshness override, else formula VT1). Returns the compute_effective_aet
    dict, or None if HR thresholds are unavailable.

    Phase 0: dark — not yet wired into any prompt or load path.
    """
    from llm_recommendations_module import get_user_hr_thresholds
    from readiness_engine import get_ans_readiness
    from db_utils import get_athlete_model

    hr = get_user_hr_thresholds(user_id)
    if not hr or hr.get('vt1_bpm') is None:
        return None

    zones = hr.get('zones') or {}
    z1z2_floor = (zones.get('zone2') or {}).get('min')

    readiness = get_ans_readiness(user_id)
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
