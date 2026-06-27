# Design Guidance — Dynamic AeT in Internal Load & the Rx

**Date:** 2026-06-27 · **Status:** design guidance (not implemented) · **Source concept:** `VAULT/Dynamic AeT.md`
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
- `baseline_AeT` = `athlete_model.aet_bpm` if fresh (≤42d), else formula VT1. The drift
  test still matters — it **calibrates the baseline**; the dynamic layer modulates around it.
- `readiness_offset` from today's HRV Z (**reuse `readiness_engine`'s `hrv_z` — do not
  recompute**). Suppressed HRV → lower AeT.
- **Per the determinism rule, the offset magnitudes are NOT hard-coded magic numbers.**
  Start with conservative defaults, store per-athlete in `athlete_model`, calibrate from
  response data over time. The source concept's ±2/5/8 bpm bands are a starting
  hypothesis, not settled values.
- Computed in code, injected as fact. Never LLM-derived.

## Effect A — Rx + zone classification (lower risk; can ship first)

1. `get_user_hr_thresholds` returns the **effective (dynamic) AeT** as VT1, so the Z2
   ceiling moves daily.
2. Time-in-zone and zone-compliance (polarized black-hole detection) computed against
   today's dynamic boundaries → a 130 bpm effort correctly lands in Z3 on a suppressed
   day. **This realizes the concept's core effect using the existing zone machinery.**
3. Rx: inject a **"TODAY'S EFFECTIVE AeT"** authoritative fact block (baseline, today's
   value, delta, why), parallel to the metric-verdict block. Element 7 execution cues use
   today's AeT for HR targets ("keep HR below 130 today, not 135"). Prose may frame a
   depressed AeT as a recovery signal.

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

## Open decisions (resolve before building)

1. Effect B method: zone-weighted (a) vs Banister multiplier (b) vs dual-track (c).
2. ACWR consistency: backfill rolling history vs forward-only transition.
3. Offset function shape/magnitude + calibration home (`athlete_model`); defaults to start.
4. Does effective AeT shift only the Z2 ceiling, or proportionally rescale all zones?
5. HRV source/cadence: confirm daily waking rMSSD is reliably populated, and from what device.

## Deferred for future consideration (memorialized, out of scope here)

- **HRR intra-run decay auditor** — within-run autonomic fatigue from mid-run HR-recovery
  slowing. Genuinely novel (YTM has no within-run autonomic signal). Validate event-
  detection reliability on noisy trail/optical HR streams *before* acting on it.
- **SWI (Strain-to-Work Index = internal/external ACWR ratio)** — do **not** build; it is
  the ratio form of the existing `normalized_divergence`. Duplicative.
- **"Micro-vetoes-macro" veto engine** (SWI + HRR drift) — revisit only if/after HRR
  proves reliable; thresholds must be personalized in `athlete_model`, not hard-coded.
