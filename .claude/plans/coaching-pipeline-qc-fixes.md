# Plan: Coaching Pipeline QC Fixes
*Source: docs/architecture/coaching-pipeline-qc-audit.md (2026-03-22)*

## Context

The QC audit identified 16 findings across the coaching pipeline. Two are high-severity (core personalization is
broken; agentic path has unknown context parity). The rest are medium/low signal-quality and silent-failure issues.
This plan groups them into four phases by risk and dependency — earlier phases have no dependencies and can be done
independently.

---

## Phase 1 — Quick Fixes (no schema changes, low risk)
*~6 targeted edits, all in existing functions*

### 1-A: Silent failure fallbacks (Findings 3-A, 3-B)
**File:** `app/llm_recommendations_module.py`

- **3-A** (`create_enhanced_prompt_with_tone`, except block ~line 1057-1059):
  Replace the empty string fallback with a race-goal-aware fallback. Both `get_race_goals()` and
`format_race_goals_for_prompt()` already exist in `coach_recommendations.py`:
  ```python
  except Exception as e:
      logger.warning(f"Phase B: weekly context injection failed for user {user_id}: {e}. Falling back to race goals.")
      try:
          from coach_recommendations import get_race_goals, format_race_goals_for_prompt
          fallback_goals = get_race_goals(user_id)
          goals_str = format_race_goals_for_prompt(fallback_goals)
          weekly_context_block = f"\n### WEEKLY CONTEXT\n[Weekly plan unavailable — using race goals directly]\n{goals_str}\n"
      except Exception:
          weekly_context_block = "\n### WEEKLY CONTEXT\n[Weekly context unavailable — recommendation generated from current metrics only]\n"
  ```
  This preserves the season goal signal even when the weekly program is missing or the DB call fails.

- **3-B** (`get_athlete_model_context`, except block ~line 2132):
  Change `return ""` to:
  ```python
  return "ATHLETE MODEL: UNAVAILABLE (fetch error — using population defaults)"
  ```

### 1-B: Fix alignment trend monotonicity (Finding 2-B)

**File:** `app/llm_recommendations_module.py:update_athlete_model:~2197`

Replace strict 3-point monotone check with endpoint comparison:
```python
# Before
if recent_scores[0] > recent_scores[1] > recent_scores[2]:
    trend = 'improving'
elif recent_scores[0] < recent_scores[1] < recent_scores[2]:
    trend = 'declining'

# After
if recent_scores[0] > recent_scores[2]:
    trend = 'improving'
elif recent_scores[0] < recent_scores[2]:
    trend = 'declining'
```
(Most recent vs. oldest; middle value is noise.)

### 1-C: Skip model alignment update on fallback autopsy (Finding 3-C)

**Files:** `app/llm_recommendations_module.py` (flag), `app/strava_app.py:save_journal_entry()` (call site guard)

In `generate_basic_autopsy_fallback_enhanced()`, add a flag to the return dict:
```python
return {
    'analysis': analysis,
    'alignment_score': alignment_score,
    'is_fallback': True
}
```

At the call site in `strava_app.py:save_journal_entry()`, skip `update_athlete_model()` if `is_fallback` is True. Per the
execution order invariant, `update_athlete_model()` runs after Phase C in that function — that is the only call site to
modify.

### 1-D: Add tone to agentic path (Finding 6-B)

**File:** `app/llm_recommendations_module.py:generate_recommendations_agentic:~3308`

Fetch `get_user_coaching_spectrum(user_id)` and `get_coaching_tone_instructions()` at the top of the function. Prepend
tone instructions to `system_turn1`:
```python
spectrum_value = get_user_coaching_spectrum(user_id)
tone_instructions = get_coaching_tone_instructions(spectrum_value)
system_turn1 = tone_instructions + "\n\n" + system_turn1
```

---

## Phase 2 — Signal Quality Fixes (no schema changes)

*Improves data quality fed into prompts*

### 2-A: Unify autopsy insight extraction (Finding 2-A)

**File:** `app/coach_recommendations.py`

Delete `get_recent_autopsy_insights()` from `coach_recommendations.py` (lines 310-336).
Import the version from `llm_recommendations_module.py` instead:
```python
from llm_recommendations_module import get_recent_autopsy_insights
```
The `llm_recommendations_module.py` version extracts LEARNING INSIGHTS section (300-500 chars) and returns
`alignment_trend`. The weekly prompt build already formats the output correctly — the dict keys `count`, `avg_alignment`,
`latest_insights` are the same.

Note: The `llm_recommendations_module.py` version uses `days=3` default vs. `days=7` in the weekly path. The weekly call
passes `days=7` explicitly — confirm this parameter is passed through.

### 2-B: Add deviation_reason to autopsy insight queries (Finding 1-A)

**File:** `app/llm_recommendations_module.py:get_recent_autopsy_insights:~2348`

Add `deviation_reason` to the SELECT and include in the return dict:
```sql
SELECT date, autopsy_analysis, alignment_score, deviation_reason, generated_at
```
Add to return:
```python
'reason_breakdown': {
    'physical': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'physical'),
    'external': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'external'),
    'unknown': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'unknown'),
}
```

Update the autopsy context block in `create_enhanced_prompt_with_tone()` and the weekly prompt in
`build_weekly_program_prompt()` to include the breakdown (e.g., "2 physical, 1 external, 1 unknown").

### 2-C: Inject deviation_log summary into daily prompt (Finding 1-B)

**File:** `app/llm_recommendations_module.py:create_enhanced_prompt_with_tone:~1044`

The weekly context block already has access to `week_ctx`. Add after the existing `weekly_context_block` assembly:
```python
deviation_log = week_ctx.get('deviation_log') or []
revision_pending = week_ctx.get('revision_pending') or False
if deviation_log or revision_pending:
    weekly_context_block += f"\nThis week's deviation count: {len(deviation_log)}"
    if revision_pending:
        weekly_context_block += " | ⚠️ Plan revision pending — a mid-week adjustment has been proposed."
```

---

## Phase 3 — Core Personalization Fix

*Replaces broken/misleading ACWR calibration with meaningful confidence metrics; removes dead code*

### 3-A: Remove dead ACWR sweet spot override from apply_athlete_model_to_thresholds() (Finding 4-A / 7-A)

**File:** `app/llm_recommendations_module.py:apply_athlete_model_to_thresholds:~1872`

The injury signal framework is entirely divergence-based. `acwr_sweet_spot_low/high` are orphaned fields from a
superseded design. The override block that reads them has never fired (requires `sweet_high` to be non-null, which never
happens). Remove the dead block:

```python
# REMOVE this block entirely:
confidence = model.get('acwr_sweet_spot_confidence') or 0.0
sweet_high = model.get('acwr_sweet_spot_high')
if confidence >= MIN_CONFIDENCE and sweet_high:
    calibrated['acwr_high_risk'] = float(sweet_high)
    changes.append(f"acwr_high_risk→{sweet_high:.2f}")
```

The divergence overrides below it (`divergence_overtraining`, `divergence_moderate_risk`) are correct per the framework
and stay unchanged.

Also remove references to `acwr_sweet_spot_low/high` from `get_athlete_model_context()` (~lines 2114-2115) — do not
display uncalibrated ACWR sweet spot values to the LLM as if they were personalized.

### 3-B: Implement meaningful confidence metric — Gap 6 (Finding 2-C / 4-C)

**File:** `app/llm_recommendations_module.py:update_athlete_model`

The injury signal framework (Gap 6) calls for replacing `acwr_sweet_spot_confidence` with two calibration-quality
counters: `div_low_n` (qualifying healthy days) and `threshold_n` (physical distress events).

**Step 1** — Track counts during computation.
In the existing `typical_divergence_low` block (~line 2268):
```python
if healthy_rows and len(healthy_rows) >= 5:
    div_low_n = len(healthy_rows)   # ADD
    # ... existing P20 computation unchanged ...
    updates['div_low_n'] = div_low_n  # ADD to updates dict
```

In the existing `divergence_injury_threshold` block (~line 2229):
```python
if distress_rows and len(distress_rows) >= 3:
    threshold_n = len(distress_rows)   # ADD
    # ... existing median computation unchanged ...
    updates['threshold_n'] = threshold_n  # ADD to updates dict
```

**Step 2** — Schema: add two columns (run in Cloud SQL Editor before deploying Phase 3):
```sql
ALTER TABLE athlete_models
  ADD COLUMN IF NOT EXISTS div_low_n INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS threshold_n INTEGER DEFAULT 0;
```

Also add both to `allowed_columns` in `db_utils.py:upsert_athlete_model` (~line 564).

**Step 3** — Update `MIN_INJECT_CONFIDENCE` gate.
```python
# Before
if confidence < MIN_INJECT_CONFIDENCE:
    return "ATHLETE MODEL: LEARNING ..."

# After
total_autopsies = model.get('total_autopsies', 0) or 0
if total_autopsies < 3:
    return "ATHLETE MODEL: LEARNING (building athlete model — insufficient data yet)"
```

### 3-C: Update athlete model context to reflect actual calibration state (Finding 4-B)

**File:** `app/llm_recommendations_module.py:get_athlete_model_context:~2120`

Replace the ACWR sweet spot lines with a calibrated-fields summary using `div_low_n` and `threshold_n`:

```
- Productive window edge: {div_low:.3f} ({f"calibrated from {div_low_n} healthy days" if div_low_n >= 5 else "population default — calibrating"})
- Breakdown threshold: {-div_injury:.3f} ({f"calibrated from {threshold_n} distress events" if threshold_n >= 3 else "population default — calibrating"})
```

---

## Phase 4 — Inter-Layer Coherence & Observability

### 4-A: Explain daily override of weekly plan (Finding 5-A)

**File:** `app/llm_recommendations_module.py:create_enhanced_prompt_with_tone`

Add to the `### RESPONSE INSTRUCTIONS` section after the CRITICAL REQUIREMENTS block:
```
PLAN OVERRIDE RULE: If today's prescribed session (from WEEKLY CONTEXT) conflicts with your recommendation (e.g., you
recommend recovery but the plan calls for a key session), explicitly state the conflict and safety rationale in your
DAILY RECOMMENDATION section. Example: "Your plan calls for [X] today, but [metric reason] means today should be [Y]
instead."
```

### 4-B: Fetch prior week deviation log for weekly prompt (Finding 5-B)

**File:** `app/coach_recommendations.py:build_weekly_program_prompt:~493`

Add alongside the existing `prior_synthesis` query:
```python
prior_deviation_rows = execute_query(
    """
    SELECT deviation_log, week_start_date
    FROM weekly_programs
    WHERE user_id = %s
      AND week_start_date < %s
      AND deviation_log IS NOT NULL
    ORDER BY week_start_date DESC
    LIMIT 1
    """,
    (user_id, target_week_start),
    fetch=True
)
prior_deviation_log = prior_deviation_rows[0]['deviation_log'] if prior_deviation_rows else []
```

Inject into the **LAST WEEK IN REVIEW** section:
```
f"Prior week deviations: {len(prior_deviation_log)} logged" if prior_deviation_log else "No deviation log available."
```

### 4-C: Agentic path context parity audit (Finding 6-A)

**File:** `app/llm_context_tools.py` (read-only audit first)

1. Read `TOOL_DEFINITIONS` to confirm which context categories are available as tools.
2. Compare against standard path's guaranteed injections: athlete model, morning readiness, filtered training guide, weekly context, pattern flags, 7-day activity summary.
3. For any context not available as a tool, add it to `system_turn1` as static context.

Do not add tools blindly. Goal is parity, not feature expansion. Must happen before expanding the `agentic_context` feature flag.

### 4-D: Add observability to structured output (Finding 4-C)

**File:** `app/llm_recommendations_module.py:create_enhanced_prompt_with_tone`

In the `<structured_output>` template (~line 1183), add to the meta block:
```json
"athlete_model_injected": false,
"div_low_n": 0,
"threshold_n": 0,
"divergence_overtraining_threshold": 0.0
```
Note: no ACWR field — Phase 3-A removes ACWR personalization. These fields reflect the divergence-only threshold state.

In `generate_recommendations()`, extract and log these values from `sections['structured_output']`.

---

## Files Modified

| File | Phase | Changes |
|------|-------|---------|
| `app/llm_recommendations_module.py` | 1, 2, 3, 4 | Silent failure fallbacks; trend logic; fallback flag; agentic tone; deviation_reason in query; deviation_log in prompt; remove dead ACWR override; add div_low_n/threshold_n tracking; update model context; plan override instruction; structured output meta |
| `app/coach_recommendations.py` | 2, 4 | Remove duplicate `get_recent_autopsy_insights()`; import from llm module; prior-week deviation log fetch |
| `app/db_utils.py` | 3 | Add `div_low_n`, `threshold_n` to `allowed_columns` in `upsert_athlete_model()` |
| `app/strava_app.py` | 1 | Check `is_fallback` flag before calling `update_athlete_model()` in `save_journal_entry()` |

**Schema change required for Phase 3** (run in Cloud SQL Editor before deploying Phase 3):
```sql
ALTER TABLE athlete_models
  ADD COLUMN IF NOT EXISTS div_low_n INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS threshold_n INTEGER DEFAULT 0;
```

---

## Sequencing Recommendation

- **Phase 1** — safe to ship immediately. No schema changes, all defensive fixes.
- **Phase 2** — prompt context quality. Verify via logs that `deviation_reason` appears in autopsy context block.
- **Phase 3** — run SQL migration first, then deploy. Verify `div_low_n`/`threshold_n` non-zero in `athlete_models` after next autopsy. Confirm inject gate in `get_athlete_model_context()` uses `total_autopsies < 3` (not confidence field).
- **Phase 4** — additive. Agentic audit (4-C) must happen before expanding the `agentic_context` feature flag.

## Verification

1. Run mock server, trigger recommendation generation via Coach page.
2. Check Cloud Logging (`llm_recommendations` logger) — confirm no silent exception swallows.
3. After Phase 3: inspect `athlete_models` in Cloud SQL Editor — `div_low_n` and `threshold_n` non-zero after qualifying autopsy run.
4. After Phase 2: search prompt logs for `deviation_reason` to confirm breakdown appears in autopsy context block.
