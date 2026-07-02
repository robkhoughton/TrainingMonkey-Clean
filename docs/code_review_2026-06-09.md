# YTM Codebase Review — 2026-06-09

Scope: security, critical-path correctness (daily coaching pipeline), data integrity, and dead code / architectural drift. Key files reviewed: `app/strava_app.py`, `app/llm_recommendations_module.py`, `app/db_utils.py`, `app/strava_training_load.py`, `app/timezone_utils.py`, `frontend/src/`.

Real issues only — style, formatting, and hypothetical problems omitted. Each finding was traced in code.

---

## SQL Injection — clean (verified, not a finding)

Every dynamic-query site found interpolates **only column names drawn from a hardcoded `allowed_fields` whitelist**, with all values passed as `%s` parameters. No user input reaches a query unparameterized.

- `strava_app.py:8409` — `UPDATE user_settings SET {fields}` — fields whitelisted at 8385.
- `acwr_configuration_service.py:463` — `UPDATE acwr_configurations SET {updates}` — whitelisted at 447.
- `acwr_migration_admin.py:774` — `SELECT COUNT(*) FROM ({query})` — wraps a fully parameterized inner query.
- `db_utils.py:598` — `INSERT INTO athlete_models (... {insert_cols})` — code-defined columns.

---

## SECURITY

### S1 — Cron endpoints protected only by a spoofable header (MEDIUM)

`strava_app.py:7280` (and 7414, 7449, 7535) gate `/cron/*` with `if not request.headers.get('X-Cloudscheduler')`. That header is plain text any HTTP client can set — the setup scripts confirm no OIDC token is configured (`--headers="X-Cloudscheduler=true"`, no `--oidc-service-account-email`). Anyone who learns the Cloud Run URL can `POST /cron/daily-recommendations` with that header and trigger **batch LLM generation for every active user** — a cost/abuse vector.

- **Fix:** have Cloud Scheduler attach an OIDC token and verify the `Authorization: Bearer` JWT (audience + service-account email), not the presence of a header.
- **Note:** inconsistency — line 1004 checks `== 'true'` while the cron checks mere presence.

### S2 — IDOR on `/api/user/dashboard-config` (LOW, but a pattern to audit)

`strava_app.py:9537`: `user_id = request.args.get('user_id', type=int)`, falling back to `current_user.id`. A logged-in user can pass `?user_id=<other_user>` and read another user's dashboard config — no ownership check. Data is low-sensitivity (chronic period, decay rate), but the pattern is broken access control. The admin twin at `10423` is correctly `is_admin`-gated.

- **Fix:** ignore client-supplied `user_id` for non-admin routes; always use `current_user.id`. Grep remaining routes for the same `request.args.get('user_id')`-without-ownership-check shape.

---

## CORRECTNESS (critical path)

### C1 — ACWR silently computes to 0 on a transient DB error (HIGH)

`strava_training_load.py:1985` `get_sum_result()` wraps each load/TRIMP sum in `try/except` and **returns 0 on any exception**. `execute_query_direct` correctly *raises* on failure (`db_utils.py:201`), but this helper eats it.

Consequence: a momentary connection blip during ACWR recompute → acute and chronic sums = 0 → `acute_chronic_ratio = 0`, `trimp_acute_chronic_ratio = 0` → these get **written to the activities row** (2055-2069). The coach then reads ACWR 0 as detraining/zero-load and gives wrong guidance, with no error surfaced.

- **Fix:** let the exception propagate (or abort the write) rather than persisting fabricated zeros. Distinguish "genuinely no activities" (`COALESCE`→0 from a *successful* query) from "query failed."

### C2 — Daily-recommendations cron uses UTC `datetime.now()`, bypassing the per-user-timezone default (LOW / latent)

`strava_app.py:7294` computes `tomorrow = datetime.now()+1` (UTC) and passes it explicitly into `generate_daily_recommendation_only(user_id, tomorrow)` at 7377 — overriding that function's own correct default `get_user_current_date(user_id)+1` (7057). Same for `cutoff`/`yesterday`/`today` at 7297/7318/7320.

**Not currently a live bug:** the job runs at 11 AM UTC (docstring 7276 ≈ 3-4 AM Pacific), where UTC and all US-timezone dates coincide, so `tomorrow` lands correctly. But it violates CLAUDE.md rule #7, contradicts the function it calls, and will go silently off-by-one if the schedule ever moves earlier in the UTC day.

- **Fix:** use `get_app_current_date()` so it is robust regardless of fire time.

---

## DATA INTEGRITY / DRIFT

### D1 — `execute_query` never pools; opens a fresh connection per call (MEDIUM)

`db_utils.py:203` defaults `use_pool=False`, so the default path always calls `execute_query_direct`, which does `with psycopg2.connect(...)` (178) — psycopg2's context manager commits/rolls back but **does not close**, and the pool (`db_manager`) is only touched when `use_pool=True` (onboarding). The documented behavior in `.claude/rules/database.md` ("execute_query() — tries pool first, falls back to direct") is false in code.

Real impact: a new TCP+TLS+auth handshake to Cloud SQL on *every* query (latency), connection reliance on GC for cleanup, and risk of momentarily exhausting Cloud SQL's connection cap under burst (e.g., the per-user loop in the daily cron).

- **Fix:** reconcile doc and code; route the hot path through the pool.

### D2 — Naive `?`→`%s` rewrite can corrupt queries (LOW / latent)

`db_utils.py:181`: `if '?' in query: query = query.replace('?', '%s')` — a global replace. Any query containing a literal `?` inside a string literal (a LIKE pattern, an embedded text value, a JSON operator) gets silently mangled. SQLite-compat dead weight in a PostgreSQL-only codebase.

### D3 — SQLite drift throughout

`get_sum_result` carries dual SQLite/PostgreSQL row handling and comments (1990-2000); `update_moving_averages` docstring says "Handles SQLite row objects" (1869); `initialize_db` creates tables at runtime (267) despite the rule "never modify schema in application code." The row-handling fallbacks are dead branches that obscure intent.

---

## DEAD CODE

- **`frontend/src/App_dev.tsx`** and **`frontend/src/updated-compact-dashboard-banner.tsx`** — zero inbound references. Dead.
- `BannerTest.tsx` / `SpinnerTestPage.tsx` — 1 ref each (test routes); confirm intentionally shipped or strip.
- **Overlapping ACWR modules**: `acwr_calculation_service`, `optimized_acwr_service`, `acwr_configuration_service`, `acwr_visualization_service`, `unified_metrics_service` all touch ACWR. Divergence was consolidated into `UnifiedMetricsService`, but the legacy `calculate_normalized_divergence` (`strava_training_load.py:1849`) and the enhanced/standard `update_moving_averages` fork remain as parallel paths — verify which is authoritative for the coach so two methods can't disagree.

---

## Top three to fix

1. **C1** — silent-zero ACWR corrupts coaching data.
2. **S1** — spoofable cron auth (cost/abuse).
3. **D1** — no connection pooling on the hot path (scalability/reliability).
