"""Add dual-track weekly synthesis scoring + athlete week reflection columns.

Mirrors the daily autopsy's score persistence (alignment/quality/composite) at the
weekly level, and adds storage for the athlete's "how did your week go?" reflection
that feeds the next weekly plan.

Columns added to weekly_programs:
  - weekly_alignment_score   INT          (Track A: RX adherence, 1-10)
  - weekly_quality_score     INT          (Track B: productive work, 1-10)
  - weekly_composite_score   NUMERIC(4,2) (per-user weighted blend)
  - week_reflection          TEXT         (athlete's own-words week review)
  - reflection_submitted_at  TIMESTAMP    (when the reflection was captured)

Idempotent — safe to run multiple times.

Run from scripts/migrations/ (this script sets its own import path to app/).
"""
import os
import sys

# Resolve app/ on the import path, then load credentials BEFORE importing db_utils
# (db_utils raises at import time if DATABASE_URL is unset).
_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
sys.path.insert(0, _APP_DIR)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(_APP_DIR, '.env'))

from db_credentials_loader import set_database_url  # noqa: E402
set_database_url()

import db_utils  # noqa: E402

COLUMNS = [
    ("weekly_alignment_score", "INT"),
    ("weekly_quality_score", "INT"),
    ("weekly_composite_score", "NUMERIC(4,2)"),
    ("week_reflection", "TEXT"),
    ("reflection_submitted_at", "TIMESTAMP"),
]


def main():
    for name, coltype in COLUMNS:
        db_utils.execute_query(
            f"ALTER TABLE weekly_programs ADD COLUMN IF NOT EXISTS {name} {coltype}"
        )
        print(f"Ensured weekly_programs.{name} ({coltype})")

    # Verify
    rows = db_utils.execute_query(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'weekly_programs'
          AND column_name IN (
            'weekly_alignment_score', 'weekly_quality_score', 'weekly_composite_score',
            'week_reflection', 'reflection_submitted_at'
          )
        ORDER BY column_name
        """,
        fetch=True,
    )
    print("\nVerified columns now present:")
    for r in (rows or []):
        print(f"  - {r['column_name']}: {r['data_type']}")
    if not rows or len(rows) != len(COLUMNS):
        raise SystemExit("Migration verification failed — expected 5 columns")
    print("\nMigration complete.")


if __name__ == "__main__":
    main()
