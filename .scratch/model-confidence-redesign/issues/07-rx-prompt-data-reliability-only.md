# 07 — Rx prompt cites Data Reliability alone

**What to build:** The daily Rx's confidence-reporting language currently states a blended "model confidence % and autopsy count" as two bolted-together facts. Rewrite it to cite Data Reliability (02) alone, in plain language tied to what it actually measures (e.g. "78% — your HR, activity history, and journaling are solid, trust this fully" vs. "45% — light on recent journaling, treat today's call as an estimate"). Autopsy count no longer appears as a separate clause — it's already folded into Data Reliability (ticket 02).

Specification Clarity does not appear in daily Rx prose at all going forward — it's a precondition resolved upstream by the season-goal floor of the Adequate Context Gate (04, merged from the original ticket 05) before generation ever starts, so there's nothing left to report about it per-day once that gate exists.

**Fix location, verified (2026-09-05 review finding) — narrower than "one prompt location," but not a multi-site hunt either:**
the literal string `"- Model Confidence: {pct}%"` occurs exactly once in the codebase, inside `get_athlete_model_context()` (llm_recommendations_module.py:4281-4285). The risk this ticket originally missed: that function is called from **two independent places** — inside `assemble_daily_context()` (the daily-Rx seam, 3 call sites) AND directly from `coach_recommendations.py:932` (the weekly-program builder), bypassing the daily seam entirely. If ticket 06 stops persisting the old `model_confidence_pct` composite, the weekly builder's copy of this string would permanently read "building (not yet computed)" right next to the daily Rx's new Data Reliability language — two contradictory confidence statements. Because both consumers funnel through this one function, the fix belongs in `get_athlete_model_context()` itself, not scattered across callers — but confirm both consumers are exercised by whatever test/spot-check this ticket adds, don't assume the daily path alone proves it.

**Blocked by:** 02, 04 (Data Reliability must exist to be cited; the Adequate Context Gate's season-goal floor must exist before it's safe to drop Specification Clarity from daily narration — otherwise a user with an unclear target loses the only place that was ever mentioned to them)

**Status:** ready-for-agent

- [ ] Generated Rx text cites Data Reliability alone, not the old blended model-confidence/autopsy-count phrasing
- [ ] The weekly program prompt (coach_recommendations.py:932, via the same `get_athlete_model_context()` call) also cites Data Reliability alone — not left showing the old/placeholder text after ticket 06 retires the composite
- [ ] Specification Clarity is not mentioned anywhere in daily Rx prose
- [ ] Spot-checked against real generations at both ends of the Data Reliability spectrum (high and low) to confirm the language reads correctly at each end, not just at a mid-range value
