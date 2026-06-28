"""
Migration: add activities.trimp_dynamic — the dynamic-AeT (Edwards) internal load.

Part of the Dynamic AeT build (Phase B, Effect B). This column runs DUAL-TRACK alongside
the incumbent Banister `trimp`: it is the Edwards summated-HR-zone TRIMP computed on zones
anchored to the effective AeT of each activity's date. Banister `trimp` stays the primary
internal-load signal feeding ACWR/divergence; `trimp_dynamic` accumulates in parallel and
only takes over divergence at a later code-gated 28-day cutover.

Forward-only: NULL for historical activities (no backfill into this column). A separate
one-time validation backfill writes to a scratch location, not here.

Run autonomously via the Cloud SQL proxy. Idempotent: ADD COLUMN IF NOT EXISTS.
"""
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)

# db_utils validates DATABASE_URL at import time, so load env + set the URL first.
from dotenv import load_dotenv
load_dotenv(os.path.join(APP_DIR, '.env'))
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

db_utils.execute_query(
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS trimp_dynamic REAL"
)
print("ensured column activities.trimp_dynamic REAL")

rows = db_utils.execute_query(
    """SELECT column_name, data_type
       FROM information_schema.columns
       WHERE table_name = 'activities' AND column_name = 'trimp_dynamic'""",
    fetch=True,
)
print("Verification:", [dict(r) for r in rows])
print("Done." if rows else "FAILED — column not present.")
