"""
Lactate Step Test Engine — LT1 (Aerobic Threshold) detection.

Pure computation module. No database or Flask dependencies.
Called by strava_app.py endpoints after collecting the manually-entered step table.

This is a CATEGORY-1 AUTHORITATIVE COMPUTATION (see .claude/rules/llm-determinism.md):
LT1 / baseline / aet_bpm / validity are computed deterministically here and injected
into the LLM prompt as stated fact. The model NEVER re-derives the threshold.

v1 analyzer = "first sustained rise":
    LT1 = first work stage S where
        lactate[S]   >= baseline + LT1_RISE_THRESHOLD_MMOL
    AND lactate[S+1] >= lactate[S]          (two-stage rule — beats ~±0.3 mmol meter noise)
    baseline = running minimum lactate over the established lower plateau.
    aet_bpm  = LT1_bpm = HR at stage S.

Dmax / modified-Dmax (more precise) and an LT2 detector (for the future LT1+LT2 ramp)
are DEFERRED. The function is kept pluggable so they can be added without reworking
storage: the full curve is persisted as JSONB and re-analysis stays a pure function.
"""

import logging

logger = logging.getLogger(__name__)

# Documented constant. The "two consecutive stages" rule is what defends against
# portable-meter noise (~±0.2–0.3 mmol); without it a single 0.3 bump could be noise.
# Flagged to revisit if field tests show it is too sensitive/insensitive (spec §6).
LT1_RISE_THRESHOLD_MMOL = 0.3


def analyze_lactate_step_test(
    stages: list,
    baseline_lactate: float = None,
    rise_threshold: float = LT1_RISE_THRESHOLD_MMOL,
) -> dict:
    """Detect LT1 (AeT) from a lactate step table.

    Args:
        stages: ordered list of dicts, one per work stage, each with:
                  stage   (int, 1-based; optional — order is what matters),
                  grade   (float, % incline),
                  hr      (number, steady-state bpm at end of stage),
                  lactate (number, mmol/L at end of stage).
        baseline_lactate: optional warm-up baseline sample (mmol/L) taken at the end
                  of the warm-up. If provided it participates in the running minimum,
                  anchoring the "rise" to a clean low reading (spec §3).
        rise_threshold: mmol rise above baseline that marks LT1 (default 0.3).

    Returns:
        On success:
            valid (True), lt1_bpm, lt1_grade, lt1_stage, baseline_lactate,
            peak_lactate, rise_threshold_mmol, analyzer_method, interpretation
        On failure:
            valid (False), error (str)  — never invent an AeT (category-2 guard,
            mirrors the drift test's invalid-result handling).
    """
    if not stages or not isinstance(stages, list):
        return {"valid": False, "error": "No step data provided."}

    # Normalise + validate each stage. Require HR and lactate; grade is optional.
    clean = []
    for i, s in enumerate(stages):
        try:
            hr = float(s.get("hr")) if s.get("hr") is not None else None
            lac = float(s.get("lactate")) if s.get("lactate") is not None else None
        except (TypeError, ValueError):
            return {"valid": False, "error": f"Stage {i + 1} has non-numeric HR or lactate."}
        if hr is None or lac is None:
            return {"valid": False, "error": f"Stage {i + 1} is missing HR or lactate."}
        if hr <= 30 or lac < 0:
            return {"valid": False, "error": f"Stage {i + 1} has an implausible HR or lactate value."}
        grade = None
        if s.get("grade") is not None:
            try:
                grade = float(s.get("grade"))
            except (TypeError, ValueError):
                return {"valid": False, "error": f"Stage {i + 1} has a non-numeric grade."}
        clean.append({"stage": s.get("stage", i + 1), "grade": grade, "hr": hr, "lactate": lac})

    # Need at least two stages so the two-stage confirmation can ever fire.
    if len(clean) < 2:
        return {
            "valid": False,
            "error": "Need at least two stages to confirm a sustained rise. "
                     "Add more stages and retest.",
        }

    # Establish the baseline plateau. The warm-up sample (if given) seeds the running
    # minimum so it cannot be undercut by a noisy early stage.
    valid_baseline = None
    if baseline_lactate is not None:
        try:
            vb = float(baseline_lactate)
            if vb >= 0:
                valid_baseline = vb
        except (TypeError, ValueError):
            return {"valid": False, "error": "Baseline lactate is non-numeric."}

    peak_lactate = max(c["lactate"] for c in clean)

    # Running minimum of lactate over everything BEFORE the candidate stage (the
    # established lower plateau). LT1 is the first rise of >= threshold above it that
    # the next stage confirms.
    running_min = valid_baseline
    for idx in range(len(clean)):
        cur = clean[idx]
        # baseline against which this stage's rise is judged = lowest reading seen so far
        baseline_prior = running_min if running_min is not None else cur["lactate"]

        is_rise = (running_min is not None) and (cur["lactate"] >= baseline_prior + rise_threshold)
        confirmed = (idx + 1 < len(clean)) and (clean[idx + 1]["lactate"] >= cur["lactate"])

        if is_rise and confirmed:
            return {
                "valid": True,
                "lt1_bpm": round(cur["hr"], 0),
                "lt1_grade": cur["grade"],
                "lt1_stage": cur["stage"],
                "baseline_lactate": round(baseline_prior, 2),
                "peak_lactate": round(peak_lactate, 2),
                "rise_threshold_mmol": rise_threshold,
                "analyzer_method": "first_sustained_rise",
                "interpretation": _interpret_lt1(cur, baseline_prior, peak_lactate, rise_threshold),
            }

        # update running minimum AFTER judging this stage so a stage can't be its own baseline
        if running_min is None or cur["lactate"] < running_min:
            running_min = cur["lactate"]

    # No sustained rise captured → invalid (never invent an AeT).
    return {
        "valid": False,
        "error": (
            f"No sustained lactate rise of +{rise_threshold} mmol over baseline was "
            "captured (or it appeared only at the final stage, where it can't be "
            "confirmed). The test likely stayed below LT1 — retest starting at a "
            "higher grade, or add stages until a confirmed rise appears."
        ),
        "baseline_lactate": round(running_min, 2) if running_min is not None else None,
        "peak_lactate": round(peak_lactate, 2),
    }


def _interpret_lt1(stage: dict, baseline: float, peak: float, rise_threshold: float) -> str:
    """Human-readable interpretation. Surfaces the meter-noise caveat (spec §4)."""
    grade_txt = f" at {stage['grade']:.1f}% grade" if stage.get("grade") is not None else ""
    caveat = ""
    if peak > 3.5:
        caveat = (
            " Note: peak lactate exceeded ~3 mmol — the test ran warmer than a light "
            "LT1-only assessment. The LT1 estimate stands, but keep future tests lighter."
        )
    return (
        f"LT1 (aerobic threshold) detected at {stage['hr']:.0f} bpm{grade_txt} — "
        f"the first stage where lactate rose +{rise_threshold} mmol above the "
        f"{baseline:.1f} mmol baseline and the next stage confirmed it. "
        f"Your Zone 2 ceiling (AeT) is approximately {stage['hr']:.0f} bpm. "
        f"Treat this as protocol-/trend-based, not single-decimal precise — portable "
        f"meters carry ~±0.2–0.3 mmol noise." + caveat
    )
