# 01 — Support non-race season goals

**What to build:** A user can set a season goal that isn't a specific race — general fitness, weight loss, base-building with no race scheduled — alongside the existing race-goal flow. It persists and is retrievable the same way race goals are today, without breaking any existing race-oriented Rx or weekly-plan logic that reads race date/distance/elevation fields.

This unblocks the Specification Clarity score (03) and the season-goal hard gate (05) — both need a non-race goal to count as a fully legitimate, fully "clear" season goal, not a degraded or penalized case.

**Blocked by:** None — can start immediately

**Status:** done (2026-09-05)

**Implementation note:** Built as a separate `season_goals` table rather than
extending `race_goals` — `race_name`/`race_date` are `NOT NULL` on `race_goals`
and ~10 files read that table assuming a race exists, so a non-race goal never
enters those code paths by construction. `coach_recommendations.has_season_goal()`
is the new unifying presence check for tickets 03/05. See commit 3bc54d8.

- [x] Season-goal input screen offers a non-race goal type (or types) alongside the existing race-goal entry (name/date/distance) — "Other Season Goals" card + modal in SeasonPage.tsx, goal types: base_building/fitness/weight_loss/general
- [x] Non-race goals persist and round-trip through the same lookup path race goals use today (the domain concept the app currently calls a "race goal" needs to be read as "does this athlete have a season goal at all," not "does this athlete have a race") — `has_season_goal()` in coach_recommendations.py
- [x] Existing race-goal-dependent Rx/weekly-plan/race-readiness logic is unaffected for users who do have a race goal — race_goals table/consumers untouched
- [x] A user with only a non-race goal does not trigger any code path that assumes race date/distance/elevation are present (no crashes, no silent wrong values) — non-race goals live in a separate table, never read by race-goal-dependent code
