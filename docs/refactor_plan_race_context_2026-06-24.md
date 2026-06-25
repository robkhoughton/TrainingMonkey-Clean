# Refactor Plan — Single Source of Truth for Race Context

**Date:** 2026-06-24
**Author:** Claude (Opus 4.8) + Rob
**Trigger:** "No race on the calendar" bug recurred despite two prior "permanent" fixes (June 9 2026). Root cause was structural, not a one-off.

---

## Goal

Make race context **impossible to omit or mis-shape** in any coaching prompt. Today, every prompt builder re-derives "the athlete's races" independently, through different mechanisms, with three different field names. A fix to one path does not propagate — so every new prompt path silently reintroduces the same bug.

**Design principle:** one canonical builder for race context + one canonical field name for "weeks to race". Prompt builders *call* it; they never re-assemble it.

---

## Root cause evidence (why this keeps recurring)

### 1. Field-name drift — same value, three names

| Name | Where | Notes |
|------|-------|-------|
| `weeks_until_race` | `_calculate_training_stage()` (strava_app.py:14543), `get_current_training_stage` has-race path | The canonical computed value |
| `weeks_to_race` | `get_current_training_stage` **no-race path** (coach_recommendations.py:287), readers at general.py:80, llm_recommendations:1670, coach_recommendations:1043 | The bug magnet |
| `weeks_to_a_race` | `strategic_summary` JSONB (persisted), llm_context_tools.py, db_utils.py:1511 | Persisted snapshot |

**The landmine:** `get_current_training_stage()` returns `weeks_to_race: None` when there is **no** race (line 287) but `weeks_until_race: <n>` when there **is** one (line 304). Any caller reading `.get('weeks_to_race')` gets `None` *exactly when a race exists*. This identical bug currently lives in **4 places**:
- `llm_recommendations_module.py:4225` — daily autopsy prompt (**fixed 2026-06-24**)
- `llm_recommendations_module.py:1670` — daily non-autopsy prompt
- `chat/context_loaders/general.py:80` — chat coach
- `coach_recommendations.py:1043` — **weekly program** generation prompt (`Weeks to Primary Race: N/A`)

### 2. Race-goal injection is duplicated, not shared

`get_race_goals()` is queried/formatted in **5+ independent sites** in `llm_recommendations_module.py` alone (lines 197, 1753, 1909, 1918, 1953), plus the autopsy builder originally used none of them. There are also **two** `get_race_goals` implementations (coach_recommendations.py:61 returns a list; llm_context_tools.py:88 returns a dict) and **three** training-stage computers (coach_recommendations.get_current_training_stage, strava_app.py:14501 `_calculate_training_stage`, strava_app.py:6551-6731, llm_context_tools.py:115).

### 3. No guardrail test

Two fixes shipped without a test asserting "race appears in the daily prompt." That is why both missed the path the user actually hits.

---

## Plan (phased — each phase ships independently)

### Phase 0 — Tactical fix ✅ DONE (2026-06-24)
- `create_autopsy_informed_decision_prompt`: added unconditional `### RACE GOALS` block + fixed `weeks_to_race`→`weeks_until_race`. Verified end-to-end (narrative now states "12 weeks out from Mountain Lakes 100").
- **Needs deploy** to reach production.

### Phase 1 — Normalize the field name ✅ DONE (2026-06-25)
**One key everywhere: `weeks_until_race`.** Shipped with the Phase 4 contract test (`app/tests/test_training_stage_field_contract.py`, 3 passing). Fixed the 3 unaddressed mis-keyed readers (chat coach, non-autopsy daily, weekly-program prompt) + normalized the `get_current_training_stage` no-race path. Needs deploy. The strava_app.py HTTP training-stage endpoint still returns `weeks_to_race` to the frontend — that is a separate API contract, deferred to Phase 3.

1. `coach_recommendations.py` `get_current_training_stage` no-race path (line 285-290): return `weeks_until_race: None` (not `weeks_to_race`), and align `stage` casing to lowercase `'base'` to match the has-race path. Add `priority: None`, `details` for shape parity.
2. Update readers that query the wrong key against this function's output:
   - `llm_recommendations_module.py:1670` → `weeks_until_race`
   - `chat/context_loaders/general.py:80` → `weeks_until_race`
   - `coach_recommendations.py:843` → drop the defensive `or weeks_to_race` (no longer needed)
   - `coach_recommendations.py:1043` (weekly program prompt) → `weeks_until_race`
3. Leave `weeks_to_a_race` as the **persisted** `strategic_summary` key (renaming a JSONB key orphans old rows). Document it as the persisted snapshot; live code reads `weeks_until_race` from `get_current_training_stage` as the authority, `strategic_summary.weeks_to_a_race` only as fallback (matches the 2026-04-28 server-computed decision).
4. `workout_library.py` uses `weeks_to_race` as an internal **function parameter** — leave as-is (not a dict-key contract); optionally rename for consistency.

**Test:** assert `get_current_training_stage(user_with_A_race)` and `(user_with_no_race)` both expose `weeks_until_race`.

### Phase 2 — Canonical race-context builder
Add to `coach_recommendations.py`:

```python
def build_race_context_block(user_id: int, target_date) -> str:
    """Single source of truth for race context in coaching prompts.
    Returns a prompt-ready string: TODAY-IS-RACE-DAY block (if applicable),
    then the ### RACE GOALS upcoming-races block. Always safe to inject.
    """
```

It composes the existing primitives (`get_race_on_date`, `get_race_goals` filtered to upcoming, `format_race_goals_for_prompt`) so behavior is unchanged — just centralized.

Replace ad-hoc injections with a single call in each builder:
- `create_autopsy_informed_decision_prompt` (replaces the 2 blocks added in Phase 0 + race_day_context)
- `create_enhanced_prompt_with_tone` (replaces the 4 redundant sites: 1753, 1909/1918, 1953, 1930)
- `coach_recommendations.py` weekly program prompt (~line 1030)
- `chat/context_loaders/general.py` and `training_plan.py`

Net: ~10 race-assembly sites collapse to one function with 4 call sites.

### Phase 3 — Consolidate duplicate primitives (stretch / separate session)
- Make `llm_context_tools.get_race_goals` delegate to `coach_recommendations.get_race_goals` (one query, one shape).
- Unify the training-stage computers on `get_current_training_stage`. Higher blast radius (touches the training-stage API endpoint at strava_app.py:6551-6731 and 14501) — do only with explicit regression testing of the Coach/Season page.

### Phase 4 — Guardrail test (the missing safety net)
Integration test, one per daily prompt builder: for a fixture user with an A-race, build the prompt and assert the race name + a numeric "weeks" value appear, and that no "no race" phrasing is produced. This is what would have caught both prior misses.

---

## Risk & sequencing

- **Phase 1** is low-risk and independently shippable — do it next, it kills the bug class in the 3 unfixed readers (chat + non-autopsy daily + weekly program).
- **Phase 2** is the real consolidation; medium risk because it touches all daily/weekly/chat prompts. Ship after Phase 1, with the Phase 4 test in place first.
- **Phase 3** is optional cleanup; defer to its own session.
- All phases are local code — **Rob deploys**. No DB migration required (no column renames; `weeks_to_a_race` JSONB key preserved).

## Recommended order
1. Deploy Phase 0 (stops the live contradiction today).
2. Phase 1 + Phase 4 test together.
3. Phase 2.
4. Phase 3 when convenient.
