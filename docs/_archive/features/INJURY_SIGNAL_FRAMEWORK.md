# Injury Signal Framework — Design & Architecture Reference

*Last updated: 2026-03-22*

---

## Design Intent

The goal is to characterize each athlete's **personal training envelope** — the range within which they can push hard, sustain load, and perform well. The divergence threshold serves two jobs:

- **Safe range (liberating):** where the athlete is thriving at elevated load — divergence is negative, alignment is high, no distress — and the system should affirm that range as normal and safe for this individual
- **Breakdown threshold (protective):** the point beyond which the athlete has historically shown distress — divergence has moved far enough outside the safe range, with physical signals, that early warning is warranted

**Both jobs are equally important.** An athlete who sees constant warnings when they're actually fine learns to ignore the coach. A well-calibrated threshold is silent when silence is correct, and trusted because of it.

The threshold is not just a danger line — it describes the athlete's capacity. "Your coach has learned that you can sustain divergence of -0.12 without distress" is as valuable a finding as "your breakdown threshold is -0.22 — you've never been there without consequence."

---

## The Divergence Model

Three zones, two computed values. Zero is the natural boundary between recovery and productive training — positive divergence means the body is not under meaningful stress, no personal calibration needed.

```
     0.00          -0.12              -0.20
      |              |                  |
   neutral         div_low           threshold
←— recovery —→←— productive —→←— danger —→
```

- **Recovery zone** (positive to 0): easy days, active recovery — healthy but not where adaptation happens
- **Productive training window** (0 to `div_low`): real training stress, adaptation territory — the zone to affirm and protect
- **Danger zone** (beyond `threshold`): historical breakdown territory, early warning warranted

`div_low` is the lower edge of what this athlete can sustain productively while healthy. `threshold` is how far beyond that edge they've gone before things broke down.

`typical_divergence_high` is not computed — positive divergence needs no personal calibration.

---

## Current Implementation (as of 2026-03-22)

### Three-Category Deviation Framework

When an athlete deviates from the plan, exactly one of three things happened:

| Category | Signal | Response |
|---|---|---|
| **Physical** | Fatigue, injury, pain, low energy | Early warning → update athlete model |
| **External/Life** | Weather, travel, work, schedule | Prompt to review training availability |
| **Plan mismatch** | Wrong terrain, wrong volume, habitually unexecutable | Feedback into plan generation |

Cause classification is not just about routing responses — it's the gate that makes alignment meaningful as a calibration input. Only physical-cause deviations contribute to threshold calibration.

### `typical_divergence_low` — Productive Window Edge

Computed in `update_athlete_model()` (`llm_recommendations_module.py`) on every autopsy:

- Source: last 60 days of activities joined with autopsies and journal entries
- Qualifying days: alignment ≥ 7, pain% = 0 or NULL, energy ≥ 3 or NULL, real activity (not rest)
- Statistic: P20 of the normalized divergence distribution on qualifying days
- Minimum N: 5 qualifying days required; otherwise existing value unchanged
- Default: -0.05 (population constant, replaced once N≥5 healthy days available)

### `divergence_injury_threshold` — Breakdown Threshold

Computed in `update_athlete_model()` on every autopsy:

- Source: autopsies where `deviation_reason = 'physical'` (written by Phase C) joined with activity divergence
- Qualifying events: `normalized_divergence < typical_divergence_low` (beyond the productive window)
- Statistic: median of qualifying event divergence values, stored as absolute value
- Minimum N: 3 physical distress events required; otherwise existing value unchanged
- Default: 0.15 (stored positive, displayed as -0.15; replaced once N≥3 distress events available)
- Guaranteed to be more negative than `div_low` by construction — distress events are defined as beyond `div_low`

### Phase C — Deviation Classification

`classify_deviation()` (`llm_recommendations_module.py`) runs synchronously after autopsy in the journal POST handler:

- Detects physical cause: injury/pain flags from `extraction_result` and `structured_output.risk.flags`, fatigue from RPE calibration signal, consecutive injury days in `deviation_log`
- Detects external cause: keyword scan of `preference_note` (weather, travel, work, schedule, sick, illness)
- Checks ACWR spike (>20% above `load_target_high`)
- Classifies Tier 1 vs Tier 2, logs to `deviation_log`
- **Writes `deviation_reason` ('physical' / 'external' / 'unknown') to `ai_autopsies`** — this is the gate for threshold calibration
- Tier 2 sets `revision_pending` flag

Physical detection is **independent of alignment score** — an athlete who completes a workout in pain can still be classified as physical even if alignment ≥ 5.

### Programmatic Enforcement

`apply_athlete_model_to_thresholds()` (`llm_recommendations_module.py`) overrides risk thresholds with athlete-specific values:

- `divergence_overtraining` ← `-divergence_injury_threshold` (no-op at default 0.15; activates when real calibration exists)
- `divergence_moderate_risk` ← `typical_divergence_low` (no-op at default -0.05; activates when real calibration exists)

These overrides propagate into both the weekly program builder and the daily recommendation generator.

### Early Warning System

Pattern: 2 of the last 5 autopsies with `deviation_reason = 'physical'`.

When triggered:
- Sets `early_warning_active = TRUE` and `early_warning_message` on the athlete model
- Surfaces as an amber banner in JournalPage (session-dismissible by athlete)
- Exposed via `/api/athlete-model/early-warning` endpoint

Single threshold crossings are noted but do not trigger early warning. The sustained pattern requirement filters noise.

### Athlete Model Card (CoachPage)

Three sections replace the previous four-metric grid:

1. **Coach Learning**: journal coverage bar (% of last 30 days activities with journal entries), autopsies progress bar (capped at 20), milestone unlocks at 5/10/20 autopsies
2. **Training Envelope**: productive window (0.000 to div_low) and breakdown threshold (−div_injury). Shows "Calibrating…" when values are still at defaults
3. **Plan Execution**: avg lifetime alignment (/10) and alignment trend (improving/stable/declining)

Badge states: Getting Started → Learning (≥5 autopsies) → Calibrated (≥10 + both envelope values off defaults).

### Execution Flow (Journal Submit → Autopsy)

The autopsy is **synchronous** — runs in the journal POST handler immediately on submit. `update_athlete_model()` must run AFTER Phase C so `deviation_reason` is available for threshold calibration.

```
POST /api/journal
  → Save journal entry
  → generate_enhanced_autopsy()         ← synchronous LLM call
  → Phase C: classify_deviation()       ← writes deviation_reason to ai_autopsies
  → update_athlete_model()              ← AFTER Phase C (deviation_reason dependency)
  → Phase D: alignment_queries insert   ← runs if alignment < 4 and nothing extracted
  → Generate tomorrow's recommendation  ← uses fresh autopsy
```

---

## Data Available for Calibration

Journal page collects (all manual entry, stored in `journal_entries`):
- **RPE**: 1–10 scale
- **Pre-workout energy**: 1–5 scale
- **% of time thinking about pain**: 0, 20, 40, 60, 80, 100
- **Free text notes**

The autopsy LLM receives this data. Phase C extracts injury/fatigue signals from `extraction_result` and `structured_output`.

---

## Known Weaknesses

### Weakness 4: Blind to skipped workouts
No activity record → no divergence data → model learns nothing. Clean blind spot. No fix currently in place.

### Weakness 5: Completed-in-pain workouts (partially addressed)
If an athlete completes a workout in pain but divergence doesn't cross `typical_divergence_low` (e.g., ran easy while injured), the threshold calibration query misses it. Phase C can still classify the event as physical via subjective signals (RPE, pain%, notes), but the threshold update requires `divergence < div_low` — so a physically distressed but easy workout doesn't contribute to threshold calibration even if Phase C flags it correctly.

---

## Remaining Gaps

### Gap 4: Targeted Follow-Up Questions (Phase D) — Medium Priority
Phase D currently inserts a generic alignment query when `alignment_score < 4` and extraction found nothing significant. The question is not tailored to what the athlete actually submitted.

**Target:** Generate a targeted follow-up question that cross-references the athlete's specific RPE, energy level, pain percentage, and notes. Example: "I see you went in with energy=1 and 40% pain time, but your note doesn't mention fatigue — bad sleep or something else?" Lower friction than a form, richer signal.

### Gap 5: Plan Mismatch Path — Low Priority
Phase C detects physical and external causes but has no plan mismatch classification. Signal: athlete habitually deviates on workouts requiring terrain or volume inconsistent with their location or schedule. This category should feed back into plan generation, not the athlete model.

### Gap 6: Confidence Redefinition — Low Priority
`acwr_sweet_spot_confidence` increments 0.05 per autopsy — it measures journal count, not calibration quality. Real confidence requires qualifying events on **both sides** of the envelope: enough distress events to establish the breakdown threshold, enough high-performance events to establish the safe range.

Replace with a metric that reflects how well-characterized the envelope is:
- `div_low_n`: number of qualifying healthy days used to compute `typical_divergence_low`
- `threshold_n`: number of physical distress events used to compute `divergence_injury_threshold`
- Composite confidence = function of both N values, not autopsy count

---

## DB Schema (relevant columns)

### `athlete_models`
| Column | Type | Purpose |
|---|---|---|
| `typical_divergence_low` | FLOAT | P20 of healthy day divergence. Default -0.05 |
| `divergence_injury_threshold` | FLOAT | Median of physical distress event divergence (stored positive). Default 0.15 |
| `early_warning_active` | BOOLEAN | 2-of-5 physical pattern triggered |
| `early_warning_message` | TEXT | Message surfaced in JournalPage banner |
| `acwr_sweet_spot_confidence` | FLOAT | Autopsy count proxy (0.05/autopsy, cap 1.0) — to be replaced by Gap 6 |
| `avg_lifetime_alignment` | FLOAT | Weighted moving average (30% new / 70% historical) |
| `recent_alignment_trend` | TEXT | 'improving' / 'stable' / 'declining' / 'insufficient_data' |
| `total_autopsies` | INT | Count of autopsies run |

### `ai_autopsies`
| Column | Type | Purpose |
|---|---|---|
| `deviation_reason` | TEXT | 'physical' / 'external' / 'unknown' — written by Phase C |
| `alignment_score` | FLOAT | Plan adherence 0–10 |
| `autopsy_analysis` | TEXT | LLM narrative |

---

## Key Files

| File | Relevance |
|---|---|
| `app/llm_recommendations_module.py` | `classify_deviation()`, `update_athlete_model()`, `apply_athlete_model_to_thresholds()`, `get_athlete_model_context()` |
| `app/strava_app.py` | `save_journal_entry()` — full execution flow with Phase C/D |
| `app/db_utils.py` | `upsert_athlete_model()` allowed_columns, `get_pending_alignment_query()` |
| `frontend/src/CoachPage.tsx` | `AthleteModelPanel` component, `AthleteModel` interface |
| `frontend/src/JournalPage.tsx` | Early warning banner, `earlyWarning` state |
| `docs/features/COACHING_FRAMEWORK_GAPS.md` | Layer 3 gaps: pain location (HIGH), adoption (HIGH), structured deviation flag (LOW) |
