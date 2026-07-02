"""Add explicit synthesis_week_start to weekly_programs.

The displayed "week in review" range was derived as (synthesis_generated_at - 7 days),
which is only correct when the synthesis is generated on schedule. A late or manual
regeneration mislabels the week. Storing the actual trailing-window start the synthesis
covered makes the displayed range exact regardless of when it was generated.

Idempotent. Run from scripts/migrations/.
"""
import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
sys.path.insert(0, _APP_DIR)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(_APP_DIR, '.env'))

from db_credentials_loader import set_database_url  # noqa: E402
set_database_url()

import db_utils  # noqa: E402


def main():
    db_utils.execute_query(
        "ALTER TABLE weekly_programs ADD COLUMN IF NOT EXISTS synthesis_week_start DATE"
    )
    print("Ensured weekly_programs.synthesis_week_start (DATE)")

    rows = db_utils.execute_query(
        """
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_name = 'weekly_programs' AND column_name = 'synthesis_week_start'
        """,
        fetch=True,
    )
    if not rows:
        raise SystemExit("Migration verification failed — column missing")
    print(f"Verified: {rows[0]['column_name']} ({rows[0]['data_type']})")
    print("Migration complete.")


if __name__ == "__main__":
    main()
