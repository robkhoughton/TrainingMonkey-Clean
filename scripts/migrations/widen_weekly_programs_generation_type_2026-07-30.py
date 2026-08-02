"""
Widen weekly_programs_generation_type_check to allow 'reflection'.

Root cause: save_weekly_program()'s INSERT previously dropped the generation_type
param entirely (never in the column list or ON CONFLICT DO UPDATE), so every row
was silently written with the column default 'scheduled' regardless of what the
caller passed. That bug masked a second, pre-existing one: submit_week_reflection()
(app/strava_app.py) has always called save_weekly_program(..., generation_type='reflection'),
but the CHECK constraint only ever allowed 'scheduled' and 'manual'. Once the INSERT
bug was fixed to actually write generation_type, 'reflection' started violating the
constraint and the "Save & rebuild my week" flow started failing outright.

Fix: widen the constraint to the three values the application actually uses.
"""
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

db_utils.execute_query(
    "ALTER TABLE weekly_programs DROP CONSTRAINT IF EXISTS weekly_programs_generation_type_check"
)
db_utils.execute_query(
    """
    ALTER TABLE weekly_programs
    ADD CONSTRAINT weekly_programs_generation_type_check
    CHECK (generation_type IN ('scheduled', 'manual', 'reflection'))
    """
)

result = db_utils.execute_query(
    """
    SELECT pg_get_constraintdef(oid) AS def
    FROM pg_constraint
    WHERE conname = 'weekly_programs_generation_type_check'
    """,
    fetch=True
)
print("Updated constraint:", result[0]['def'] if result else "NOT FOUND")
