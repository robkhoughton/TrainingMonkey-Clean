# 06 — Athlete-model panel shows two scores, not one composite

**What to build:** The existing "what YTM knows about you" panel, which today shows a single blended model-confidence percentage, is replaced with Data Reliability (02) and Specification Clarity (03) shown as two distinct scores, each with its own component breakdown and "what's missing" guidance — a full replacement, not a third number added alongside the old one.

This is the engagement mechanic now: showing users the real reliability signals directly, so improving them is the same action as improving Rx quality, rather than climbing a gamified number that was only loosely related to it.

**Blocked by:** 02, 03 (both scores must exist — both done as of 2026-09-06)

**Status:** done (2026-09-06)

**Component copy — reuse ticket 04's mapping, don't invent separate wording (decided 2026-09-05):**
ticket 04 defines the label/message/deep-link mapping for every Data Reliability component (`load_coverage` → "Training history", etc.), each with an action-oriented message and a real link to the fix (e.g. `/settings/hrzones`, `/settings/integrations`). This panel must use that exact same mapping for its breakdown, not raw internal component names and not independently-drafted copy — two different phrasings of the same "why is my score low" answer in two different places is its own confusion.

**Implementation:** `CoachPage.tsx`'s existing `AthleteModelPanel` — the old single "Model Confidence" hero + 8-component list is fully replaced with two `ScoreHero` + component-row sections (Data Reliability, then Specification Clarity), reusing the existing `ConfRow`/`StatBar` primitives rather than building new ones. Backend: `GET /api/athlete-model` (`get_athlete_model_api()` in strava_app.py) now returns `data_reliability`/`specification_clarity` instead of `model_confidence` — the old composite's computation and `athlete_models.model_confidence_pct` persistence are left running unchanged (just dropped from this endpoint's response), since ticket 07's Rx-prompt read of that column still depends on it until ticket 07 migrates it.

Component actions: Athlete Profile/Season Goal reuse the panel's existing `onOpenProfileModal`/`onOpenGoalModal` callbacks. Added a new `onOpenRiskModal` prop (wired in SeasonPage.tsx to `setEditingPref('risk')`) for the `recommendation_style` row — the existing `onOpenPrefsModal` opens the *communication* pref modal, which would have pointed users at the wrong settings screen. Live-verified in the mock server: the risk-tolerance modal opens correctly from this new wiring, and the Weekly Schedule row (no modal exists for it) correctly falls back to its plain `href`.

Removed now-dead code from the old composite's UI: `jpExpanded` state and the `SubRow` sub-component (Journal Power's expandable field-coverage breakdown), both unused once the old section was replaced.

- [x] Panel displays Data Reliability and Specification Clarity as two separate scores with separate breakdowns
- [x] The old single blended model-confidence percentage is fully removed from this panel, not left displayed alongside the new two scores
- [x] Each score's breakdown gives the user a concrete, specific next action with a working deep link where one exists (not generic advice) — using ticket 04's label/message/link mapping for Data Reliability components
