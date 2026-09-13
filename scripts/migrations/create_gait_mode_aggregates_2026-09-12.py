"""
Create gait_mode_aggregates: per-activity running/hiking cadence aggregates.

Background: a single trail activity mixes running and hiking (power-hiking on
climbs); averaging cadence across the whole activity blends two different
gaits into a meaningless number. gait_classifier.classify_gait_modes()
separates the two using grade-adjusted speed (never cadence, to avoid
circularity) and this table stores the resulting per-mode aggregates.

classifier_version is part of the unique key, not just a metadata column: if
the classifier's thresholds are ever retuned, old and new aggregates get
different version tags and are never silently blended into one trend line.

low_confidence_fraction flags the share of running-classified time that fell
in a grade band (steep descent, or >20% grade) where offline calibration
found classification confidence degrades even though the underlying cadence
signal itself stays stable.
"""
from db_credentials_loader import set_database_url
import db_utils

set_database_url()

db_utils.execute_query("""
    CREATE TABLE IF NOT EXISTS gait_mode_aggregates (
        id SERIAL PRIMARY KEY,
        activity_id BIGINT NOT NULL,
        user_id INTEGER NOT NULL,
        classifier_version TEXT NOT NULL,
        running_seconds REAL,
        hiking_seconds REAL,
        uncertain_seconds REAL,
        running_cadence_mean REAL,
        running_cadence_std REAL,
        running_cadence_n INTEGER,
        hiking_cadence_mean REAL,
        hiking_cadence_std REAL,
        hiking_cadence_n INTEGER,
        low_confidence_fraction REAL,
        computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE(activity_id, classifier_version)
    )
""")

db_utils.execute_query("""
    CREATE INDEX IF NOT EXISTS idx_gait_mode_aggregates_user
    ON gait_mode_aggregates(user_id)
""")

result = db_utils.execute_query("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'gait_mode_aggregates'
    ORDER BY ordinal_position
""", fetch=True)

print("gait_mode_aggregates columns:")
for row in result:
    print(f"  {row['column_name']}: {row['data_type']}")
