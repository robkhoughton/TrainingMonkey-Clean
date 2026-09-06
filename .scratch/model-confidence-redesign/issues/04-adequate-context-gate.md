# 04 — Adequate Context Gate on Rx generation

**Merged 2026-09-05** from the original tickets 04 (Data Reliability gates Rx) and 05 (season-goal hard gate), after a discussion surfaced that they were never two independent systems needing a precedence rule between them — they're three floor checks on one question: *does YTM know enough to prescribe a training session at all?* A season goal is exactly as hard a requirement as training history or recent journaling — you cannot prescribe a session without knowing what it's for, regardless of how good the load/journal data is. See ticket 05's old file (now a stub pointing here) for the prior, separate framing.

**What to build:** Rx generation is skipped entirely — no LLM call is made — unless ALL three hard floors below pass. Below any floor, the user sees a specific, ordered message naming which requirement(s) are unmet and exactly how to fix each one, instead of receiving a metrics-driven Rx built on fabricated or near-zero inputs, or one that ignores what the athlete is actually training for.

## The three floors (decided 2026-09-05, with Rob — grounded in Rx quality, not population statistics)

| # | Floor | Check | Why this is non-negotiable |
|---|---|---|---|
| 1 | Chronic training-load depth | At least 1 activity logged from 28+ days ago (`chronic_count >= 1` — the same check the old 8-component composite already used for this exact purpose; not a new invented number) | An ACWR/divergence verdict requires a real chronic (28-day) baseline. Without one, the load-based portion of the Rx is fabricated, not just uncertain. |
| 2 | Recent journaling | At least 2 journal entries in the past 7 days | A Rx generated with no recent subjective signal (energy, RPE, pain, sleep) is blind to how the athlete is actually responding — the concrete failure mode that justified this whole redesign (see ticket 02's "why gate on this" note). One entry three weeks ago tells you nothing about today. |
| 3 | Season goal present | `coach_recommendations.has_season_goal(user_id)` returns true (race or non-race, ticket 01) | Cannot prescribe a session without knowing what it's for. Equally hard a requirement as the other two — not a secondary or softer gate. |

**Rollout impact, checked against real data (2026-09-05) — accepted cost, not a reason to soften the floors:** of 149 current users, 96% already pass chronic depth, but only 3% (5 users) have journaled ≥2 times in the past 7 days, and only 10% (15 users) have ever set any season goal — combined, only 2 of 149 would pass all three floors today. Rob's call: *"that is the cost of a reliable Rx... we just need to be sure that the messaging and pointing are spot on."* This ticket ships as designed; the floors are not adjusted to raise the current pass rate. Given how many users will see this message, the label/message/link accuracy below matters more than usual — verify each link live before shipping, not just by inspection (two links in this ticket were wrong until live-checked in the mock server: `/strava-setup` was first-time OAuth setup, not a resync page, and the original `/dashboard?tab=...` URLs should have been the app's actual `/?tab=X&subtab=Y` / `onNavigateToTab()` conventions instead).

**Data Reliability's composite score (ticket 02) is no longer part of the gate.** It doesn't need to be — floors 1 and 2 above are direct, simple checks, not derived from the composite. The composite remains valuable as **informational/narrative content**: ticket 06's panel shows it (plus its full component breakdown, including `hr_calibration`/`hrv_rhr_baseline`/`aerobic_staleness`, which are NOT gate floors — they inform confidence, not eligibility), and ticket 07's Rx prompt narrates it ("your data is X% reliable, trust this Y amount"). This resolves the original open question about picking a composite gating threshold — there isn't one to pick anymore.

**Blocked by:** 01 (non-race season goals — done, deployed 2026-09-05). **No longer blocked by 02** — the composite score isn't needed to implement the three floors; 02 remains a dependency for tickets 06/07 only.

**Status:** done (2026-09-06)

**Implementation notes:**
- `app/adequate_context_gate.py` — `check_adequate_context(user_id)`, the three floors.
- Checked at the top of all four verified entry points in `llm_recommendations_module.py`: `generate_recommendations()`, `generate_recommendations_agentic()`, `generate_activity_autopsy_enhanced()`, `generate_autopsy_informed_daily_decision()` — placed *after* every existing "return the already-valid recommendation" short-circuit in each, so a passing user's behavior is genuinely unchanged and a gate-failing user never triggers the LLM call. `assemble_daily_context()` itself was deliberately left untouched (too risky to add exception-based control flow to a function 3+ callers depend on for pure content assembly) — checking at the 4 top-level generators instead gives full, verified coverage of every cron/manual/journal-triggered path (confirmed by tracing every call site in strava_app.py) without touching that seam.
- Found and fixed a latent bug this gate would have newly exposed: `generate_autopsy_for_date()` (strava_app.py) didn't handle a `None` autopsy result — it fell into an "old format" fallback that would still INSERT an empty-string autopsy row into `ai_autopsies`. Added an explicit early return.
- `.claude/CLAUDE.md`'s enforcement-seam note was stale: it listed `generate_recommendations_agentic()` as outside the seam, but it now calls `assemble_daily_context()` directly (confirmed by reading its source) — corrected the doc.
- `app/tests/test_adequate_context_gate.py` — mirrors `test_daily_context.py`'s style: asserts every one of the 4 generators calls `check_adequate_context()`, and that the call precedes any LLM invocation in that function's source.
- `GET /api/coach/adequate-context-status` (strava_app.py) — status endpoint `TodayPage.tsx` polls; not itself a gate, just exposes `check_adequate_context()`'s result plus the Strava-sync-staleness sub-detail for the chronic-depth message branch. Found and fixed a real bug here too: `last_sync_date` is a TEXT column (not DATE), so the naive date-subtraction crashed — added explicit parsing.
- `TodayPage.tsx`'s existing "no Rx yet" placeholder extended (not replaced with a new modal) to render the ordered floor list when `gateStatus.failing_floors_ordered` is non-empty, falling back to the original generic message otherwise (covers gate-status fetch failure or an unrelated reason for no Rx). Live-verified in the mock server by overriding `window.fetch` for the status endpoint (mock mode's query parser can't produce a realistic response) — all three floor messages, the "Go to Journal" button, and the "Set a Goal" link render and navigate correctly.
- `#aerobic-assessment` anchor added to `SeasonPage.tsx` by wrapping the `AerobicAssessmentPanel`/`LactateStepTestPanel` conditional at the call site (rather than either component's internals), since either can render depending on the user's AeT method — live-verified the scroll-to-anchor works.

## Message ordering when multiple floors fail

Every failing floor is listed — none are hidden or demoted to a "by the way" footnote, since all three genuinely block. But they're **ordered hardest-to-fix first**: sequencing the 30-second season-goal form ahead of "you need weeks of training history" would let a user clear the easy item, feel like they're done, then discover the real work was still ahead. Order: (1) chronic depth, (2) recent journaling, (3) season goal.

## Reuse the existing "no Rx yet" card — don't build a new blocking screen (found 2026-09-05, live-verified in the mock server)

`TodayPage.tsx` already has a placeholder in the Training Prescription card for "no Rx yet," shown today only for the journal-only reason: *"Your daily prescription will appear here once you've logged a few journal entries... Go to Journal"* (a `Go to Journal` button calling `onNavigateToTab('journal')` — the same `setActiveTab` prop `App.tsx` passes down for in-app tab switches, no full page reload). This ticket should **extend that existing conditional** to branch on all three floors and list whichever are failing, rather than introducing a separate blocking modal/screen. It's the natural existing home for this message and already matches the card's tone.

The page also already has a live example of the other link style needed here: `TodayPage.tsx`'s "Improve model confidence →" link is a plain `<a href="/?tab=coach&subtab=season#athlete-model">` — confirming the canonical deep-link format for this app is `/?tab=X&subtab=Y#anchor` (bare root, not `/dashboard`), used for anything needing a subtab or anchor that `onNavigateToTab()` can't reach (it only sets the top-level tab).

## Blocking message copy — labels, action, and deep link (confirmed with Rob 2026-09-05; link mechanism corrected after live-checking the actual UI, same date)

Internal names are not user-facing. Use this exact mapping everywhere the gate or its status is shown (the extended Training Prescription card above, and ticket 06's panel for the non-floor components too):

| Floor / Component | Label | Message | Link |
|---|---|---|---|
| Chronic depth | Training history | If Strava sync looks stale/disconnected: "Check your Strava connection." Otherwise: "Get back into regular training — this rebuilds as you log more sessions." (no link in the second case — nothing to click) | `onNavigateToTab('today')` — the "Sync with Strava" button already lives on the Today page header (confirmed live: shows "Synced today" / an orange Sync button there). **Not** `/strava-setup`, which is first-time OAuth credential entry, not a status/resync page — wrong destination for an already-connected user. |
| Recent journaling | Journaling | "Log a few recent entries to catch up — you need at least 2 in the past week." | `onNavigateToTab('journal')` — same call the existing placeholder already uses |
| Season goal | Season goal | "Set a season goal — race or general fitness/weight-loss/base-building." | `/?tab=coach&subtab=season` (plain href — `onNavigateToTab` can't reach a subtab) |
| *(informational, ticket 06 only)* `hr_calibration` | Heart rate setup | "Add your max and resting heart rate." | `/settings/hrzones` |
| *(informational, ticket 06 only)* `hrv_rhr_baseline` | Morning readiness | "Connect intervals.icu to sync HRV and resting heart rate automatically." | `/settings/integrations` |
| *(informational, ticket 06 only)* `aerobic_staleness` | Aerobic fitness test | "Take a new aerobic assessment." | `/?tab=coach&subtab=season#aerobic-assessment` — **this anchor does not exist yet** (unlike `#athlete-model`, which SeasonPage.tsx already supports via its scroll-to-hash effect, confirmed live); add `id="aerobic-assessment"` to that panel as part of this ticket. |

## Enforcement seam — named explicitly after a review pass (2026-09-05), do not assume one call site is enough

This repo has been burned by this exact pattern twice before (a legacy generator surviving a migration; a fix landing in one code path and not a sibling one). Verified entry points into Rx generation, as of this ticket — **all three floors must be checked at every one of these**, not just the daily seam:
- `assemble_daily_context()` (llm_recommendations_module.py:1814) — the shared context seam; called from 3 sites in that file (lines 2656, 4921, 5666). This is where `_load_coaching_context()` already lives per `.claude/CLAUDE.md`, and `app/tests/test_daily_context.py` already fails the build if a builder stops consuming a shared signal — the gate almost certainly belongs here, reusing that same guarantee.
- `generate_recommendations_agentic()` — **explicitly flagged in `.claude/CLAUDE.md` as outside the seam already**, needing a direct check. Called from `/cron/weekly-comprehensive` (strava_app.py:7044).
- `generate_activity_autopsy_enhanced()` — **also explicitly flagged as outside the seam**, needing a direct check.
- `/cron/daily-recommendations` (strava_app.py:6823) — the daily cron entry point; confirm what it calls and whether that path reaches the seam.
- `/api/llm-recommendations/generate` (strava_app.py:2296, manual/on-demand generation) — confirm this path too.

Before implementing: confirm which of these actually need their own gate check vs. which already route through `assemble_daily_context()` by construction, then add an explicit test asserting no generator can bypass the gate — mirroring how `test_daily_context.py` already guards the coaching-context seam.

## Acceptance criteria

- [x] A user failing any of the three floors is blocked from Rx generation entirely — verified no LLM call occurs, across every entry point listed above (live-tested against real account 80: `generate_recommendations(force=True, user_id=80)` returned `None`, zero new rows in `llm_recommendations`)
- [x] Blocking message lists every failing floor, ordered hardest-to-fix first (chronic depth → journaling → season goal), each using the label/message/link mapping above — not raw internal names, not a generic "insufficient data" message
- [x] A user passing all three floors sees no change in behavior (gate check placed after every pre-existing "return existing Rx" short-circuit; a passing user's code path is byte-for-byte what it was before this ticket)
- [x] Each floor's own pass/fail is recomputed fresh and reflected immediately in the status endpoint as the user fixes it — Rx generation itself still requires all three (by design, not a partial-credit gate)
- [x] `#aerobic-assessment` anchor added to SeasonPage.tsx's aerobic assessment panel — live-verified the scroll-to-anchor works
- [x] Extends `TodayPage.tsx`'s existing "no Rx yet" placeholder in the Training Prescription card, rather than introducing a new modal/screen
- [x] Uses `onNavigateToTab()` for same-tab-set navigation and the `/?tab=X&subtab=Y#anchor` href convention where a subtab/anchor is needed — matching the app's existing patterns, not an invented URL format
- [x] Every link in the final implementation is click-tested live in the mock server, not just inspected — "Go to Journal" and "Set a Goal" both confirmed navigating correctly
