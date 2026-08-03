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
`elevation_gain_feet / 750`, added to `distance_miles` for Total Load Miles. Confirmed as what every production code path computes (`strava_training_load.py` since at least Sept 2025, the race-readiness route, `trail_specifics.md`). `Training_Metrics_Reference_Guide.md` previously stated `/1000` — corrected 2026-08-03 to match production; the origin of the 750 figure itself is still undocumented, flagged for a citation.

**RPE**: session-level 1–10 perceived exertion (`rpe_score`). Whole-workout gestalt, not peak or average.

**Pain Score** (`pain_percentage`): 0–100, % of workout time the athlete was aware of pain. Doc calls it "Pain Score"; code/DB/UI call it `pain_percentage` — treat as the same term, `pain_percentage` is the identifier form.

**HR Zones 1–5**: personalized via Karvonen or % method. Zone 2 = Aerobic Base (primary training zone). Zone 3 = "**the black hole**" — moderate-hard, physiologically unproductive if overused; this is a coaching-prose term for Zone 3, not a separate field.

**Workout Classification** (`workout_classification`, from `classify_workout_by_hr_zones()`): `Easy/Recovery` / `Moderate` / `Tempo/Threshold` / `Intervals/Hard` / `Unknown`. Injected directly into LLM prompts and shown to users as "(X intensity)". A second, single-activity classifier, `_classify_activity_intensity()` (`Easy/Recovery` / `Moderate` / `Hard` / `Unknown`), is used only inside `analyze_pattern_flags()`'s back-to-back-hard-day and minimum-easy-day checks — the coarser 3-way label there collapses `Tempo/Threshold` and `Intervals/Hard` into one `Hard` bucket, which is fine on its own. RESOLVED 2026-08-03: the two previously disagreed on Zone-2-dominant days (`classify_workout_by_hr_zones` called them `Moderate`, contradicting its own `primary_zone<=2` fallback branch, which already called the same data `Easy/Recovery`) — fixed by aligning the explicit Zone-2 branch with the project's own Zone 2 definition ("Aerobic Base... primary training zone") and with the other classifier.

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

**Weekly Synthesis** (`generate_weekly_synthesis()`): retrospective, dual-track (alignment + productive-work) narrative for the completed week, plus a composite score and athlete reflection field. Runs via the `/cron/weekly-synthesis` Saturday Cloud Scheduler job (manually regenerable via `/api/coach/weekly-synthesis/generate`) and **is fully user-facing** — the Coach page fetches it from `/api/coach/weekly-synthesis` and renders it via `WeeklySynthesisCard`/`WeeklyProgramDisplay.tsx`. Confirmed 2026-08-03 this was never just an internal artifact.

**Autopsy** (`generate_enhanced_autopsy()` → `ai_autopsies` table): post-activity analysis producing `alignment_score` (0–10, how well behavior matched the plan) and `deviation_reason`. Must run before `update_athlete_model()` — reversing this order silently breaks threshold calibration.
- **Fallback autopsy**: `is_fallback: True`, hardcoded `alignment_score = 6`. Must be excluded from `update_athlete_model()` or it pollutes `avg_lifetime_alignment`.

**Athlete Model** (`athlete_models` table): the persistent per-user learned model — `typical_divergence_low`, `divergence_injury_threshold`, `avg_lifetime_alignment`, `recent_alignment_trend`, `total_autopsies`, `rpe_calibration_offset`. Below `total_autopsies ≥ 3`, the model is treated as not-yet-warmed-up (a "LEARNING" state is injected instead of the model).

**Confidence** — three distinct, non-interchangeable concepts share this word (a fourth, `acwr_sweet_spot_confidence`, was removed 2026-08-03 — see **ACWR Sweet Spot** below). Canonical names:
- **Model Warm-up Gate** (`total_autopsies ≥ 3`): boolean-ish gate on whether the full Athlete Model is injected into prompts at all.
- **Model Completeness Score** (`model_confidence_pct`): newer 9-component composite (profile, HR calibration, journal power ×2, aerobic assessment, etc.), 0–100%. A data-completeness/onboarding-quality score, unrelated to the above.
- **Baseline Coverage Confidence** (the `confidence` field inside `compute_readiness_state()`): HRV/RHR baseline data-sufficiency score that can downgrade RED→AMBER→GREEN when low.
_Avoid_: "confidence" alone. The product roadmap itself flags this ambiguity as unresolved ("is confidence scoring simply an average of autopsies and journal entries") — the four terms above are the intended resolution; confirm with the user before treating it as settled.

## Race & Goal Planning

**Race Goal**: `race_goals` table, Priority A/B/C (A = primary target).

**Training Stage** (`_calculate_training_stage()`): `base` (12+ wks out) → `build` → `specificity` → `taper` → `peak` → `recovery`. Matches the Canonical Workout Library's phase table exactly — a clean positive example of doc/code agreement.

**Race Readiness Score** (`/api/coach/race-readiness`): projects whether chronic load can reach race-peak load-miles before taper. Statuses: `on_track` / `not_achievable` / `already_ready`. Unrelated to Readiness State or Morning Check-in above — see the Readiness disambiguation.

**ACWR Sweet Spot** — status as of 2026-08-03: **fully resolved.**
- `acwr_sweet_spot_low`/`acwr_sweet_spot_high` are dead — never computed by any code path (confirmed against the existing internal audit, `docs/architecture/coaching-pipeline-qc-audit.md` Finding 4-A), permanently frozen at their migration defaults (0.8/1.2) for every user. `acwr_high_risk` (the actual ACWR ceiling used everywhere, including Race Readiness) is **never personalized** in the current divergence-only framework — `apply_athlete_model_to_thresholds()` only overrides the two divergence thresholds, by design (see its docstring).
- `acwr_sweet_spot_confidence` — a per-autopsy counter that fed a `model_calibrated: true/false` badge on the Race Readiness card's ACWR ceiling tile — was removed 2026-08-03. It was diagnosed as meaningless by the project's own QC audit ("confidence in an undefined sweet spot") and there was no honest signal to replace it with, since the ceiling it claimed to describe is never personalized.
- Branding decided 2026-08-03: dropped "Sweet Spot" from `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md` (Success Green usage lists, blog topic list) — kept the unrelated "Our Sweet Spot: Professional-friendly with technical credibility" voice-tone line, which isn't about ACWR at all. Deliberately **left untouched** in `COACHING_FRAMEWORK_GAPS.md` (Tier 1 #2, the proposal to surface sweet spot low/high + confidence%) per instruction — that doc keeps the concept on record as a possible future build, just no longer marketed as live.

## Coaching Context Library

`app/coaching_context/*.md` — state-gated files injected directly into LLM prompts as ground truth (not application code, not documentation in the normal sense). Own writing rules (imperative, no citations) and its own conflict-priority protocol: `readiness.md` overrides all other context files when injected.

---

## Open Questions (raised during initial glossary pass, 2026-08-02 — not yet resolved with the user)

1. ~~**Readiness vocabulary drift, live-output risk**~~ — RESOLVED 2026-08-03. Root cause was not a missing state in the code; `readiness_engine.py` already computed the full `YELLOW_SYMPATHETIC`/`YELLOW_PARASYMPATHETIC` vocabulary correctly and matches `readiness.md` exactly. The bug was that both LLM-facing prompt builders (`llm_recommendations_module.py`, standard and agentic paths) were displaying the *other*, legacy classifier's output (`compute_readiness_state()` → GREEN/AMBER/RED) to the model instead of the canonical engine's — even though the standard path's own context-gating already correctly used the canonical engine, and the frontend API endpoint already correctly used it too. The agentic path additionally gated `readiness.md`'s injection on the wrong (legacy) state. Fixed by sourcing `state`/`narrative` from `_ans` (`get_ans_readiness()`) at all 3 prompt-facing call sites and removing the now-dead `compute_readiness_state()` calls there; the function itself stays, still legitimately used by the `strava_app.py` readiness endpoint for `confidence`/`component_flags`.
2. ~~**Elevation Load Miles divisor**~~ — RESOLVED 2026-08-03. `strava_training_load.py`'s `/750` traces back to at least Sept 2025 (`be2eb48`, comment "unchanged for safety" through later refactors) — the long-standing, multiply-cross-validated production value. `Training_Metrics_Reference_Guide.md`'s `/1000` was last touched in the March 2026 doc rewrite (`9de7c0cd`) but never reconciled against the code; nothing in the live system has used `/1000`. Corrected the doc to `/750` and removed its fabricated-sounding "research showing 100ft≈0.1mi" justification (no such citation exists anywhere else in the repo) rather than invent a new one for 750 — the actual empirical basis for 750 is still an open item. Did not touch the code: changing an 18-month-old live coaching formula on internal reasoning alone would be a real behavior change to real users' recommendations, not a docs fix — that's Rob's call, and there's no evidence `/1000` was ever the intended value to revert to.
3. ~~**ACWR Sweet Spot**~~ — RESOLVED 2026-08-03. Dead/misleading code-level plumbing removed (`acwr_sweet_spot_confidence`, the stale `model_calibrated` badge on the Race Readiness card). Branding decided: dropped "Sweet Spot" from `docs/branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`; deliberately left in `COACHING_FRAMEWORK_GAPS.md` as a possible future build, not currently marketed.
4. ~~**"End-of-week synthesis"**~~ — RESOLVED 2026-08-03. Not a duplicate-risk at all: `generate_weekly_synthesis()` already runs on the exact Saturday-cron schedule the gaps doc proposed as new, and the Coach page already fetches and renders it in full (`WeeklySynthesisCard`). `COACHING_FRAMEWORK_GAPS.md` was simply stale — it had been listing a shipped, fully user-facing feature as a HIGH-priority missing gap, apparently never updated after the feature landed. Corrected the doc (moved the item to Layer 4's "What Exists" table, removed it from Gaps, updated the Tier 3 and Phase 3 build-order tables to mark it shipped) rather than let anyone spend a sprint rebuilding it.
5. ~~**Two workout-intensity classifiers**~~ — RESOLVED 2026-08-03. Confirmed as a real, reproducible bug, not just a naming mismatch: a Zone-2-dominant day (this project's own docs call Zone 2 "Aerobic Base... primary training zone") was classified `Moderate` by `classify_workout_by_hr_zones()` (shown to users, injected into LLM prompts) but `Easy/Recovery` by `_classify_activity_intensity()` (used in the minimum-easy-day guardrail) — meaning the same day could be excluded from a user's "easy day" count while simultaneously being described to the LLM as accomplished. Worse, `classify_workout_by_hr_zones()` contradicted itself: its own `primary_zone<=2` fallback branch already treated Zone 2 as `Easy/Recovery` whenever Zone 2 was merely the plurality zone, while its explicit `zone_percentages[1] > 50` branch called a *more* Zone-2-concentrated day `Moderate` — backwards. Fixed by changing that branch to `Easy/Recovery`, matching the fallback, the sibling classifier, and the project's own zone definition.
