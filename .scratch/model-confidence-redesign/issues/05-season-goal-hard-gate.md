# 05 — Season-goal hard gate on Rx (MERGED into 04)

**Status:** merged into `04-adequate-context-gate.md` (2026-09-05)

This ticket's original framing treated the season-goal gate as independent from the Data Reliability gate (04), needing a precedence rule between the two when both failed. A discussion on 2026-09-05 concluded that framing was wrong: a season goal is exactly as hard a requirement as training-load depth or recent journaling — YTM cannot prescribe a session without knowing what it's for, regardless of how good the load/journal data is. All three are floor checks on one question ("does YTM know enough to prescribe at all"), not two systems needing to be reconciled.

See `04-adequate-context-gate.md` for the current ticket: the season-goal check is floor #3 there, `coach_recommendations.has_season_goal(user_id)`, ordered last in the blocking message (since it's the fastest to fix) but blocking on exactly the same footing as the other two floors.
