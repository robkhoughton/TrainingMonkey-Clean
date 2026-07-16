# Open Issues

Tracked follow-ups that aren't yet closed out. Remove an entry once resolved.

## Drop `weekly_recommendation` / `pattern_insights` columns from `llm_recommendations`

**Opened:** 2026-07-16
**Target review date:** 2026-07-23 (~1 week)

**Context:** Two bugs were fixed 2026-07-16 — a legacy 3-section daily-Rx prompt and a
platform-wide stale rest-day placeholder (206 rows across ~50 users, see
[[project_daily_rx_and_restday_bugs_july2026]] in Open Brain / auto-memory). As part of
that cleanup, all in-code plumbing that generated or forwarded `weekly_recommendation`
and `pattern_insights` was removed — every producer and consumer across
`llm_recommendations_module.py` and `strava_app.py` now omits these keys, and
`save_llm_recommendation()` writes `NULL` for both going forward.

**Deliberate choice — schema left untouched.** The `weekly_recommendation TEXT` and
`pattern_insights TEXT` columns in `llm_recommendations` were NOT dropped, as risk
avoidance in case something was missed and needs a quick rollback.

**Action:** If the app has been running cleanly for about a week with no
KeyError/DB-write regressions tied to this change, drop both columns via a migration
(`ALTER TABLE llm_recommendations DROP COLUMN weekly_recommendation, DROP COLUMN pattern_insights;`).
If anything surfaced in the meantime, investigate before dropping.
