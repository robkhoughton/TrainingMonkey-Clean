# scripts/migrations/add_running_speed_to_gait_aggregates_2026-09-12.py
"""
Adds raw running-mode speed stats to gait_mode_aggregates, needed to derive
stride length (speed / cadence) downstream. Additive only -- does not change
classifier logic or classifier_version.
"""
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

db_utils.execute_query("""
    ALTER TABLE gait_mode_aggregates
    ADD COLUMN IF NOT EXISTS running_speed_mean REAL,
    ADD COLUMN IF NOT EXISTS running_speed_std REAL,
    ADD COLUMN IF NOT EXISTS running_speed_n INTEGER
""")

result = db_utils.execute_query("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'gait_mode_aggregates'
    AND column_name IN ('running_speed_mean', 'running_speed_std', 'running_speed_n')
""", fetch=True)

print(f"Columns present: {[r['column_name'] for r in result]}")
