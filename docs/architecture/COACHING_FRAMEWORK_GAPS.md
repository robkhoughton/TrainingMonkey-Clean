# YTM Coaching Framework — Gaps Report

**Purpose:** Track gaps between YTM's current capabilities and the ideal coaching framework for trail runners 60+. Updated layer by layer.

---

## Layer 1 — Athlete Profile

### What Exists

| Data Point | Location |
|---|---|
| Race goals (name, date, type, priority A/B/C, target time, elevation) | Coach > Race Goals |
| Race history (past results, distance, finish time) | Coach > Race History |
| Weekly availability (days, hours, long run days) | Coach > Training Schedule |
| Supplemental training (strength, mobility, cross-training) | Coach > Training Schedule |
| Fixed constraints (free text) | Coach > Training Schedule |
| Age (birth month/year) | Settings > Profile |
| Gender | Settings > Profile |
| Coaching tone (casual/supportive/direct/analytical) | Settings > Coaching |
| Recommendation style (conservative → aggressive) | Settings > Coaching |
| ACWR alert threshold | Settings > Coaching |
| Injury risk alerts on/off | Settings > Coaching |
| Experience level (beginner/intermediate/advanced) | Settings (users table) — injected into daily prompt, not weekly program |

### Gaps

| Gap | Priority | Rationale |
|---|---|---|
| Injury history (body part, type, recurrence) | HIGH | Most important long-term limiter for 60+; AI is blind to recurrence risk |
| Years running / training background | HIGH | Connective tissue capacity diverges from what fitness metrics show |
| Current injury or active pain flags | HIGH | Should suppress load or redirect training type immediately |
| Sleep quality baseline | MEDIUM | Chronic poor sleep = primary recovery limiter in this age group |
| Life stress baseline | MEDIUM | Changes total allostatic load available for training |
| Medications relevant to training | MEDIUM | Beta-blockers distort HR; NSAIDs mask pain; statins affect muscle recovery |
| Primary motivation / fear | LOW | Shapes coaching voice — "stay healthy" vs. "hit a time goal" |

---

## Prioritized Build Order

### Tier 1 — Quick Wins (hours each, no new data, no schema changes)

| # | Item | Layer | Notes |
|---|---|---|---|
| 1 | Inject age into coaching prompts | 5 | One function change in `create_enhanced_prompt_with_tone()` and `build_weekly_program_prompt()`. Age already in DB. Highest ROI per line of code. |
| 2 | Surface athlete model to user | 6 | Read-only panel on Coach page: ACWR sweet spot, confidence %, alignment trend. No backend work. |
| 3 | Surface confidence / LEARNING state | 6 | Show "Still learning — X autopsies" when <15% confidence. Pair with #2. Also show in journal metapanel. |

### Tier 2 — Medium Effort (days each, data exists, minimal schema changes)

| # | Item | Layer | Notes |
|---|---|---|---|
| 4 | Weekly intensity distribution | 2 | SQL rollup of zone times → % easy/moderate/hard over 7 and 28 days. New API endpoint + dashboard component. |
| 5 | Back-to-back hard session detection | 5 | Add check in `analyze_pattern_flags()` using existing `workout_classification`. Backend only. |
| 6 | Weekly minimum easy day guardrail | 5 | Count easy/recovery days in rolling 7-day window. Pair with #5, same function. |
| 7 | Extract pain location in autopsy | 3 | Add `pain_location` to autopsy `structured_output` schema. Zero journal friction — extracted from notes by LLM at autopsy time. |
| 8 | Age-adjusted thresholds | 5 | Modify `get_adjusted_thresholds()` to apply age multiplier. Depends on #1. |

### Tier 3 — Structural Additions (1–2 weeks each)

| # | Item | Layer | Notes |
|---|---|---|---|
| 9 | Journal adoption / friction reduction | 3 | Post-sync modal: 3 fields, 10 seconds. Addresses 89% non-adoption. Highest practical impact in the project. |
| 10 | Injury history intake | 1 | New form: body part, injury type, recurrence, last occurrence. New columns on user profile. Inject as standing context block in all prompts. |
| 11 | Activity gap detection | 2 | SQL logic for gaps >5 days. Inject as pattern flag with return-to-load guidance. |
| 12 | End-of-week synthesis | 4 | Retrospective weekly narrative. New Saturday cron + prompt + UI card on Coach page. |

### Tier 4 — Dependent on Earlier Work

| # | Item | Depends On | Layer |
|---|---|---|---|
| 13 | Consistency score / boom-bust detection | #4 + #11 | 2 |
| 14 | Multi-week pattern detection | #13 | 4 |
| 15 | Athlete model enrichment | #10 + #4 | 4 |
| 16 | Transparency panel outside journal | #2 | 6 |
| 17 | Current pain / active injury flags | #10 | 1 |

### Side Fix (one line, do whenever in the file)
- Inject experience level into `build_weekly_program_prompt()` — currently only in daily recommendation prompt.

---

## Race Readiness Feature Spec

### The Metric

**Peak training week load miles ≥ race load miles, achieved by ~3 weeks before race day (taper start).**

Race load miles = `race_distance_miles + (race_elevation_feet / 750)`

This uses YTM's existing `total_load_miles` metric throughout — vert and mileage are never tracked separately. A 100-mile / 10,000ft race = 100 + 13.3 = **113.3 load miles** target peak week.

### The Projection

Given current chronic load and an ACWR ceiling, project the maximum safe weekly volume forward week by week:

```
max_week_N = ACWR_ceiling × chronic_N
chronic_N+1 = (chronic_N × 3 + max_week_N) / 4  # simplified 28-day rolling update
```

Chain until target is reached or weeks run out. Use the athlete's personal ACWR sweet spot upper bound from the athlete model (if confidence >15%); fall back to 1.3.

### Example Outputs

**On track:**
> "Your current chronic load is 65 load miles/week. Your A race target is 113 load miles. At your personal ACWR ceiling of 1.1, you can safely peak there by week 5. Taper starts in 6 weeks — you have a 1-week buffer. On track."

**Not achievable safely:**
> "At your ACWR ceiling of 1.1, the earliest you can safely reach 113 load miles is week 9. Your taper starts in 6 weeks. The target peak is not achievable in this training block. Current trajectory peaks at ~88 load miles. Options: accept the lower peak, or re-examine your race goal."

**Already there:**
> "Your training peak this block is 119 load miles — you've already exceeded your race target of 113. Taper when ready."

### Schema Gap

`race_goals` table is missing `distance_miles`. All other required data exists:
- `elevation_gain_feet` ✓ on race goals
- `total_load_miles` ✓ per activity (already used for ACWR)
- Chronic load (28-day avg) ✓ in `activities` table
- Personal ACWR sweet spot ✓ in `athlete_models`
- Weeks to taper ✓ from training stage calculation

### Build Placement

**Tier 3** — pairs naturally with injury history intake (#10). Both require a small schema addition and prompt injection. The readiness score should be injected into the weekly program prompt and surfaced as a card on the Coach page.

New item: **#10b — Race readiness score** (add `distance_miles` to race goals schema + projection function + Coach page display)

---

## Layer 2 — Activity Intelligence

### What Exists

| Signal | Status | Detail |
|---|---|---|
| Weekly volume (hours/miles trend) | ✓ | `seven_day_avg_load`, `twentyeight_day_avg_load` stored per activity |
| ACWR / training load ratio | ✓ | `acute_chronic_ratio` and `trimp_acute_chronic_ratio` computed and stored |
| Vertical gain | ✓ | `elevation_gain_feet` stored; `elevation_load_miles` computed |
| Per-activity HR zone times | ✓ | `time_in_zone1-5` stored per activity |
| Per-day workout classification | ✓ Partial | `classify_workout_by_hr_zones()` returns Easy/Moderate/Hard/VO2Max per day; injected into daily journal autopsy prompt only |

### Gaps

| Gap | Priority | Detail |
|---|---|---|
| Weekly intensity distribution | HIGH | Zone time data exists per activity but never aggregated into weekly % easy/moderate/hard. No 80/20 analysis. Most actionable signal for 60+ athletes who chronically over-intensify. |
| Consistency score / boom-bust detection | HIGH | No computation of training regularity over rolling windows. Pattern detection (solid block → gap → spike) is invisible to coaching engine. |
| Activity gap detection | MEDIUM | No logic to detect multi-day/week gaps in activity record. Gaps signal injury, illness, or life disruption — all affect safe return-to-load. |

**Key finding:** The intensity data exists — zone times are stored and zone classification works. The gap is upstream aggregation: data is never rolled up into a weekly intensity balance metric. This is a computation and display problem, not a data collection problem.

**Note:** Pace-at-HR efficiency trend was excluded — terrain and grade variability on trails makes this metric unreliable except on controlled track workouts.

---

## Layer 3 — Subjective Context

### What Exists

| Signal | Where | Detail |
|---|---|---|
| Sleep quality | Morning Readiness card | 1–5 slider, saved to `readiness` table |
| Morning soreness | Morning Readiness card | 0–100 slider |
| Energy level (pre-session motivation/readiness) | Journal table | 1–5 dropdown, per-day |
| RPE score | Journal table | 1–10 dropdown, per-day |
| Pain (global intensity) | Journal table | 0–100% in 20% increments |
| Free text notes | Journal table | Unstructured textarea |

### Gaps

| Gap | Priority | Detail |
|---|---|---|
| Pain location | HIGH | `pain_percentage` captures severity but not location. Achilles vs. hip vs. quad are completely different risk profiles for 60+ athletes. No body map or body-part field exists. |
| Adoption | HIGH | 11% of users have ever used the journal. Data model is right; collection mechanism isn't working. All fields are useless if not filled in. Dominant practical gap for the entire layer. |
| "What limited you" structured flag | LOW | Notes is free text. No structured capture of limiting factor (HR, legs, lungs, weather, injury). AI must infer from prose. |

**Key finding:** Layer 3 is architecturally more complete than Layer 2. The problem is behavioral, not structural. Priority is friction reduction (adoption), not new fields — except pain location, which is a real data gap.

---

## Layer 4 — Coaching Engine

### What Exists

| Component | Status | Detail |
|---|---|---|
| Weekly Program | ✓ | `generate_weekly_program()` — goal-driven, periodized, includes strategic context |
| Daily Recommendation | ✓ | `create_enhanced_prompt_with_tone()` — metrics, pattern flags, autopsy insights, tone, training guide injected |
| Post-activity Autopsy | ✓ | Alignment scoring + narrative; feeds athlete model |
| Athlete Model | ✓ | Persistent ACWR sweet spot, divergence threshold, alignment trend — confidence-gated |
| Pattern Flags | ✓ | `analyze_pattern_flags()` injected into daily and weekly prompts |
| Weekly Cron | ✓ | Regenerates recommendations for all active users weekly |

### Gaps

| Gap | Priority | Detail |
|---|---|---|
| End-of-week synthesis | HIGH | No user-facing retrospective weekly summary. Strategic context in weekly program is a forecast, not a review. Nothing tells the athlete "here's what happened this week, what patterns emerged, what we learned." |
| Athlete model is data-starved | HIGH | Tracks ACWR sweet spot and alignment metrics but holds no injury history, training background, or intensity balance. Layer 1 and Layer 2 gaps flow directly into this layer. Numerically sophisticated but contextually thin. |
| No multi-week pattern detection | MEDIUM | 28-day load window exists but no systematic detection of multi-week behavioral patterns (boom-bust cycles, chronic over-intensification, progressive fatigue accumulation across blocks). |

**Key finding:** Strongest layer in the app architecturally. Gap is not structural — the engine is operating with less context than it could. Layer 1 and Layer 2 gaps cascade here. One true structural gap: missing retrospective weekly synthesis.

---

## Layer 5 — 60+ Guardrails

### What Exists

| Guardrail | Status | Detail |
|---|---|---|
| Rest day enforcement | ✓ Partial | `days_since_rest_max` (6–8 days by recommendation style) → triggers `mandatory_rest` |
| ACWR risk ceiling | ✓ Partial | 1.2–1.5 by style; loose ramp rate proxy |
| Accumulated load detection | ✓ Partial | Divergence overtraining threshold |
| Chronic ACWR elevation | ✓ | 5+ consecutive high-ACWR days flagged |
| Consecutive negative divergence | ✓ | 5+ consecutive days flagged |
| Injury risk score | ✓ | Composite of ACWR + divergence + days_since_rest |

### Gaps

| Gap | Priority | Detail |
|---|---|---|
| Age not in prompts | CRITICAL | Age collected in Profile, used only for HR zone math. Never injected into any coaching prompt. AI makes all training decisions with no knowledge of athlete age. Single most impactful fix for 60+ coaching. |
| Back-to-back hard session detection | HIGH | `workout_classification` exists per day but never checked for consecutive hard days. Two Easy days and two Hard days in a row are treated identically. |
| Weekly minimum easy day requirement | HIGH | `days_since_rest` tracks only full rest days, not intensity. No guardrail ensures ≥2 easy/recovery days per week — most important structural protection for 60+. |
| Age-adjusted thresholds | HIGH | All thresholds are population-generic. No age-based modifier regardless of athlete's stated risk preference. |
| Bounce-back detector | LOW | Alignment scores could flag post-hard-block underperformance but never aggregated into a pattern. |

**Key finding:** Age-blind coaching engine is the dominant gap. Injecting age into prompt context is a small change with large coaching impact — it enables the AI to apply age-appropriate reasoning immediately without any other changes.

---

## Layer 6 — Coach Transparency

### What Exists

| Element | Where | Detail |
|---|---|---|
| Assessment category | Journal > RecommendationMetaPanel | Decision type (mandatory_rest, high_acwr_risk, normal_progression, etc.) |
| Primary driver | Journal > RecommendationMetaPanel | One-line dominant factor explanation |
| Divergence label | Journal > RecommendationMetaPanel | Severity + direction |
| Risk level | Journal > RecommendationMetaPanel | Low / Moderate / High |
| Autopsy-informed badge | Journal > RecommendationMetaPanel | Green badge when autopsy fed today's recommendation |
| "Why this recommendation?" | Journal > WhyRecommendationPanel | Full conversational explanation on demand |

### Gaps

| Gap | Priority | Detail |
|---|---|---|
| Athlete model invisible | HIGH | System has learned ACWR sweet spot, divergence range, alignment trend, confidence — none of it shown to user. Trust and adoption gap. Athletes who see the system learning about them engage more and journal more. |
| Confidence state not surfaced | HIGH | Model tracks 0–100% confidence and "LEARNING" state below 15%. Neither shown to users. Transparency about calibration state builds trust. |
| Transparency locked behind journal | MEDIUM | RecommendationMetaPanel only appears in journal view. 89% of users who don't journal see only the prose recommendation. Primary driver and assessment category should be accessible from dashboard. |

**Key finding:** Daily transparency layer is well-built. The gap is the athlete model — YTM has built a learning system but the athlete can't see it learning. Surfacing model state in a profile view would make the product feel like it genuinely knows you, directly addressing adoption.

---

## Complete Implementation Plan — All Gaps Filled

This plan assumes all 17 gap items and the race readiness feature (#10b) are built. Four sequential phases; each phase unlocks the next.

---

### Phase 1 — Age-Aware Coaching (Tier 1 + Side Fix)

**Scope:** No new data, no schema changes. Pure prompt and UI work.

| # | Item | Where | Notes |
|---|---|---|---|
| 1 | Inject age into coaching prompts | `llm_recommendations_module.py` | Add age (computed from birth_month/birth_year) to `create_enhanced_prompt_with_tone()` and `build_weekly_program_prompt()`. Age already in DB — one function change each. |
| SF | Inject experience level into weekly program | `coach_recommendations.py` | `build_weekly_program_prompt()` missing experience_level; already injected into daily prompt. Add it. |
| 2 | Surface athlete model panel | Coach page (React) | Read-only panel: ACWR sweet spot low/high, confidence %, alignment trend, total autopsies. No backend work — data already in athlete_models. |
| 3 | Surface confidence / LEARNING state | Athlete model panel + RecommendationMetaPanel | Show "Still learning — N autopsies to go" when confidence <15%. Show calibrated confidence % once above threshold. |

**Outcome:** Coach AI knows athlete age and experience. Athlete can see what the system has learned about them. Zero friction cost.

---

### Phase 2 — Richer Signal Processing (Tier 2)

**Scope:** Data exists; adds computation, pattern detection, and one schema field (pain_location extracted by LLM).

| # | Item | Where | Notes |
|---|---|---|---|
| 4 | Weekly intensity distribution | New API endpoint + dashboard component | SQL rollup of time_in_zone1-5 by week → % Easy / Moderate / Hard / VO2Max over 7 and 28 days. Display on Training Load dashboard. Feeds prompt as intensity_balance block. |
| 5 | Back-to-back hard session detection | `analyze_pattern_flags()` | Check workout_classification for consecutive Hard or VO2Max days in rolling 7-day window. Inject as pattern flag. |
| 6 | Weekly minimum easy day guardrail | `analyze_pattern_flags()` | Count Easy/Recovery days in rolling 7-day window. Flag if <2. Pair with #5 in same function pass. |
| 7 | Extract pain location in autopsy | `structured_output` schema | Add pain_location field to LLM autopsy output. Extracted from notes by the LLM — zero journal friction. Feeds Layer 1 active pain context once #10 exists. |
| 8 | Age-adjusted thresholds | `get_adjusted_thresholds()` | Apply age multiplier to ACWR ceilings and days_since_rest_max. Depends on #1. Example: ACWR ceiling 1.3 → 1.2 for age 65+. |

**Outcome:** Coaching engine detects intensity imbalance and consecutive hard days. Thresholds reflect athlete age. Pain location captured passively from existing notes.

---

### Phase 3 — Data Collection and Race Readiness (Tier 3)

**Scope:** Structural additions — schema changes, new data intake, new cron jobs.

| # | Item | Where | Notes |
|---|---|---|---|
| 9 | Journal adoption / friction reduction | Post-sync modal | 3 fields (energy, RPE, pain), 10 seconds. Trigger after Strava sync. Hardest problem in the app — 89% non-adoption rate. Highest practical impact per hour invested. |
| 10 | Injury history intake | New form + DB schema + prompt injection | Body part, injury type (strain/tendon/stress fracture/etc.), recurrence (yes/no), last occurrence date. New columns on user profile. Inject as standing context block in all prompts: "Injury history: left achilles tendinopathy, recurrent." |
| 10b | Race readiness score | `coach_recommendations.py` + Coach page | Add distance_miles to race_goals schema (only missing field). Projection: chain ACWR_ceiling × chronic forward weekly until target load miles reached or weeks run out. Use personal ACWR sweet spot if confidence >15%, else 1.3. Display as Coach page card: "On track / Not achievable safely / Already there." |
| 11 | Activity gap detection | `analyze_pattern_flags()` + SQL | Detect gaps >5 days in activity record. Inject as pattern flag with return-to-load guidance (ACWR ceiling 1.1 for re-entry week). |
| 12 | End-of-week synthesis | New Saturday cron + new prompt + Coach page card | Retrospective weekly narrative: what happened, patterns that emerged, what the system learned. Distinct from forward-looking weekly program. Coach page card showing current week's synthesis. |

**Outcome:** Athletes enter injury history once; AI applies it permanently. Journal friction addressed at the highest-leverage point. Race readiness answers the athlete's most important question. Gaps and load returns handled with appropriate caution.

---

### Phase 4 — Learning and Pattern Intelligence (Tier 4)

**Scope:** Builds on all prior phases. Depends on #4, #10, #11, #13 data existing.

| # | Item | Depends On | Notes |
|---|---|---|---|
| 13 | Consistency score / boom-bust detection | #4 + #11 | Compute training regularity score over rolling 4-week windows. Detect solid block → gap → spike patterns. Flag boom-bust cycles as pattern risk. |
| 14 | Multi-week pattern detection | #13 | Systematic detection of: chronic over-intensification (>4 weeks zone 3+), progressive fatigue accumulation across blocks, seasonal under-recovery. Inject into weekly program prompt. |
| 15 | Athlete model enrichment | #10 + #4 | Add injury history risk profile, intensity preference tendency, and consistency score to athlete_models. Feeds all downstream coaching. |
| 16 | Transparency panel outside journal | #2 | Surface RecommendationMetaPanel (assessment category, primary driver, divergence label, risk level) on dashboard for the 89% who don't journal. |
| 17 | Current pain / active injury flags | #10 | Use injury history + LLM-extracted pain_location (#7) to detect active issues. Suppress load or redirect training type when match found. |

**Outcome:** Coaching engine detects multi-week behavioral patterns and chronic fatigue accumulation. Athlete model holds full context: load history, injury history, intensity tendency, consistency. Transparency accessible to all users regardless of journal adoption.

---

### Full System State — All Phases Complete

When all 17 items + #10b are built, YTM provides:

**Coach AI knows:**
- Athlete age, experience level, injury history, training background
- Intensity balance (% easy/moderate/hard over 7 and 28 days)
- Active injury / pain signals (from autopsy extraction, not form friction)
- Race readiness trajectory (weeks to safely peak, not vague encouragement)
- Multi-week behavioral patterns: boom-bust, chronic over-intensification, block fatigue

**Guardrails enforce:**
- Age-adjusted ACWR ceilings and rest requirements
- Back-to-back hard session detection
- Minimum 2 easy days/week
- Return-to-load protocols after gaps
- Injury recurrence risk suppression

**Athlete sees:**
- What the system has learned (ACWR sweet spot, confidence %, alignment trend)
- Weekly intensity balance chart
- Race readiness status
- End-of-week synthesis narrative
- Transparency metadata from dashboard (not just journal)

**The one remaining behavioral gap — journal adoption (#9) — is addressed structurally, not by adding fields.**
