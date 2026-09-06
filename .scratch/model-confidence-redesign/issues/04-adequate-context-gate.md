# 04 — Adequate Context Gate on Rx generation

**Merged 2026-09-05** from the original tickets 04 (Data Reliability gates Rx) and 05 (season-goal hard gate), after a discussion surfaced that they were never two independent systems needing a precedence rule between them — they're three floor checks on one question: *does YTM know enough to prescribe a training session at all?* A season goal is exactly as hard a requirement as training history or recent journaling — you cannot prescribe a session without knowing what it's for, regardless of how good the load/journal data is. See ticket 05's old file (now a stub pointing here) for the prior, separate framing.

**What to build:** Rx generation is skipped entirely — no LLM call is made — unless ALL three hard floors below pass. Below any floor, the user sees a specific, ordered message naming which requirement(s) are unmet and exactly how to fix each one, instead of receiving a metrics-driven Rx built on fabricated or near-zero inputs, or one that ignores what the athlete is actually training for.

## The three floors (decided 2026-09-05, with Rob — grounded in Rx quality, not population statistics)

| # | Floor | Check | Why this is non-negotiable |
|---|---|---|---|
| 1 | Chronic training-load depth | At least 1 activity logged from 28+ days ago (`chronic_count >= 1` — the same check the old 8-component composite already used for this exact purpose; not a new invented number) | An ACWR/divergence verdict requires a real chronic (28-day) baseline. Without one, the load-based portion of the Rx is fabricated, not just uncertain. |
| 2 | Recent journaling | At least 2 journal entries in the past 7 days | A Rx generated with no recent subjective signal (energy, RPE, pain, sleep) is blind to how the athlete is actually responding — the concrete failure mode that justified this whole redesign (see ticket 02's "why gate on this" note). One entry three weeks ago tells you nothing about today. |
| 3 | Season goal present | `coach_recommendations.has_season_goal(user_id)` returns true (race or non-race, ticket 01) | Cannot prescribe a session without knowing what it's for. Equally hard a requirement as the other two — not a secondary or softer gate. |

**Data Reliability's composite score (ticket 02) is no longer part of the gate.** It doesn't need to be — floors 1 and 2 above are direct, simple checks, not derived from the composite. The composite remains valuable as **informational/narrative content**: ticket 06's panel shows it (plus its full component breakdown, including `hr_calibration`/`hrv_rhr_baseline`/`aerobic_staleness`, which are NOT gate floors — they inform confidence, not eligibility), and ticket 07's Rx prompt narrates it ("your data is X% reliable, trust this Y amount"). This resolves the original open question about picking a composite gating threshold — there isn't one to pick anymore.

**Blocked by:** 01 (non-race season goals — done, deployed 2026-09-05). **No longer blocked by 02** — the composite score isn't needed to implement the three floors; 02 remains a dependency for tickets 06/07 only.

**Status:** ready-for-agent

## Message ordering when multiple floors fail

Every failing floor is listed — none are hidden or demoted to a "by the way" footnote, since all three genuinely block. But they're **ordered hardest-to-fix first**: sequencing the 30-second season-goal form ahead of "you need weeks of training history" would let a user clear the easy item, feel like they're done, then discover the real work was still ahead. Order: (1) chronic depth, (2) recent journaling, (3) season goal.

## Blocking message copy — labels, action, and deep link (confirmed with Rob 2026-09-05)

Internal names are not user-facing. Use this exact mapping everywhere the gate or its status is shown (this ticket's blocking screen, and ticket 06's panel for the non-floor components too):

| Floor / Component | Label | Message | Link |
|---|---|---|---|
| Chronic depth | Training history | If Strava sync looks stale/disconnected: "Check your Strava connection." Otherwise: "Get back into regular training — this rebuilds as you log more sessions." (no link in the second case — nothing to click) | `/strava-setup` (conditional) |
| Recent journaling | Journaling | "Log a few recent entries to catch up — you need at least 2 in the past week." | `/dashboard?tab=journal` |
| Season goal | Season goal | "Set a season goal — race or general fitness/weight-loss/base-building." | `/dashboard?tab=coach&subtab=season` |
| *(informational, ticket 06 only)* `hr_calibration` | Heart rate setup | "Add your max and resting heart rate." | `/settings/hrzones` |
| *(informational, ticket 06 only)* `hrv_rhr_baseline` | Morning readiness | "Connect intervals.icu to sync HRV and resting heart rate automatically." | `/settings/integrations` |
| *(informational, ticket 06 only)* `aerobic_staleness` | Aerobic fitness test | "Take a new aerobic assessment." | `/dashboard?tab=coach&subtab=season#aerobic-assessment` — **this anchor does not exist yet** (unlike `#athlete-model`, which SeasonPage.tsx already supports via its scroll-to-hash effect); add `id="aerobic-assessment"` to that panel as part of this ticket. |

## Enforcement seam — named explicitly after a review pass (2026-09-05), do not assume one call site is enough

This repo has been burned by this exact pattern twice before (a legacy generator surviving a migration; a fix landing in one code path and not a sibling one). Verified entry points into Rx generation, as of this ticket — **all three floors must be checked at every one of these**, not just the daily seam:
- `assemble_daily_context()` (llm_recommendations_module.py:1814) — the shared context seam; called from 3 sites in that file (lines 2656, 4921, 5666). This is where `_load_coaching_context()` already lives per `.claude/CLAUDE.md`, and `app/tests/test_daily_context.py` already fails the build if a builder stops consuming a shared signal — the gate almost certainly belongs here, reusing that same guarantee.
- `generate_recommendations_agentic()` — **explicitly flagged in `.claude/CLAUDE.md` as outside the seam already**, needing a direct check. Called from `/cron/weekly-comprehensive` (strava_app.py:7044).
- `generate_activity_autopsy_enhanced()` — **also explicitly flagged as outside the seam**, needing a direct check.
- `/cron/daily-recommendations` (strava_app.py:6823) — the daily cron entry point; confirm what it calls and whether that path reaches the seam.
- `/api/llm-recommendations/generate` (strava_app.py:2296, manual/on-demand generation) — confirm this path too.

Before implementing: confirm which of these actually need their own gate check vs. which already route through `assemble_daily_context()` by construction, then add an explicit test asserting no generator can bypass the gate — mirroring how `test_daily_context.py` already guards the coaching-context seam.

## Acceptance criteria

- [ ] A user failing any of the three floors is blocked from Rx generation entirely — verified no LLM call occurs, across every entry point listed above
- [ ] Blocking message lists every failing floor, ordered hardest-to-fix first (chronic depth → journaling → season goal), each using the label/message/link mapping above — not raw internal names, not a generic "insufficient data" message
- [ ] A user passing all three floors sees no change in behavior
- [ ] Fixing a failing floor (journaling again, syncing recent activity, setting a goal) and re-requesting a Rx unblocks it once that specific floor passes — partial progress on one floor is reflected immediately, not held hostage by the others
- [ ] `#aerobic-assessment` anchor added to SeasonPage.tsx's aerobic assessment panel (needed for ticket 06's informational link, not this ticket's own floors)
