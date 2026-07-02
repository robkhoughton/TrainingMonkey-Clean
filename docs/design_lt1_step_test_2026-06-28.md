# Design — LT1 Lactate Step Test as a Selectable AeT Assessment Method

**Status:** Design only — NOT implemented. For sign-off before coding.
**Date:** 2026-06-28
**Related:** `app/workout_library.py` (AEROBIC_ASSESSMENT_PROTOCOL), `app/coaching_context/aerobic_assessment.md`, `app/dynamic_aet.py`, `docs/design_dynamic_aet_2026-06-27.md`, `athlete_models.aet_bpm` + VT1 override (`get_user_hr_thresholds`)

---

## 1. The reframe (why this is not a new workout)

YTM already schedules an AeT assessment — the **HR Drift Test** — on a 28-day window / 42-day-overdue cadence, blocked in taper/peak/recovery, "replaces one Zone 2 run," writing its result to `athlete_models.aet_bpm` (consumed by the VT1 override / zone system / dynamic AeT).

`aerobic_assessment.md` defines **AeT = Zone 2 ceiling = VT1 ≈ 2 mmol/L lactate.** The HR drift test is an *indirect* estimate of that boundary; a **lactate step test is the direct measurement of the same boundary.**

→ Therefore the LT1 step test is **a second method for the existing AeT-assessment slot, not a new training stimulus.** It shares the slot's cadence, blocked phases, fresh-legs placement, light-session classification, and the `aet_bpm` write path. One boundary, one scheduler, one AeT field.

## 2. Decisions locked (Rob, 2026-06-28)

1. **Slot:** Method of the existing AeT assessment — **not** a standalone scheduler.
2. **Method selection:** A **user-selectable either/or option**, not a hidden capability flag. The user picks which AeT assessment they use (HR Drift Test *or* Lactate Step Test). The scheduler prescribes the chosen one when the retest window opens.
3. **Clear in-app protocols:** Both protocols must be presented as readable step-by-step instructions **in the app UI** (assessment panel), not only inside the LLM prompt.
4. **Scope (v1):** **LT1-only, light session** — directly interchangeable with the drift test (replaces an easy Z2 run). **LT1+LT2 ramp deferred** (anticipate it; don't build yet).
5. **LT1 analyzer (v1):** **First sustained rise above baseline.** **Dmax / modified-Dmax deferred** (more desirable, more code — later). Definition must be deterministic (category-1 authoritative computation per `.claude/rules/llm-determinism.md`).

## 3. The v1 LT1 step-test protocol (light, submax)

Goal: find the HR (and speed/grade) at the first sustained lactate rise — LT1 — without going near LT2. Controlled treadmill.

- **Warm-up:** 10–15 min very easy. Take a **baseline lactate** sample at the end of the warm-up (clean, low reading — this anchors the "rise").
- **Stages:** 3–4 min each (lactate needs ≥3 min to reflect the stage; shorter under-reads). **Grade-based progression** — hold a fixed, comfortable speed and raise the incline each stage (keeps running cadence/form constant and is race-specific for a trail/uphill athlete). Start near-flat (0–1% grade) at an effort clearly below AeT (HR ~20–25 bpm under estimated AeT).
- **Increment:** constant grade step — default **+1.5% grade per stage** (configurable). Speed stays fixed for the whole test. Constant increment + fixed speed matter for comparability across tests.
- **Sampling:** fingertip lactate + steady-state HR recorded at the **end of each stage** (brief straddle/step-off to draw blood is acceptable; resume immediately).
- **Stop criteria (LT1-only):** terminate once **two consecutive stages** show lactate ≥ `baseline + LT1_RISE_THRESHOLD` and trending up (rise confirmed as sustained, not noise). Peak lactate stays ~2.5–3 mmol → genuinely light. **Do not push to LT2.**
- **Placement / cost:** same as the drift test — replaces one easy Zone 2 run, fresh legs (not within 2 days of a long/hard session), blocked in taper/peak/recovery.

**Protocol-consistency requirement (for comparability across tests):** identical warm-up, stage length, and increment every time; control heat, hydration, caffeine, glycogen, and time-of-day. (Same consistency logic as HRV measurement.) Surface these as preconditions in the UI.

## 4. The analyzer (v1 — first sustained rise)

Deterministic, documented, injected as fact (never LLM-judged).

```
baseline_lactate = min(stage lactate over the first low stages)   # running minimum
LT1 = first stage S where:
        lactate[S]   >= baseline_lactate + LT1_RISE_THRESHOLD_MMOL
    AND lactate[S+1] >= lactate[S]                                  # sustained, beats meter noise
LT1_bpm   = HR at stage S            (optionally linear-interpolate between S-1 and S)
LT1_speed = speed/grade at stage S
```

- **`LT1_RISE_THRESHOLD_MMOL` — open decision (recommend 0.3).** Documented constant. The "two consecutive stages" requirement is what defends against ±0.2–0.3 mmol meter noise; without it a single 0.3 bump could be noise.
- **Meter-noise caveat** (surface in UI + interpretation): portable lactate meters carry ~±0.2–0.3 mmol; treat LT1 as protocol-/trend-based, not single-decimal precision. Require a clean baseline reading; if no sustained rise is captured, the test is invalid (mirrors the drift test's "unusable result" handling — never invent an AeT).
- **Output AeT:** `aet_bpm = LT1_bpm`, identical contract to the drift test — flows straight into the existing VT1 override and dynamic-AeT baseline. The model treats `aet_bpm` the same regardless of method.
- **Structure for the future:** keep the analyzer pluggable so **Dmax** (and an **LT2** detector for the future ramp) can be added without reworking storage.

## 5. Build surface (multi-file — for scope visibility)

| Area | Change |
|---|---|
| **User setting** | `aet_assessment_method` in `user_settings` — enum `'hr_drift'` (default) \| `'lactate_step'`. UI toggle on Season/settings. |
| **Schema** | **New `lactate_step_tests` table** (decided — kept separate for curve comparison over time): `(id SERIAL PK, user_id, test_date, speed, stages JSONB [{stage,grade,hr,lactate}], baseline_lactate, lt1_bpm, lt1_grade, method, notes, created_at)`. Add `aet_method` alongside `athlete_models.aet_bpm`/`aet_test_date`. JSONB curve so Dmax/LT2 reuse it. Migration script → `scripts/migrations/`. |
| **`workout_library.py`** | New `LACTATE_STEP_TEST_PROTOCOL`; scheduler selects protocol text by `aet_assessment_method`; status logic (current/window_open/overdue/blocked) shared with the drift test. |
| **Analyzer** | New deterministic function: step table → LT1_bpm + baseline + validity. (New module → add to `Dockerfile.strava`.) |
| **Input UI** | Manual step-table entry panel (no auto lactate stream): speed/grade, HR, lactate per stage → POST → analyzer → writes `aet_bpm`/`aet_test_date`/`aet_method` → displays LT1 + curve. |
| **In-app protocols** | Render both protocols (drift + lactate step) as clear instructions in the assessment panel. |
| **Coaching context** | Update `aerobic_assessment.md`: AeT may come from either method; both produce `aet_bpm`; LT1 (lactate) is direct ≈ first rise, drift is indirect; treat `aet_bpm` identically. |

## 6. Decisions resolved (2026-06-28)

1. **`LT1_RISE_THRESHOLD_MMOL` = 0.3 mmol** over baseline (default; not explicitly overridden — flag to revisit if tests show it's too sensitive/insensitive).
2. **Storage** — **new `lactate_step_tests` table** (kept separate from `aerobic_assessments` to preserve the full lactate curves for comparison over time).
3. **Stepping** — **grade-based**: fixed speed, +1.5% grade per stage (default, configurable).
4. **Entry UX** — **post-run single-screen step table** (enter speed + per-stage grade/HR/lactate after the test).

## 7. Determinism check

- LT1 value, baseline, AeT bpm, validity → **deterministic code, injected as fact** (category 1).
- "Don't invent an AeT from an invalid/no-rise test" → **safety/guard** (category 2), mirrors existing drift-test handling.
- Method selection → user config. Protocol text → reference. No LLM judgment in any threshold.

---

**Next step:** Rob reviews §6 open decisions → I produce the migration + code changes (still user-built/deployed per project rules). No code until sign-off.
