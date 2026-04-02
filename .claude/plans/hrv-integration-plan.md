# YTM Wellness Integration Plan (intervals.icu)
**Status**: Active — data path confirmed via intervals.icu API (March 2026)
**Author**: Rob Houghton / Claude Code session 2026-03-15, updated 2026-03-25
**Constraint**: Additive-only changes. Must not displace divergence-first principle. 102 production users.

---

## Data Path: intervals.icu

**Confirmed 2026-03-25**: intervals.icu REST API provides wellness data with simple API key auth.

- Endpoint: `GET /api/v1/athlete/{id}/wellness?oldest=DATE&newest=DATE`
- Auth: basic auth, username `API_KEY`, password = user's key (Settings → Developer Settings)
- Relevant fields confirmed in API response:
  - `hrv` — rMSSD (ms float)
  - `hrvSDNN` — SDNN
  - `restingHR` — integer bpm
  - `sleepSecs` — total sleep in seconds
  - `sleepScore` — Garmin composite score
  - `spO2` — blood oxygen %
  - `respiration` — overnight breathing rate
- Test confirmed 2026-03-25: manual entry of `45.0` returned as `"hrv": 45.0`

**Outstanding question**: Does intervals.icu auto-populate wellness fields from Garmin overnight?
Verification: wear Garmin 955 to sleep, check API response next morning.

**Why not other paths evaluated:**
- Strava API: does not carry Garmin wellness metrics
- garth (unofficial Garmin library): fragile auth, ToS risk, breaks when Garmin changes internal API
- Fitrockr: enterprise pricing, unknown for personal use
- Health Connect (Android): does not receive Garmin HRV data
- Garmin Connect API (official): requires OAuth + partner approval (months of lead time)

---

## Context & Architectural Anchors

The existing YTM signal stack:
- **External ACWR** — load (distance + elevation)
- **Internal ACWR** — physiology (TRIMP from HR streams)
- **Divergence** = External − Internal — the primary coaching signal
- **Morning Readiness** — subjective (sleep quality 1–5, soreness 0–100) — already in prompt

Wellness signals fill a gap that TRIMP cannot: **overnight recovery state**. TRIMP measures the
acute physiological stress of a session. Wellness signals measure whether the body has absorbed
that stress by the next morning. They answer different questions.

**All wellness signals enter at the readiness layer only.** None become ACWR streams. None
override divergence. The LLM receives all signals and interprets holistically.

### Tier 1 Signals (Phase 1 + 3 scope)

| Signal | Field | Baseline | Coaching value |
|---|---|---|---|
| HRV (rMSSD) | `hrv` | 30-day rolling avg | Primary recovery indicator; suppression = incomplete absorption of load |
| Resting HR | `restingHR` | 7-day rolling avg | Elevated = fatigue, illness, or overreaching; fast to respond |
| Sleep duration | `sleepSecs` | Absolute threshold | <6hrs = deficit; <7hrs = suboptimal; no baseline needed |

### Combined Differential (richer than any single signal)

| HRV | RHR | Interpretation |
|---|---|---|
| Suppressed | Elevated | Strong fatigue/overreaching — reduce load |
| Suppressed | Normal | Non-training stress (work, life) — note but don't cut load automatically |
| Normal | Elevated | Early illness signal — flag for awareness |
| Both normal | Both normal | Training as planned |

### Tier 2 (Phase 3+ only, lower priority)
- `spO2` — altitude training and illness detection (relevant for Sierra Nevada running)
- `respiration` — early illness detection via elevated overnight breathing rate

---

## Decision Log

### Wellness signals are NOT ACWR streams
ACWR streams must use comparable load units. Wellness signals have no load units — they are
state indicators. They enter as readiness modifiers only. Mixing them with ACWR would distort
the divergence calculation.

### Schema: Extend `journal_entries` for Phase 1, sync from intervals.icu in Phase 3

**Phase 1**: Add `hrv_value`, `hrv_source`, `resting_hr`, and `sleep_duration_secs` to
`journal_entries`. Reuses existing `ON CONFLICT (user_id, date)` upsert pattern. Fully additive.

**Phase 3**: Daily sync job pulls all Tier 1 fields from intervals.icu wellness endpoint in a
single API call. Writes directly to `journal_entries`. No intermediate table needed for Phase 3
(add `wellness_readings` raw table only if audit trail or multi-source conflict resolution needed).

### Sleep duration replaces subjective sleep quality in the prompt (but both stay in schema)
Objective `sleepSecs` from Garmin is more reliable than the subjective 1–5 sleep quality score.
When `sleepSecs` is available (Phase 3), it replaces the sleep quality line in the prompt.
The `sleep_quality` column stays in the schema — it remains visible in the journal UI and useful
for days when no Garmin data is available.

### Manual entry scope for Phase 1
- **HRV**: include manual entry field — user can read it from Garmin Connect app each morning
- **Resting HR**: include manual entry field — visible on Garmin watch face each morning
- **Sleep duration**: omit manual entry — too awkward to calculate manually; wait for Phase 3 auto-sync

---

## Phase 1: Schema + Prompt + Frontend (Manual Entry)

### 1A. Database Migration
File: `scripts/migrations/add_wellness_columns.py`

```sql
ALTER TABLE journal_entries
  ADD COLUMN IF NOT EXISTS hrv_value         NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS hrv_source        TEXT DEFAULT 'manual',
  ADD COLUMN IF NOT EXISTS resting_hr        INTEGER,
  ADD COLUMN IF NOT EXISTS sleep_duration_secs INTEGER;
```

- `hrv_value`: rMSSD in ms (e.g. 42.0). NULL = not entered.
- `hrv_source`: `'manual'` in Phase 1; `'intervals_icu'` in Phase 3.
- `resting_hr`: bpm integer. NULL = not entered.
- `sleep_duration_secs`: total sleep seconds from Garmin. NULL until Phase 3 auto-sync.
- No hard range constraints — devices vary.

### 1B. Backend — `/api/journal/readiness` (POST)

Add new fields to the existing endpoint in `strava_app.py`:

```python
hrv_value  = data.get('hrv_value')
resting_hr = data.get('resting_hr')

if hrv_value is not None:
    hrv_value = float(hrv_value)
    if hrv_value <= 0 or hrv_value > 300:
        return jsonify({'error': 'hrv_value must be between 0 and 300 ms'}), 400

if resting_hr is not None:
    resting_hr = int(resting_hr)
    if resting_hr <= 0 or resting_hr > 220:
        return jsonify({'error': 'resting_hr must be between 0 and 220 bpm'}), 400
```

Update INSERT with COALESCE so partial saves don't wipe existing fields:

```sql
INSERT INTO journal_entries
  (user_id, date, sleep_quality, morning_soreness, hrv_value, hrv_source, resting_hr, updated_at)
VALUES (%s, %s, %s, %s, %s, 'manual', %s, NOW())
ON CONFLICT (user_id, date) DO UPDATE SET
  sleep_quality    = COALESCE(EXCLUDED.sleep_quality,    journal_entries.sleep_quality),
  morning_soreness = COALESCE(EXCLUDED.morning_soreness, journal_entries.morning_soreness),
  hrv_value        = COALESCE(EXCLUDED.hrv_value,        journal_entries.hrv_value),
  hrv_source       = COALESCE(EXCLUDED.hrv_source,       journal_entries.hrv_source),
  resting_hr       = COALESCE(EXCLUDED.resting_hr,       journal_entries.resting_hr),
  updated_at       = NOW()
```

Extend `GET /api/journal/readiness` to return:
`{ sleep_quality, morning_soreness, hrv_value, resting_hr, sleep_duration_secs, hrv_baseline_30d, rhr_baseline_7d }`

Baselines computed server-side:

```sql
-- HRV 30-day baseline (require ≥7 readings)
SELECT AVG(hrv_value) AS hrv_baseline, COUNT(hrv_value) AS hrv_count
FROM journal_entries
WHERE user_id = %s
  AND date >= CURRENT_DATE - INTERVAL '30 days'
  AND date < CURRENT_DATE
  AND hrv_value IS NOT NULL

-- RHR 7-day baseline (require ≥3 readings)
SELECT AVG(resting_hr) AS rhr_baseline, COUNT(resting_hr) AS rhr_count
FROM journal_entries
WHERE user_id = %s
  AND date >= CURRENT_DATE - INTERVAL '7 days'
  AND date < CURRENT_DATE
  AND resting_hr IS NOT NULL
```

### 1C. Prompt Integration — `llm_recommendations_module.py`

Extend the readiness query to include all wellness fields:

```python
readiness_data = execute_query(
    """SELECT sleep_quality, morning_soreness, hrv_value, resting_hr, sleep_duration_secs
       FROM journal_entries
       WHERE user_id = %s AND date = %s""",
    (user_id, current_date), fetch=True
)
```

Injection logic (appended to existing `### MORNING READINESS` section):

```python
MIN_HRV_READINGS = 7
MIN_RHR_READINGS = 3

# HRV context
hrv_context = ""
if hrv_value is not None:
    baseline = hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data else None
    count    = hrv_baseline_data[0]['hrv_count']    if hrv_baseline_data else 0
    if baseline and count >= MIN_HRV_READINGS:
        ratio     = hrv_value / baseline
        pct_diff  = (ratio - 1.0) * 100
        direction = "suppressed" if ratio < 0.85 else ("elevated" if ratio > 1.15 else "normal range")
        hrv_context = (
            f"- HRV: {hrv_value:.0f}ms "
            f"(30-day baseline: {baseline:.0f}ms, "
            f"{abs(pct_diff):.0f}% {'below' if pct_diff < 0 else 'above'} baseline — {direction})"
        )
    else:
        readings_needed = max(0, MIN_HRV_READINGS - count)
        hrv_context = f"- HRV: {hrv_value:.0f}ms (building baseline — {readings_needed} more readings needed)"

# Resting HR context
rhr_context = ""
if resting_hr is not None:
    rhr_baseline = rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data else None
    rhr_count    = rhr_baseline_data[0]['rhr_count']    if rhr_baseline_data else 0
    if rhr_baseline and rhr_count >= MIN_RHR_READINGS:
        rhr_diff = resting_hr - rhr_baseline
        pct_diff = (rhr_diff / rhr_baseline) * 100
        if pct_diff >= 10:
            status = "significantly elevated"
        elif pct_diff >= 5:
            status = "elevated"
        elif pct_diff <= -5:
            status = "below baseline"
        else:
            status = "normal range"
        rhr_context = (
            f"- Resting HR: {resting_hr}bpm "
            f"(7-day baseline: {rhr_baseline:.0f}bpm, "
            f"{abs(pct_diff):.0f}% {'above' if rhr_diff > 0 else 'below'} baseline — {status})"
        )
    else:
        rhr_context = f"- Resting HR: {resting_hr}bpm (building baseline)"

# Sleep duration context (Phase 3 — auto from intervals.icu)
sleep_context = ""
if sleep_duration_secs is not None:
    hours = sleep_duration_secs / 3600
    if hours < 6:
        sleep_status = "significant sleep deficit"
    elif hours < 7:
        sleep_status = "suboptimal sleep"
    else:
        sleep_status = "adequate sleep"
    sleep_context = f"- Sleep: {hours:.1f}hrs ({sleep_status})"
```

**Override principle**: No signal overrides divergence. The LLM receives all signals and
interprets holistically. Divergence-first is preserved.

### 1D. Frontend — Morning Readiness Card (`JournalPage.tsx`)

Expand the existing card (sleep quality, morning soreness) with two new optional fields:

**HRV field:**
- Label: "HRV (ms)"
- Input: number, integer
- Placeholder: "e.g. 45"
- Tooltip: "Morning rMSSD from Garmin Connect, Apple Watch, or Whoop"

**Resting HR field:**
- Label: "Resting HR (bpm)"
- Input: number, integer
- Placeholder: "e.g. 48"
- Tooltip: "Your resting heart rate from this morning"

**Display baseline inline once established:**
- HRV: "30-day avg: 52ms" — suppressed: muted orange; elevated: sage green
- RHR: "7-day avg: 46bpm" — elevated: muted orange; normal: no color
- No data: omit entirely (no empty state clutter)

---

## Phase 2: Athlete Model + Autopsy Correlation

**Trigger**: 30+ days of Phase 1 data.

### 2A. Schema — Extend `athlete_models`

```sql
ALTER TABLE athlete_models
  ADD COLUMN IF NOT EXISTS hrv_suppression_threshold NUMERIC(4,3) DEFAULT 0.85,
  ADD COLUMN IF NOT EXISTS hrv_baseline_7d           NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS hrv_baseline_30d          NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS hrv_last_updated          DATE,
  ADD COLUMN IF NOT EXISTS rhr_elevation_threshold   NUMERIC(4,3) DEFAULT 1.05,
  ADD COLUMN IF NOT EXISTS rhr_baseline_7d           NUMERIC(5,1),
  ADD COLUMN IF NOT EXISTS rhr_last_updated          DATE;
```

### 2B. Autopsy Learning

Extend `update_athlete_model_from_autopsy()`:
- HRV: if ≥5 low-alignment days (alignment < 5) correlated with HRV suppression above current
  threshold, tighten by 0.02 (cap at 0.70). Mirrors `divergence_injury_threshold` pattern.
- RHR: if ≥5 low-alignment days correlated with elevated RHR above current threshold,
  tighten threshold by 0.01 (cap at 1.02).

### 2C. Dashboard Banner

Add wellness pills to `CompactDashboardBanner`:
- HRV suppression pill: muted orange when suppressed, sage green when normal. Omit if no data.
- RHR elevation pill: muted orange when elevated. Omit if normal or no data.
- Only show pills when today's value AND valid baseline both exist.

### 2D. Personalized Thresholds in Prompt

Replace hard-coded defaults with athlete's learned thresholds from `athlete_models`:

```python
hrv_suppression_threshold = model.get('hrv_suppression_threshold', 0.85)
rhr_elevation_threshold   = model.get('rhr_elevation_threshold', 1.05)
```

---

## Phase 3: intervals.icu Automated Sync

**Trigger**: Phase 1 adopted. Zero-friction daily pull replaces manual entry.
**Adoption gate**: Only build if Phase 1 shows ≥15% of active users entering HRV or RHR weekly.

### 3A. intervals.icu Credentials Storage

- Extend `user_settings`: add `intervals_icu_api_key TEXT`, `intervals_icu_athlete_id TEXT`
- Optional "Connect intervals.icu" step in Settings page
- Daily background job (runs after 6AM recommendation generation):

```python
# app/intervals_icu_sync.py
def sync_wellness_for_user(user_id, api_key, athlete_id, date):
    url = f"https://intervals.icu/api/v1/athlete/{athlete_id}/wellness"
    params = {'oldest': date, 'newest': date}
    resp = requests.get(url, params=params, auth=('API_KEY', api_key))
    resp.raise_for_status()
    data = resp.json()
    if not data:
        return
    w = data[0]
    execute_query("""
        INSERT INTO journal_entries
          (user_id, date, hrv_value, hrv_source, resting_hr, sleep_duration_secs, updated_at)
        VALUES (%s, %s, %s, 'intervals_icu', %s, %s, NOW())
        ON CONFLICT (user_id, date) DO UPDATE SET
          hrv_value          = COALESCE(EXCLUDED.hrv_value,          journal_entries.hrv_value),
          hrv_source         = COALESCE(EXCLUDED.hrv_source,         journal_entries.hrv_source),
          resting_hr         = COALESCE(EXCLUDED.resting_hr,         journal_entries.resting_hr),
          sleep_duration_secs= COALESCE(EXCLUDED.sleep_duration_secs,journal_entries.sleep_duration_secs),
          updated_at         = NOW()
    """, (user_id, date, w.get('hrv'), w.get('restingHR'), w.get('sleepSecs')))
```

### 3B. Sleep duration replaces subjective sleep quality in prompt

When `sleep_duration_secs` is non-null (auto-synced), use objective hours in the prompt instead
of the subjective 1–5 sleep quality score. Both remain in the schema.

### 3C. Tier 2 fields (spO2, respiration) — add to sync job at no cost

Same single API call already fetches these. Store in `journal_entries` (add columns) and inject
into prompt only when values are outside normal range:
- `spO2` < 95%: flag in prompt as potential altitude/illness signal
- `respiration` > personal 7-day average by >15%: flag as early illness signal

---

## Rollback Strategy

| Component | Rollback |
|---|---|
| Schema (Phase 1) | Nullable columns — existing queries unaffected. Drop if needed. |
| API endpoint | New optional fields — existing calls without them work identically. |
| Prompt injection | All guards are NULL checks and count thresholds. No data = no change. |
| Frontend | New optional inputs — users who ignore them see no behavior change. |
| Athlete model (Phase 2) | New columns with defaults — existing model logic unchanged. |
| intervals.icu sync (Phase 3) | Disable sync job — manual entry fallback still works. |

No feature flags needed — guards are data-driven.

---

## Files to Touch When Implementing

**Phase 1**:
- `scripts/migrations/add_wellness_columns.sql` (new)
- `app/strava_app.py` — extend `/api/journal/readiness` POST + GET
- `app/llm_recommendations_module.py` — readiness query + prompt injection
- `frontend/src/JournalPage.tsx` — Morning Readiness card (HRV + RHR fields)

**Phase 2**:
- `scripts/migrations/add_wellness_athlete_model.sql` (new)
- `app/llm_recommendations_module.py` — autopsy correlation + personalized thresholds
- `frontend/src/TrainingLoadDashboard.tsx` — banner pills

**Phase 3**:
- `scripts/migrations/add_wellness_sync_columns.sql` (new — sleep_duration_secs, spO2, respiration)
- `app/strava_app.py` — Settings endpoints for intervals.icu credentials
- `app/intervals_icu_sync.py` (new) — daily sync job
- `frontend/src/SettingsPage.tsx` — intervals.icu connect UI

---

## Open Questions

1. **Display scale**: Raw rMSSD ms confirmed — data-literate user base, no normalization needed.

2. **Garmin auto-sync to intervals.icu**: Unverified — wear Garmin 955 overnight and check `hrv`
   and `restingHR` fields in API response next morning. Determines whether Phase 3 is zero-friction.

3. **Structured output schema**: Should `assessment.primary_signal` allow `"hrv"`? No — not in
   Phase 1 or 2. HRV is a readiness modifier, not a primary signal. Revisit after Phase 2 data.

4. **Recommendation timing**: intervals.icu sync must complete before the 6AM recommendation
   job runs. Sync job should run at 5AM or be triggered as a prerequisite step.
