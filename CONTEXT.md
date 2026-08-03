# Your Training Monkey (YTM)

AI coaching app for trail/endurance runners. Flask (Python) backend + React/TypeScript frontend, PostgreSQL. Turns Strava activity data and subjective journal input into a daily training recommendation, personalized over time by a per-user learned Athlete Model.

## Load & Risk Metrics

**ACWR (Acute:Chronic Workload Ratio)**:
7-day rolling average load ÷ 28-day rolling average load. Computed separately for external and internal load. `<0.8` undertraining, `0.8–1.3` optimal, `1.3–1.5` high risk, `>1.5` very high risk.
- **External ACWR** (`acute_chronic_ratio`): built from distance + elevation.
- **Internal ACWR** (`trimp_acute_chronic_ratio`): built from TRIMP.

**Normalized Divergence** (`normalized_divergence`):
YTM's flagship metric: `(External ACWR − Internal ACWR) / avg(External ACWR, Internal ACWR)`. Measures whether external effort and internal (cardiac) cost are moving together. `< −0.15` high overtraining risk, `+0.05` to `+0.15` efficient, `> +0.15` potential undertraining.
_Avoid_: "Divergence Analysis" (marketing name for the same metric), `norm_divergence` (diagram-only abbreviation, not a real field).

**TRIMP (Training Impulse)**:
Banister-formula internal load: `duration × HRR × 0.64e^(k×HRR)`. The primary, system-of-record internal-load metric.
_Avoid_: **Dynamic TRIMP** (`trimp_dynamic`) is a *different*, Edwards-formula, zone-summated metric computed in parallel. It only becomes system-of-record after a feature-flag cutover — until then, "TRIMP" means Banister TRIMP.

**Elevation Load Miles / Total Load Miles**:
`elevation_gain_feet / 750`, added to `distance_miles` for Total Load Miles. This is what production code (`strava_training_load.py`, the race-readiness route, `trail_specifics.md`) actually computes everywhere.
⚠ `app/Training_Metrics_Reference_Guide.md` (line 127) states the divisor as `/1000` — that line is stale/wrong relative to every live code path. See Open Questions.

**RPE**: session-level 1–10 perceived exertion (`rpe_score`). Whole-workout gestalt, not peak or average.

**Pain Score** (`pain_percentage`): 0–100, % of workout time the athlete was aware of pain. Doc calls it "Pain Score"; code/DB/UI call it `pain_percentage` — treat as the same term, `pain_percentage` is the identifier form.

**HR Zones 1–5**: personalized via Karvonen or % method. Zone 2 = Aerobic Base (primary training zone). Zone 3 = "**the black hole**" — moderate-hard, physiologically unproductive if overused; this is a coaching-prose term for Zone 3, not a separate field.

**Workout Classification**:
⚠ Two classifiers exist with different vocabularies over the same HR-zone data — `classify_workout_by_hr_zones()` returns Easy/Moderate/Hard/VO2Max (4-way); `_classify_activity_intensity()` (used only for pattern-flag checks) returns Hard/Easy-Recovery/Unknown (3-way). See Open Questions.

## Aerobic Threshold (AeT) System

**AeT (Aerobic Threshold)**: the Zone 2 ceiling, treated as dynamic day-to-day rather than fixed. `effective_AeT = baseline ± daily offset`, offset driven by HRV-based readiness, asymmetric and clamped. Computed server-side in `dynamic_aet.py` — never re-derived by the LLM.
- **VT1** = the Zone 2/3 boundary = AeT (operational name for VT1 specifically).
- **VT2** = lactate threshold; fixed, no daily proxy.

## Journal & Subjective Wellness

**Journal** (`journal_entries`): daily subjective input — `energy_level`, `rpe_score`, `pain_percentage`, `sleep_quality`, `morning_soreness`, `hrv_value`, `resting_hr`, free-text `notes`. All fields live on one table; there is no separate `readiness` table (confirmed against schema — `COACHING_FRAMEWORK_GAPS.md`'s reference to a "readiness table" is stale, not a real second location).

**Readiness** — three unrelated concepts share this word; pick the specific one:
- **Readiness State** (ANS/autonomic): `get_ans_readiness()` / `classify_readiness_state()` in `readiness_engine.py` → `GREEN` / `YELLOW_SYMPATHETIC` / `YELLOW_PARASYMPATHETIC` ("Deep Hole") / `RED` / `UNKNOWN`, from HRV/RHR z-scores vs. personal baseline. This is the canonical engine — `coaching_context/readiness.md` is written directly against its state names and thresholds, and it's what the user-facing readiness API returns (`readiness_state`, `readiness_narrative`).
  _Avoid_: `compute_readiness_state()` (in `llm_recommendations_module.py`) — a separate, older, coarser classifier that only returns `GREEN`/`AMBER`/`RED` using its own independent threshold logic (not the same rules as the canonical engine). It is legitimately still used for two fields it alone computes — `confidence` and `component_flags`, consumed by the readiness API endpoint — but its `state`/`narrative` output must never be shown to the LLM or treated as the readiness state; that's the canonical engine's job.
- **Morning Check-in**: the UI card that writes `sleep_quality` + `morning_soreness` to `journal_entries`.
- **Race Readiness Score**: unrelated — see Race & Goal Planning below.
_Avoid_: "readiness" alone — always qualify which of the three you mean.

**Pattern Flags** (`analyze_pattern_flags()`): `red_flags` / `positive_patterns` / `warnings`. Named flags agree tightly with the reference guide (e.g. Chronic ACWR Elevation, Divergence Drift) — a clean example of doc/code agreement.

## Coaching Engine

**Assessment Category** (`derive_assessment_category()`): the server-computed daily verdict — `mandatory_rest`, `overtraining_risk`, `high_acwr_risk`, `recovery_needed`, `undertraining_opportunity`, `normal_progression`. Authoritative fact, injected into prompts, never re-derived by the LLM.
_Avoid_: conflating this with **Divergence Classification** (the reference guide's Balanced/Efficient/Moderate Risk/etc. labels) — that vocabulary describes what a divergence *value* means; Assessment Category describes what *action* to take, combining divergence with ACWR and days-since-rest. Related, not interchangeable.

**Safety Floor** (`floor_category` / `enforce_safety_floor()`): the non-negotiable action mandate derived 1:1 from Assessment Category (e.g. `mandatory_rest` → `rest`). Enforced against the LLM's output after generation; violations trigger one regeneration, then a hardcoded fallback. Deterministic, never trust-based.

**The decision pipeline** (canonical name for each layer, top to bottom):
1. **Assessment Category** — server classification (`mandatory_rest`, etc.)
2. **Decision Action** (`decision.action`) — mandated LLM output enum: `rest` / `reduce` / `train_allowed`
3. **Today's Decision** (`todays_decision`, from DB column `daily_recommendation`) — the prose text shown to the user, UI-labeled "AI Training Decision"

_Avoid_: using "decision" and "recommendation" interchangeably across these three layers — pick the layer name above instead.

**Prescribed** (workout structure) vs. **Recommendation/Decision** (daily coaching verdict): "prescribed"/"prescription" language is reserved for fixed **Canonical Workout Library** protocols (Norwegian 4×4, Lactate Shuttle/Over-Unders, Strides — do not substitute or invent variants). It does not describe the daily coaching output. No "Rx" abbreviation is used anywhere — the brand voice deliberately avoids clinical framing.

**Daily Recommendation** (`llm_recommendations` table): `daily_recommendation` (prose) + `structured_output` (JSONB: assessment, divergence, risk, context). Two parallel, non-unified generators exist — `generate_recommendations()` (standard) and `generate_recommendations_agentic()` (tool-calling, feature-flag gated) — parity between them is an acknowledged open gap, not yet resolved.

**Weekly Program** (`build_weekly_program_prompt()` / `weekly_programs` table): `strategic_summary`, `daily_program`, `weekly_synthesis`, `deviation_log`.

**Weekly Synthesis** (`generate_weekly_synthesis()`): retrospective, runs after program generation, reflects only the *prior* week. This is an **internal prompt-injection artifact** (feeds next week's program) — it is not currently user-facing.
⚠ `COACHING_FRAMEWORK_GAPS.md` proposes an "End-of-week synthesis" as a *missing* user-facing feature. It may be asking to expose this existing internal artifact rather than build a new one. See Open Questions.

**Autopsy** (`generate_enhanced_autopsy()` → `ai_autopsies` table): post-activity analysis producing `alignment_score` (0–10, how well behavior matched the plan) and `deviation_reason`. Must run before `update_athlete_model()` — reversing this order silently breaks threshold calibration.
- **Fallback autopsy**: `is_fallback: True`, hardcoded `alignment_score = 6`. Must be excluded from `update_athlete_model()` or it pollutes `avg_lifetime_alignment`.

**Athlete Model** (`athlete_models` table): the persistent per-user learned model — `typical_divergence_low`, `divergence_injury_threshold`, `avg_lifetime_alignment`, `recent_alignment_trend`, `total_autopsies`, `rpe_calibration_offset`. Below `total_autopsies ≥ 3`, the model is treated as not-yet-warmed-up (a "LEARNING" state is injected instead of the model).

**Confidence** — four distinct, non-interchangeable concepts share this word. Canonical names:
- **Calibration Confidence** (`acwr_sweet_spot_confidence`): legacy per-autopsy counter. Docs record it as functionally replaced by `div_low_n`/`threshold_n` for threshold overrides — but it's still live as the gate for the Race Readiness feature. Status is genuinely mixed; see **ACWR Sweet Spot** below.
- **Model Warm-up Gate** (`total_autopsies ≥ 3`): boolean-ish gate on whether the full Athlete Model is injected into prompts at all.
- **Model Completeness Score** (`model_confidence_pct`): newer 9-component composite (profile, HR calibration, journal power ×2, aerobic assessment, etc.), 0–100%. A data-completeness/onboarding-quality score, unrelated to the above.
- **Baseline Coverage Confidence** (the `confidence` field inside `compute_readiness_state()`): HRV/RHR baseline data-sufficiency score that can downgrade RED→AMBER→GREEN when low.
_Avoid_: "confidence" alone. The product roadmap itself flags this ambiguity as unresolved ("is confidence scoring simply an average of autopsies and journal entries") — the four terms above are the intended resolution; confirm with the user before treating it as settled.

## Race & Goal Planning

**Race Goal**: `race_goals` table, Priority A/B/C (A = primary target).

**Training Stage** (`_calculate_training_stage()`): `base` (12+ wks out) → `build` → `specificity` → `taper` → `peak` → `recovery`. Matches the Canonical Workout Library's phase table exactly — a clean positive example of doc/code agreement.

**Race Readiness Score** (`/api/coach/race-readiness`): projects whether chronic load can reach race-peak load-miles before taper. Statuses: `on_track` / `not_achievable` / `already_ready`. Unrelated to Readiness State or Morning Check-in above — see the Readiness disambiguation.

**ACWR Sweet Spot** — status: **partially retired**, not fully removed:
- Dead as a threshold-personalization mechanism (explicitly removed from `apply_athlete_model_to_thresholds()`; architecture is divergence-only now).
- Alive as a stored, actively-incrementing value (`acwr_sweet_spot_confidence`, aka Calibration Confidence above) still consumed by the Race Readiness gate.
- Still marketed in the brand framework doc as a live UI concept ("Sweet Spot," Success Green) and listed in `COACHING_FRAMEWORK_GAPS.md` as a planned user-facing feature.
See Open Questions.

## Coaching Context Library

`app/coaching_context/*.md` — state-gated files injected directly into LLM prompts as ground truth (not application code, not documentation in the normal sense). Own writing rules (imperative, no citations) and its own conflict-priority protocol: `readiness.md` overrides all other context files when injected.

---

## Open Questions (raised during initial glossary pass, 2026-08-02 — not yet resolved with the user)

1. ~~**Readiness vocabulary drift, live-output risk**~~ — RESOLVED 2026-08-03. Root cause was not a missing state in the code; `readiness_engine.py` already computed the full `YELLOW_SYMPATHETIC`/`YELLOW_PARASYMPATHETIC` vocabulary correctly and matches `readiness.md` exactly. The bug was that both LLM-facing prompt builders (`llm_recommendations_module.py`, standard and agentic paths) were displaying the *other*, legacy classifier's output (`compute_readiness_state()` → GREEN/AMBER/RED) to the model instead of the canonical engine's — even though the standard path's own context-gating already correctly used the canonical engine, and the frontend API endpoint already correctly used it too. The agentic path additionally gated `readiness.md`'s injection on the wrong (legacy) state. Fixed by sourcing `state`/`narrative` from `_ans` (`get_ans_readiness()`) at all 3 prompt-facing call sites and removing the now-dead `compute_readiness_state()` calls there; the function itself stays, still legitimately used by the `strava_app.py` readiness endpoint for `confidence`/`component_flags`.
2. **Elevation Load Miles divisor**: `Training_Metrics_Reference_Guide.md` says `/1000`; all four live code paths say `/750`. The reference guide is the stated source of truth for coaching thresholds — this line appears to just be wrong and worth fixing there.
3. **ACWR Sweet Spot**: is this being actively revived as a user-facing feature (per the gaps doc and brand copy), or should the remaining live plumbing (`acwr_sweet_spot_confidence`) be finished being retired? Current state is neither.
4. **"End-of-week synthesis"**: is the gaps-doc proposal actually "expose the existing `generate_weekly_synthesis()` output to users," or a genuinely new feature? Worth clarifying before someone builds a duplicate.
5. **Two workout-intensity classifiers** (Easy/Moderate/Hard/VO2Max vs. Hard/Easy-Recovery/Unknown) — not confirmed as a live bug, but worth a direct look at whether they ever disagree on the same activity in a way that matters.
