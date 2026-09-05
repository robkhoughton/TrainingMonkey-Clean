# 04 — Data Reliability gates Rx generation

**What to build:** When a user's Data Reliability score (ticket 02) is below an agreed threshold, Rx generation is skipped entirely — no LLM call is made — and the user sees a specific message naming which inputs are thin (from the score's component breakdown) and how to improve them, instead of receiving a metrics-driven Rx built on fabricated or near-zero inputs (e.g. an ACWR/divergence verdict computed on a near-empty activity history).

This is the direct answer to the original premise driving this whole redesign: don't prescribe training in the absence of quality context.

**Blocked by:** 02 (Data Reliability score must exist and be validated first)

**Status:** ready-for-agent

**Enforcement seam — named explicitly after a review pass (2026-09-05), do not assume one call site is enough:**
this repo has been burned by this exact pattern twice before (a legacy generator surviving a migration; a fix landing in one code path and not a sibling one). Verified entry points into Rx generation, as of this ticket:
- `assemble_daily_context()` (llm_recommendations_module.py:1814) — the shared context seam; called from 3 sites in that file (lines 2656, 4921, 5666). This is where `_load_coaching_context()` already lives per `.claude/CLAUDE.md`, and `app/tests/test_daily_context.py` already fails the build if a builder stops consuming a shared signal — the gate almost certainly belongs here, reusing that same guarantee.
- `generate_recommendations_agentic()` — **explicitly flagged in `.claude/CLAUDE.md` as outside the seam already**, needing a direct check. Called from `/cron/weekly-comprehensive` (strava_app.py:7044).
- `generate_activity_autopsy_enhanced()` — **also explicitly flagged as outside the seam**, needing a direct check.
- `/cron/daily-recommendations` (strava_app.py:6823) — the daily cron entry point; confirm what it calls and whether that path reaches the seam.
- `/api/llm-recommendations/generate` (strava_app.py:2296, manual/on-demand generation) — confirm this path too.

Before implementing: confirm which of these actually need their own gate check vs. which already route through `assemble_daily_context()` by construction, then add an explicit test asserting no generator can bypass the gate — mirroring how `test_daily_context.py` already guards the coaching-context seam.

**Double-gate precedence with ticket 05 — decide before building either (2026-09-05 review finding):**
tickets 04 and 05 are independent hard blocks on Rx generation, but neither originally said what the user sees when **both** fail simultaneously — and that's not an edge case, it's the default state for a brand-new user (no activity history, no journal, no HRV baseline, AND no season goal, all on day one). Decide and document an explicit precedence rule here and in ticket 05 before implementing either — e.g. does the season-goal gate (05) take priority since it's a one-time setup action, with the Data Reliability message (04) only shown once a goal exists but data is still thin? Whatever the rule, a brand-new user must see ONE coherent blocking message, not two contradictory or stacked ones.

- [ ] Below-threshold users are blocked from Rx generation entirely — verified no LLM call occurs, across every entry point listed above (not just the daily seam)
- [ ] Blocking message names the specific weak component(s) from the score breakdown, not a generic "insufficient data" message
- [ ] Above-threshold users see no change in behavior
- [ ] Setting/improving the weak input (e.g. journaling again, syncing recent activity) and re-requesting a Rx unblocks it once the score crosses the threshold
- [ ] A user failing both this gate and ticket 05's season-goal gate simultaneously sees the single, precedence-resolved message decided above — not both, not neither

**Open question — do not decide silently, confirm with the user:**
- The actual threshold value. Should be set from ticket 02's real-account validation data, not chosen blind. An earlier session draft worked out threshold candidates against the *old* 8-component composite (~20–22%, at the point where HR calibration + activity history both became real) — that arithmetic doesn't carry over directly to the new decay-weighted component set and needs to be redone.
