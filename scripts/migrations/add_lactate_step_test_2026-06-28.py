"""
Migration: LT1 Lactate Step Test as a selectable AeT assessment method.
Date: 2026-06-28
Spec: docs/design_lt1_step_test_2026-06-28.md

Changes:
  1. user_settings.aet_assessment_method  VARCHAR DEFAULT 'hr_drift'
       Which AeT assessment the athlete uses: 'hr_drift' | 'lactate_step'.
  2. athlete_models.aet_method            VARCHAR
       Which method produced the current aet_bpm (alongside aet_bpm / aet_test_date).
  3. NEW TABLE lactate_step_tests
       Keeps the full lactate curve per test (JSONB stages) for comparison over
       time and so the deferred Dmax / LT2 analyzers can reuse the same storage.

PostgreSQL only. Idempotent (IF NOT EXISTS guards). Run from app/ via proxy per
.claude/CLAUDE.md § Local Development.
"""

import os
import sys

# scripts/migrations/ -> app/ is two levels up + /app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'app', '.env'))

from db_credentials_loader import set_database_url  # noqa: E402

set_database_url()  # must run before importing db_utils (it requires DATABASE_URL at import)

import db_utils  # noqa: E402


def run():
    # ── 1. user_settings.aet_assessment_method ──────────────────────────────
    db_utils.execute_query(
        """
        ALTER TABLE user_settings
        ADD COLUMN IF NOT EXISTS aet_assessment_method VARCHAR DEFAULT 'hr_drift'
        """
    )
    # Backfill any pre-existing NULLs to the default
    db_utils.execute_query(
        "UPDATE user_settings SET aet_assessment_method = 'hr_drift' "
        "WHERE aet_assessment_method IS NULL"
    )
    print("OK user_settings.aet_assessment_method ready (default 'hr_drift')")

    # ── 2. athlete_models.aet_method ────────────────────────────────────────
    db_utils.execute_query(
        "ALTER TABLE athlete_models ADD COLUMN IF NOT EXISTS aet_method VARCHAR"
    )
    print("OK athlete_models.aet_method ready")

    # ── 3. lactate_step_tests ───────────────────────────────────────────────
    db_utils.execute_query(
        """
        CREATE TABLE IF NOT EXISTS lactate_step_tests (
            id               SERIAL PRIMARY KEY,
            user_id          INTEGER NOT NULL,
            test_date        DATE NOT NULL,
            speed            DOUBLE PRECISION,          -- fixed test speed
            speed_unit       VARCHAR DEFAULT 'mph',     -- unit for speed
            stages           JSONB NOT NULL,            -- [{stage,grade,hr,lactate}, ...]
            baseline_lactate DOUBLE PRECISION,
            lt1_bpm          DOUBLE PRECISION,          -- AeT bpm = LT1 HR
            lt1_grade        DOUBLE PRECISION,
            valid            BOOLEAN DEFAULT TRUE,       -- false = no sustained rise captured
            analyzer_method  VARCHAR DEFAULT 'first_sustained_rise',  -- pluggable: dmax/lt2 later
            method           VARCHAR DEFAULT 'lactate_step',          -- assessment method label
            notes            TEXT,
            created_at       TIMESTAMP DEFAULT NOW(),
            updated_at       TIMESTAMP DEFAULT NOW(),
            UNIQUE (user_id, test_date)
        )
        """
    )
    db_utils.execute_query(
        "CREATE INDEX IF NOT EXISTS idx_lactate_step_tests_user_date "
        "ON lactate_step_tests (user_id, test_date DESC)"
    )
    print("OK lactate_step_tests table + index ready")

    # ── verify ──────────────────────────────────────────────────────────────
    cols = db_utils.execute_query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'lactate_step_tests' ORDER BY ordinal_position",
        fetch=True,
    )
    print("lactate_step_tests columns:", [c['column_name'] for c in cols])

    for tbl, col in (('user_settings', 'aet_assessment_method'),
                     ('athlete_models', 'aet_method')):
        chk = db_utils.execute_query(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (tbl, col), fetch=True,
        )
        print(f"{tbl}.{col} present:", bool(chk))


if __name__ == '__main__':
    run()
    print("Migration complete.")
