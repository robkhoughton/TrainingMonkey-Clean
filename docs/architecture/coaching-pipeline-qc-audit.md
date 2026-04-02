# YTM Coaching Pipeline — QC Audit Report
*Audit date: 2026-03-22 | Code snapshot: commit 3d4379e*

---

## Summary

The pipeline is structurally sound at the individual layer level but has three systemic failures that limit its ability to actually learn about the athlete over time. The most critical: the ACWR sweet spot personalization path (`acwr_sweet_spot_low/high`) is permanently broken — the fields are read but never written, so `apply_athlete_model_to_thresholds()` never fires its primary override. The agentic path (production-gated via feature flag) injects materially less context than the standard path with no parity guarantee. Several silent exception swallows omit context without telling the LLM what it doesn't have.

---

## Findings

### 1. Input Completeness

**Finding 1-A: `deviation_reason` is never injected into any prompt**
The `ai_autopsies` table stores `deviation_reason` (physical/external/unknown) via Phase C. Both `get_recent_autopsy_insights()` implementations query only `alignment_score`, `autopsy_analysis`, and `date`. The reason why an athlete deviated — the most actionable signal — never reaches the weekly program or daily recommendation.
- Location: `coach_recommendations.py:get_recent_autopsy_insights:316-320`, `llm_recommendations_module.py:get_recent_autopsy_insights:2348-2351`
- Severity: **medium**
- Impact: Weekly program and daily recommendation cannot adapt differently to physical distress vs. external causes vs. volitional misses. All deviations appear equivalent.
- Recommendation: Add `deviation_reason` to both `get_recent_autopsy_insights()` queries and include a breakdown (e.g., "2 physical, 1 external") in the autopsy learning section of both prompts.

---

**Finding 1-B: `deviation_log` and `revision_pending` fetched but not injected into daily prompt**
`get_current_week_context()` returns `deviation_log` and `revision_pending`. The `create_enhanced_prompt_with_tone()` function reads only `strategic_summary` from the returned dict. If the week has accumulated multiple deviations or has a pending revision, the daily recommendation LLM doesn't know.
- Location: `llm_recommendations_module.py:create_enhanced_prompt_with_tone:1002-1051`
- Severity: **medium**
- Impact: Daily recommendation cannot escalate caution in response to a pattern of deviations within the week. A pending revision proposal exists but doesn't inform today's session.
- Recommendation: Append a compact weekly deviation summary to `weekly_context_block` when `deviation_log` is non-empty or `revision_pending` is True.

---

**Finding 1-C: Morning readiness signals absent from weekly program**
`sleep_quality` and `morning_soreness` are injected into the daily recommendation via `readiness_context` but the weekly program's `get_recent_journal_observations()` only retrieves `energy_level`, `rpe_score`, `pain_percentage`, `notes`.
- Location: `coach_recommendations.py:get_recent_journal_observations:285-292`
- Severity: **low**
- Impact: Weekly planning is blind to chronic sleep disruption patterns.
- Recommendation: Add `sleep_quality`, `morning_soreness` to `get_recent_journal_observations()` and include an aggregate in the weekly prompt.

---

### 2. Signal Quality

**Finding 2-A: Two divergent `get_recent_autopsy_insights()` implementations with different quality levels**
`coach_recommendations.py` version truncates raw autopsy text to 200 chars (`[:200]`), typically cutting mid-ALIGNMENT ASSESSMENT and discarding LEARNING INSIGHTS entirely. `llm_recommendations_module.py` version extracts the LEARNING INSIGHTS section specifically (300-500 chars). The weekly program uses the worse implementation.
- Location: `coach_recommendations.py:329`, `llm_recommendations_module.py:2374-2386`
- Severity: **medium**
- Impact: Weekly program receives a fragment that almost never includes the actionable coaching takeaways.
- Recommendation: Replace `coach_recommendations.py:get_recent_autopsy_insights()` with the version from `llm_recommendations_module.py`, or unify into a shared utility.

---

**Finding 2-B: Alignment trend requires strict monotonicity — will nearly always classify as 'stable'**
`update_athlete_model()` classifies trend as 'improving' only for `score[0] > score[1] > score[2]` (strictly monotone, DESC). Any non-monotone sequence — including meaningful directional movement like [8, 6, 9] — classifies as 'stable'.
- Location: `llm_recommendations_module.py:update_athlete_model:2197-2204`
- Severity: **low-medium**
- Impact: Alignment trend signal will be 'stable' for the vast majority of realistic score sequences, eliminating its discriminative value.
- Recommendation: Replace strict monotonicity with a directional test: e.g., `score[0] > score[2]` (most recent vs. oldest, regardless of middle value).

---

**Finding 2-C: `acwr_sweet_spot_confidence` measures autopsy count, not ACWR calibration quality**
The field increments 0.05 per autopsy regardless of ACWR data content. More critically, `acwr_sweet_spot_low` and `acwr_sweet_spot_high` are never set by any code path (see Finding 4-A). Confidence of 60% in an undefined sweet spot is meaningless.
- Location: `llm_recommendations_module.py:update_athlete_model:2181-2182`
- Severity: **medium** (the broken calibration path is the higher-severity issue)
- Impact: LLM may overtrust injected ACWR sweet spot values that are identical to defaults.
- Recommendation: Rename to `athlete_model_confidence`. Separately implement ACWR sweet spot computation (see Finding 4-A).

---

### 3. Silent Failures

**Finding 3-A: Weekly context exception produces empty string, not a legible fallback**
When `get_current_week_context()` raises an exception, the except block sets `weekly_context_block = ""`. The `[No weekly plan active]` fallback is only set when the query succeeds but returns no `strategic_summary`. Exception path → empty string → LLM receives no weekly context and no signal it was expected.
- Location: `llm_recommendations_module.py:create_enhanced_prompt_with_tone:1057-1059`
- Severity: **medium**
- Impact: On a DB transient error, the daily recommendation silently drops weekly alignment. LLM proceeds as if there's no plan.
- Recommendation: In the `except` block, set `weekly_context_block` to `"\n### WEEKLY CONTEXT\n[Weekly context unavailable — recommendation generated from current metrics only]\n"`.

---

**Finding 3-B: `get_athlete_model_context()` exception and below-threshold case are indistinguishable**
Exception path returns `""` (line 2133). Below-threshold path returns the LEARNING notice. On persistent model fetch failures, the LLM runs on population defaults without any signal that the athlete model exists.
- Location: `llm_recommendations_module.py:get_athlete_model_context:2132-2134`
- Severity: **low-medium**
- Recommendation: In the except block, return the LEARNING notice rather than empty string.

---

**Finding 3-C: Fallback autopsy hardcodes alignment score = 6, polluting the athlete model**
`generate_basic_autopsy_fallback_enhanced()` always sets `alignment_score = 6`. This value is passed to `update_athlete_model()` and incorporated into `avg_lifetime_alignment` via 70/30 weighted average. Every AI failure inflates alignment by injecting a neutral score.
- Location: `llm_recommendations_module.py:generate_basic_autopsy_fallback_enhanced:2048`
- Severity: **medium**
- Impact: Repeated AI failures systematically bias the alignment model toward 6, suppressing sensitivity to real compliance patterns.
- Recommendation: Either skip the model update when using the fallback, or skip only the alignment update (increment `total_autopsies` and `confidence` but do not update `avg_lifetime_alignment`).

---

### 4. Feedback Loop Integrity

**Finding 4-A: `acwr_sweet_spot_low/high` are never computed — ACWR calibration path is broken** ⚠️ HIGH
`update_athlete_model()` computes `typical_divergence_low` and `divergence_injury_threshold` but never computes `acwr_sweet_spot_low` or `acwr_sweet_spot_high`. These fields are read in `apply_athlete_model_to_thresholds()` (line 1874) and `get_athlete_model_context()` (line 2115), but are only DB-level defaults. The condition `if confidence >= MIN_CONFIDENCE and sweet_high:` at line 1875 will never be True because `sweet_high` is always None.
- Location: `llm_recommendations_module.py:update_athlete_model:2137-2338` (confirmed by absence of any assignment), `apply_athlete_model_to_thresholds:1874-1876`
- Severity: **high**
- Impact: The primary athlete-specific ACWR threshold personalization is permanently inoperative. All athletes receive the style-based population threshold. The context block presents `acwr_sweet_spot` values as calibrated when they are not.
- Recommendation: In `update_athlete_model()`, compute ACWR sweet spot from healthy days: use P20 of ACWR values as `acwr_sweet_spot_low`, P80 as `acwr_sweet_spot_high`. Require N >= 10 qualifying days before updating. Healthy day criteria mirror the existing `typical_divergence_low` query.

---

**Finding 4-B: Athlete model injects "personalized" values that are defaults for the first ~20 autopsies**
Confidence reaches 0.15 (inject threshold) at autopsy #3. `typical_divergence_low` requires 5+ healthy days; `divergence_injury_threshold` requires 3+ physical events. Values shown to the LLM may be population defaults indistinguishable from calibrated values.
- Location: `llm_recommendations_module.py:get_athlete_model_context:2120-2128`
- Severity: **medium**
- Recommendation: Add a `calibrated_fields` note to the context block listing which fields have been updated beyond defaults vs. which remain population values.

---

**Finding 4-C: No mechanism to verify whether athlete model injection changes recommendation output**
No A/B testing, output comparison, or logging differentiates recommendations generated with vs. without athlete model context. The feedback loop runs but its downstream effect is unmeasured.
- Location: Pipeline-wide
- Severity: **low** (observability gap)
- Recommendation: Log `athlete_model_context_injected: bool` and threshold values used in `structured_output.meta`.

---

### 5. Inter-Layer Coherence

**Finding 5-A: Daily recommendation can silently override weekly plan without athlete-facing explanation**
When ACWR spikes, the daily generator triggers `high_acwr_risk` and recommends recovery even if the weekly plan prescribes a key session. The LLM is told "safety takes precedence" but the athlete receives no explanation for the conflict.
- Location: `llm_recommendations_module.py:create_enhanced_prompt_with_tone:1044-1051`
- Severity: **medium**
- Impact: Conflicting guidance without explanation erodes athlete trust.
- Recommendation: Add an output instruction: when today's prescribed session conflicts with the daily recommendation, explicitly state the override and safety rationale.

---

**Finding 5-B: Weekly program omits prior week deviation pattern**
The weekly prompt includes `prior_synthesis` but the prior week's `deviation_log` is not fetched. If the prior week had 3 Tier-2 deviations due to injury, the weekly program is unaware.
- Location: `coach_recommendations.py:build_weekly_program_prompt:493-507`
- Severity: **medium**
- Recommendation: Fetch and summarize the prior week's `deviation_log` (count, most frequent reason) alongside the prior synthesis.

---

### 6. The Agentic Path

**Finding 6-A: Agentic path is production-gated but injects materially less guaranteed context** ⚠️ HIGH
Confirmed in production via `_is_feature_enabled('agentic_context', user_id)` in both async job route and direct generation path (`strava_app.py:2194, 6468`). Turn 1 contains only 4 metrics. Standard path guarantees: tone instructions, athlete model context, morning readiness, filtered training guide, weekly context block, pattern flags, 7-day activity summary. Agentic path gets none of these unless the model requests them via tools. `TOOL_DEFINITIONS` in `llm_context_tools.py` not audited — tool availability unconfirmed.
- Location: `llm_recommendations_module.py:generate_recommendations_agentic:3305-3330`
- Severity: **high**
- Impact: Users on the agentic path receive recommendations from minimal context. The LLM must discover what context exists and ask for it.
- Recommendation: Audit `TOOL_DEFINITIONS`. Add tone instructions to `system_turn1`. Run parity comparison (same user, same day) before expanding the flag.

---

**Finding 6-B: Agentic path does not inject tone instructions**
No `tone_instructions` from `get_user_coaching_spectrum()` in either turn. Athletes configured for specific coaching styles receive generic tone.
- Location: `llm_recommendations_module.py:generate_recommendations_agentic:3307-3330`
- Severity: **medium**
- Recommendation: Add tone instructions to `system_turn1`.

---

### 7. Calibration vs. Defaults

**Finding 7-A: `acwr_sweet_spot_low/high` — defaults, unreachable calibration path**
(See Finding 4-A.) Defaults: 0.8/1.2. No code path updates these values.

**Finding 7-B: Fixed 70/30 weighted average regardless of model maturity**
Early autopsies (1-5) give new scores only 30% weight, anchoring toward bootstrapped default of 5.0. A genuinely poor compliance athlete would not reach avg≈3 in the model until ~10 autopsies.
- Location: `llm_recommendations_module.py:update_athlete_model:2178`
- Severity: **low**
- Recommendation: Use count-adaptive weighting: equal 50/50 for `total_autopsies < 5`, then stable 70/30 thereafter.

---

## Priority Order

Ranked by impact on coaching quality:

| # | Finding | Severity | Description |
|---|---------|----------|-------------|
| 1 | 4-A / 7-A | **High** | ACWR sweet spot never computed — primary personalization path broken |
| 2 | 6-A | **High** | Agentic path (production) context parity unverified |
| 3 | 2-A | Medium | Weekly program gets 200-char raw truncation instead of LEARNING INSIGHTS |
| 4 | 3-C | Medium | Fallback autopsy hardcodes score=6, biases alignment model |
| 5 | 1-A | Medium | `deviation_reason` never injected into any prompt |
| 6 | 1-B | Medium | `deviation_log` / `revision_pending` not surfaced in daily prompt |
| 7 | 3-A | Medium | Weekly context exception → empty string instead of legible fallback |
| 8 | 5-A | Medium | Daily override of weekly plan not communicated to athlete |
| 9 | 4-B / 2-C | Medium | Model context presents defaults as calibrated; confidence label misleads |
| 10 | 6-B | Medium | Agentic path missing tone injection |
| 11 | 5-B | Medium | Prior week deviation pattern absent from weekly program |
| 12 | 2-B | Low-Med | Alignment trend strict monotonicity → almost always 'stable' |
| 13 | 3-B | Low-Med | Athlete model exception vs. below-threshold indistinguishable |
| 14 | 7-B | Low | Early alignment model biased toward 5.0 by fixed 70/30 weights |
| 15 | 4-C | Low | No observability on whether athlete model changes output |
| 16 | 1-C | Low | Morning readiness absent from weekly program |
