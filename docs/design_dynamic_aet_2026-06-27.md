# Design Guidance — Dynamic AeT in Internal Load & the Rx

**Date:** 2026-06-27 · **Status:** decisions resolved — build plan ready (not implemented) · **Source concept:** `VAULT/Dynamic AeT.md`
**Follows:** `.claude/rules/llm-determinism.md`

## Intent (Rob)

AeT is not a fixed annual number — it shifts day to day with autonomic readiness. The
system should treat AeT as **dynamic** and reflect that in (a) **internal load values**
and (b) the **daily Rx**. This doc is scoped to that keystone only; the rest of the
`Dynamic AeT.md` concept is parked (see Deferred section).

## Corrected architecture baseline (how it actually works today)

- **HR zones:** user-selectable `hr_zones_method` (`custom` lab-tested / `karvonen`-HRR /
  `percentage`) + `custom_hr_zones` (`user_settings`). Time-in-zone is computed **per HR
  sample from the stream** (`calculate_hr_zones_from_streams`, `strava_training_load.py`).
  The Z2/Z3 boundary ≈ AeT/VT1.
- **AeT today:** measured by the HR drift test (`aerobic_assessment_engine`), stored as
  `athlete_model.aet_bpm` (+ date). `get_user_hr_thresholds` uses it as VT1 when ≤42d
  fresh, else a formula. **Static.**
- **Internal load (TRIMP):** **Banister HRR exponential** (`calculate_banister_trimp`),
  average or per-sample stream. **Does not use zones or AeT.** Feeds internal ACWR →
  divergence.
- **Readiness:** `readiness_engine` computes an HRV Z-score (`hrv_z`) vs
  `hrv_baseline_30d`; `athlete_model` holds `hrv_suppression_threshold`, `rhr_baseline_7d`,
  etc.

**Key fact that shapes everything below:** zones (where AeT lives) and the TRIMP load
number (Banister, no AeT) are **separate computations today**. So "dynamic AeT" reaches
them through two different mechanisms — one easy, one a real decision.

## Shared input — Effective AeT (category 1: deterministic, injected as fact)

```
effective_AeT(today) = baseline_AeT ± readiness_offset(HRV Z-score)
```
- `baseline_AeT` = `get_user_hr_thresholds().vt1_bpm`, whose precedence is **fresh drift
  test (`athlete_model.aet_bpm`, ≤42d) → user-selected custom lab AeT (`custom_hr_zones`
  Z2 ceiling) → formula VT1**. The drift test still matters — it **calibrates the
  baseline**; the dynamic layer modulates around it. (Verified 2026-06-27: the custom-zone
  middle tier was missing from this line originally.)
- `readiness_offset` from today's HRV Z (**reuse `readiness_engine`'s `hrv_z` — do not
  recompute**). Suppressed HRV → lower AeT.
- **Per the determinism rule, the offset magnitudes are NOT hard-coded magic numbers.**
  Start with conservative defaults, store per-athlete in `athlete_model`, calibrate from
  response data over time. The source concept's ±2/5/8 bpm bands are a starting
  hypothesis, not settled values.
- Computed in code, injected as fact. Never LLM-derived.

## CORRECTION (2026-06-27, verified against code) — AeT does not reach zone classification today

The original Effect A below assumed flipping `get_user_hr_thresholds` to a dynamic VT1
would move the classification boundary. **It will not.** Verified:

- `time_in_zone1..5` are bucketed **once at sync** by `calculate_hr_zones_from_streams`
  (`strava_training_load.py:1530`) from **`user_settings` boundaries only** (50/60/70/80/90%
  maxHR, HRR, or custom). AeT/`vt1_bpm` never enters bucketing. The buckets are stored
  columns on `activities`.
- The measured-AeT override only populates `vt1_bpm`, which is consumed **as a label /
  prescription string** (`compute_zone_compliance` `:535`; prompt block `:3151`; zone
  anchor `:3182`). `compute_zone_compliance` classifies black-hole / Z2-target from the
  **pre-stored bucket percentages**, then prints `vt1_bpm` as "Zone 2 ceiling" beside them.
- **Latent bug, already present:** the prompt can say "VT1 = 135 (Z2 ceiling)" while the
  z-pcts were bucketed at Z2 ceiling = 0.70·maxHR. Label and buckets can disagree today.

**Implication:** making "130 bpm land in Z3 on a suppressed day" requires **re-bucketing
the HR stream against the AeT-anchored boundary** — not a one-line VT1 flip. Machinery
exists (`calculate_hr_zones_from_streams` + raw streams retained in `hr_streams`,
`db_utils.py:1063`); it must be invoked with the effective-AeT boundary. Effect A's real
scope is therefore "introduce AeT into the bucketing path (Z2/Z3 line only)." This also
means Effect A changes classification **even at offset 0**, because it switches the Z2/Z3
line from the `user_settings` 70% value to the measured/effective AeT — the intended fix
of the latent bug, but a behavior change to validate.

## Effect A — Rx + zone classification (lower risk; can ship first)

1. `get_user_hr_thresholds` returns the **effective (dynamic) AeT** as VT1.
2. Zone-compliance (polarized black-hole detection) re-buckets the session's HR stream
   against the **effective AeT of the session's own date** for the Z2/Z3 line → a 130 bpm
   effort correctly lands in Z3 on a suppressed day. (Per decision (d): only the Z2/Z3
   line moves; other boundaries stay from `user_settings`.)
3. Rx: inject a **"TODAY'S EFFECTIVE AeT"** authoritative fact block (baseline, today's
   value, delta, source = overnight rMSSD, fallback reason if any), parallel to the
   metric-verdict block. Element 7 execution cues use today's AeT for HR targets ("keep HR
   below 130 today, not 135"). Prose may frame a depressed AeT as a recovery signal.

*Determinism map:* effective-AeT calc + zone classification = category 1 (fact); Rx
framing/voice = category 3.

## Effect B — internal load reflects dynamic AeT (the real design decision)

The load number is Banister-HRR with **no AeT/zone input**, so making internal load
reflect dynamic AeT requires a modeling choice:

- **(a) Zone-weighted load (Edwards-style):** `load = Σ(minutes_in_zone_i × weight_i)`
  using the **dynamic** zones. Directly realizes the concept and **reuses the stream
  time-in-zone already computed**. Honest expression of "AeT moved → same HR is more
  strain." But it is a **new load metric** replacing/augmenting Banister.
- **(b) Readiness multiplier on Banister:** `trimp_adj = banister × f(HRV / AeT
  suppression)`. Smallest change; keeps Banister; less mechanistic.
- **(c) Dual-track:** keep Banister for continuity, add a dynamic-AeT load as a parallel
  signal. More complexity.

**Recommendation:** lean **(a)**, because it uses existing infrastructure and is the
truest model — but this is Rob's call; it changes the core load metric.

**CRITICAL CONSISTENCY CONSTRAINT (any option):** ACWR = acute(7d)/chronic(28d). If acute
load uses dynamic AeT but the 28-day chronic baseline was computed on the old method,
ACWR and divergence are distorted. The chosen method **must be applied consistently
across both windows** — recompute the rolling TRIMP history (backfill) OR run
forward-only with an explicit transition period before trusting ACWR. This is the
make-or-break implementation detail.

**Feed the EXISTING divergence — do not add SWI** (it is the ratio form of
`normalized_divergence` we already have).

**No new safety floor needed:** a depressed AeT raising internal load naturally tightens
the existing rest/reduce floor via higher internal ACWR → divergence (the floor built in
the June 2026 safety-floor work). Good emergent behavior.

## Integration points

- `strava_training_load.py` — `calculate_hr_zones_from_streams` (dynamic boundaries);
  `calculate_training_load` / `calculate_banister_trimp` (Effect B load method).
- `llm_recommendations_module.py` — `get_user_hr_thresholds` (VT1 = dynamic AeT); daily
  prompt builders (inject effective-AeT fact + execution cues).
- `readiness_engine.py` — source of `hrv_z` (reuse).
- `aerobic_assessment_engine.py` + `athlete_model` — baseline AeT + store offset params.
- `UnifiedMetricsService` / ACWR pipeline — window consistency (Effect B).

## Resolved decisions (2026-06-27 session)

1. **Effect B method → (a) Edwards zone-weighted load on AeT-anchored dynamic zones,
   deployed dual-track.** Banister keeps running for continuity; the Edwards-dynamic load
   runs in parallel; divergence cuts over to it only after a clean 28-day baseline;
   Banister retired post-cutover. Edwards weights (1–2–3–4–5) are category-1 constants,
   injected as fact, documented in the Training Metrics Reference Guide.
2. **ACWR consistency → forward-only in production + code-gated 28-day cutover.** Dual-track
   removes the blind window (Banister covers divergence during warmup), so consistency is
   satisfied *by construction* at cutover — both 7d and 28d windows fully populated with the
   new method. Plus a **one-time read-only validation backfill** from `hr_streams` (per-day
   reconstructed AeT) for sanity comparison only — never fed to the live Rx.
3. **Offset function → continuous, asymmetric, dead-banded, clamped** (reject the concept's
   step function — it produces noise-driven boundary cliffs). Defaults seeded into
   `athlete_model`:
   `deadband 0.5σ · slope_neg 4.0 bpm/σ · slope_pos 1.5 bpm/σ · cap_neg −8 · cap_pos +3 ·
   staleness 3d`. Asymmetry (down > up) is a **safety property**, not a tuning knob.
   `effective_AeT = round(baseline_AeT + offset)`.
   - **Hard guard (category-2, code-level, not a default):** if readiness state is
     `YELLOW_PARASYMPATHETIC` (Deep Hole) or `RED` (overreaching), clamp offset ≤ 0 —
     never raise AeT, regardless of raw `hrv_z` (the parasympathetic-overdrive inversion).
   - **Missing-HRV rule:** reuse `readiness_engine` `hrv_z` (7-day acute mean already
     smooths single gaps as a carry-forward); UNKNOWN (<14 readings) → offset 0; staleness
     ceiling decays offset → 0 when latest reading older than `staleness_days`; inject the
     fallback as an honest category-1 fact ("AeT held at baseline — HRV stale/absent since
     {date}").
   - **Calibration home = `athlete_model`** (new columns + `db_utils.py:571` allowlist),
     seeded to defaults with paired `aet_offset_n` / `aet_offset_confidence` (mirrors
     `acwr_sweet_spot_confidence`). Calibration is **deferred to drift-test anchoring**:
     each drift test yields a `(hrv_z_that_day, measured_AeT − baseline)` pair; fit
     per-athlete slopes once `aet_offset_n ≥ N`. Honest framing until then: population
     default, not personalized.
4. **Zone rescaling → only the VT1 / Z2-ceiling (= Z3 floor) shifts.** VT2 and all higher
   boundaries and the Z1/Z2 split stay anchored — we have a daily proxy for the aerobic
   threshold but **none for VT2**; rescaling all zones would fabricate unmeasured VT2
   movement (determinism violation). Z3 widening downward is the *correct* expression of
   "easy ceiling fell, hard ceiling didn't." Clamps: `effective_AeT` strictly above the
   Z1/Z2 boundary and strictly below VT2 (both category-1 sanity asserts).
5. **HRV source/cadence → single source: intervals.icu, field = rMSSD (ms)** (`hrv_source`
   tracked). Device is **Oura overnight HRV (rMSSD)** (confirmed by Rob), not waking
   spot-check — relabel honestly as "overnight HRV (rMSSD)" in the Rx. Cadence is **~⅔ of
   days same-day** (Rob: 20/30 last 30d, 50/60 60d, 77/90 90d), with occasional 3-day gaps
   — which *confirms* the decision-3 robustness work is load-bearing. Chronic baseline
   reliably computable (≥14 readings present).

## Phased build plan

Sequence: **shared core → Effect A (Rx) → Effect B (load, dual-track) → cutover.** Each
phase ships independently; nothing downstream breaks if a later phase is paused.

**Implementation status (2026-06-27):** Phase 0 ✅ (349b25c) · A1 ✅ (f2dda10) · A2+A3 ✅
(f5e1f77) — Effect A live (autopsy classifies against session-date effective AeT; daily Rx
injects the "TODAY'S EFFECTIVE AeT" fact + AeT-anchored cues). B1 ✅ (adc10be, Edwards
`trimp_dynamic` at sync, dark) · B2 ✅ (6e1bde8, parallel dynamic ACWR + cutover gate,
dark) · B-validate ✅ (afdba38, read-only report). **B-cutover NOT done** — deferred
pending forward coverage + divergence-threshold recalibration (see B-cutover below).
Nothing deployed (local-deploy model).

### Phase 0 — schema + effective-AeT core (dark; no user-facing change)
- Migration: add `athlete_model` offset columns (`aet_offset_deadband`, `_slope_neg`,
  `_slope_pos`, `_cap_neg`, `_cap_pos`, `_staleness_days`, `aet_offset_n`,
  `aet_offset_confidence`); add all to the `upsert_athlete_model` allowlist; seed defaults
  on read (fallback to constants if NULL).
- New pure function `compute_effective_aet(user_id, baseline_aet, vt2, z1z2_floor, today)`
  → `{effective_aet, offset, state, fallback_reason}`. Implements the offset function,
  Deep-Hole/RED clamp, staleness decay, UNKNOWN→0, and both sanity clamps. Pulls `hrv_z` +
  state + latest-HRV-date from `readiness_engine` (no recompute).
- **Tests (pure, no DB):** offset across the `hrv_z` range; asymmetry; dead-band; both
  caps; Deep-Hole/RED clamp overrides positive `hrv_z`; staleness decay; UNKNOWN→0;
  floor/ceiling clamps; integer rounding.

### Phase A — Effect A: dynamic zone classification + Rx (lower risk)
- Add `rebucket_zone_times(activity_id, activity_date, effective_aet)` — reads the stored
  `hr_streams` row, re-buckets with the Z2/Z3 line = `effective_aet` (other boundaries from
  `user_settings`). Falls back to stored `time_in_zone*` if no stream.
- `compute_zone_compliance` uses AeT-anchored zone times (effective AeT **of the session's
  date**) for black-hole / Z2-target detection. `get_user_hr_thresholds` `vt1_bpm` =
  today's effective AeT → label and buckets finally agree (closes the latent bug).
- Inject **"TODAY'S EFFECTIVE AeT"** fact block + element-7 HR cues into the daily Rx.
  (Agentic chat + journal endpoint: note as follow-up per the 3-call-site rule; v1 = daily
  Rx.)
- **Tests:** re-bucketing moves a 130-bpm-heavy stream from Z2→Z3 as effective AeT drops
  135→127; Rx fact block renders baseline/today/delta and the honest fallback when HRV
  stale; **behavior-change check** — at offset 0 classification now uses measured AeT (not
  70% maxHR); confirm the shift is sensible and intended.

### Phase B — Effect B: Edwards dynamic load (dual-track, dark)
- Migration: add `activities.trimp_dynamic REAL` (nullable; forward-only — NULL for
  history).
- At sync: compute AeT-anchored zone times (effective AeT of the activity's date) → Edwards
  weighted sum → write `trimp_dynamic`. **Banister `trimp` unchanged and still primary.**
- Extend `acwr_calculation_service` to compute a **parallel** dynamic internal ACWR from
  `trimp_dynamic` over the same 7d/28d windows. **Not fed to `normalized_divergence` yet.**
- **Tests:** Edwards weighting from zone times; `trimp_dynamic` > Banister-equivalent on a
  suppressed-AeT, Z3-heavy day; parallel ACWR correct over windows.

### Phase B-validate — one-time backfill (analysis only) ✅ DONE
- `scripts/validate_dynamic_aet.py` — **read-only** (writes nothing to the DB): reconstructs
  per-day effective AeT, re-buckets stored streams, Edwards-weights in memory, and compares
  the dynamic internal-ACWR/divergence series against Banister; reports the no-stream load
  fraction. Prints a summary + a CSV to the scratch dir.

**Results (2026-06-27, user 1, trailing 60d):**
- **No-stream load fraction = 0.0%** (all 87 activities have HR streams) → the B2 no-stream
  fork is moot for this athlete; NULL handling is unbiased. (Re-check for any athlete with
  appreciable stream-less load before trusting their dynamic track.)
- **The dynamic track amplifies the overtraining signal during hard blocks** — it runs more
  negative than Banister (hard week: dynamic divergence ≈ −0.45 vs Banister ≈ −0.30; dynamic
  internal ACWR ≈ 2.1 vs Banister ≈ 1.8) and leans positive on easy days. This is the
  intended effect of Edwards-on-dynamic-zones (Z3+ time weighted harder).
- **22/60 sign flips vs Banister**, but the large-magnitude flips agree in sign during the
  build; flips are almost all tiny-magnitude wobble near zero on low-load days. Mean |Δ|
  0.099, max 0.335.

### Phase B-cutover — code-gated switch (mechanism BUILT; flip deferred)

**Mechanism in place (commit 0258b9b) — the cutover is self-announcing, triggered by state
not memory:**
- Feature flag `dynamic_aet_divergence_cutover` — special-cased in `utils/feature_flags.py`
  to **bypass the admin catch-all** (never auto-enables for user 1); flip = add the id to
  `cutover_user_ids` after recalibration.
- Gated swap in `UnifiedMetricsService` — replaces internal ACWR/divergence with the dynamic
  track only when the flag AND `dynamic_acwr_cutover_ready()` both pass; **no-op otherwise**.
- Self-announcing: when data-ready but flag-off, logs a recurring `[DYNAMIC-AET CUTOVER
  READY]` banner, and the admin dashboard feature-flags component raises an INFO notice via
  `dynamic_aet_cutover_status()`.

**Prerequisites (both required before flipping):**
1. **Forward coverage:** deploy B1, then accrue ≥28 days so `dynamic_acwr_cutover_ready`
   passes (gate already implemented in `dynamic_aet.py`: ≥28-day dynamic coverage AND no
   stream-bearing activity in the trailing 28d missing `trimp_dynamic`). Forward-only
   guarantees both ACWR windows are self-consistent at the flip.
2. **Divergence threshold recalibration (the load-bearing finding from B-validate):** the
   `athlete_models` divergence thresholds (`divergence_injury_threshold` default 0.15,
   `typical_divergence_low/high`) were calibrated to the **Banister** divergence
   distribution. The dynamic divergence sits systematically **more negative during builds**
   — flipping the input without recalibrating would **over-flag overtraining**. Cutover is
   therefore NOT a pure input swap. Recalibrate the thresholds (and/or the personal
   divergence band) against the dynamic-divergence distribution — derive them from the same
   reconstruction the B-validate script produces, or re-fit forward once coverage exists.

**The switch itself:** point `normalized_divergence`'s internal input from the stored
Banister `trimp_acute_chronic_ratio` to `calculate_dynamic_internal_acwr(...)`'s ratio in
`UnifiedMetricsService` (the live read site), gated on `dynamic_acwr_cutover_ready`.

- **No new safety floor** — depressed AeT → more Z3 → higher dynamic internal ACWR →
  existing `enforce_safety_floor` tightens automatically (emergent, desired). NOTE: because
  the dynamic divergence runs more negative, confirm the floor's trigger threshold is part
  of the recalibration above, not left at the Banister-tuned value.
- Keep Banister computing for a comparison window, then optionally retire from divergence.
- **Tests:** cutover gate fires only when ready; **consistency assert** — after cutover no
  ACWR window mixes Banister and Edwards; recalibrated thresholds applied to the dynamic
  distribution, not the Banister one.

### Cross-cutting
- **Determinism tags:** effective_AeT, AeT-anchored bucketing, Edwards weights,
  `trimp_dynamic`, dynamic ACWR = category 1. Deep-Hole/RED clamp + safety floor =
  category 2. Session choice within the floor + Rx prose = category 3. Format/cue scaffolds
  = category 4 `[COMP]`.
- **Dockerfile:** any new `.py` module → `app/Dockerfile.strava`.
- **Reference guide:** document effective-AeT definition, offset defaults, Edwards weights
  in `app/Training_Metrics_Reference_Guide.md`.
- **Migrations** run autonomously via the Cloud SQL proxy (proxy confirmed live this
  session).

## Deferred for future consideration (memorialized, out of scope here)

- **HRR intra-run decay auditor** — within-run autonomic fatigue from mid-run HR-recovery
  slowing. Genuinely novel (YTM has no within-run autonomic signal). Validate event-
  detection reliability on noisy trail/optical HR streams *before* acting on it.
- **SWI (Strain-to-Work Index = internal/external ACWR ratio)** — do **not** build; it is
  the ratio form of the existing `normalized_divergence`. Duplicative.
- **"Micro-vetoes-macro" veto engine** (SWI + HRR drift) — revisit only if/after HRR
  proves reliable; thresholds must be personalized in `athlete_model`, not hard-coded.
