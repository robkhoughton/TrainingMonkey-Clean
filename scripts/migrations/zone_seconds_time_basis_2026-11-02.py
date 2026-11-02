#!/usr/bin/env python3
"""
Store the Strava time stream and correct stored zone seconds for downsampled streams.

PURPOSE:
Strava downsamples long activities (smart recording: ~1 sample per 2-3 s on trail runs).
Zone time was computed by counting each HR sample as one second, so stored
activities.time_in_zone* understated real minutes by ~2.5-3x (user 1, 2026-10-31: 29 min
stored for a 94 min run). Zone percentages were roughly right; absolute minutes were not,
which broke the minute-based checks (aerobic base >= 45 min in Zone 2, Hard >= 15 min
above VT2).

1. Schema:
   - hr_streams.time_data JSONB     — per-sample elapsed seconds, index-aligned with hr_data
   - activities.zone_time_basis TEXT — how time_in_zone* was measured:
       'time'    weighted by the time stream (new syncs)
       'samples' 1 s per sample (stream at >= 1 Hz, or no time stream returned)
       'uniform' history: moving time spread evenly across the samples (this backfill)
2. Backfill (rows with zone_time_basis IS NULL and a stored HR stream): scale each stored
   zone by moving_seconds / sample_count when that factor exceeds 1. sample_count is the
   length of the stored stream (activities.hr_stream_sample_count is 0 for most rows).
   Scaling keeps the zone boundaries each activity was originally bucketed with, so
   later changes to a user's HR settings are not applied retroactively. Each row is
   marked with its basis, so the script is idempotent.

USAGE (from repo root, Cloud SQL proxy running):
    python scripts/migrations/zone_seconds_time_basis_2026-11-02.py            # dry run
    python scripts/migrations/zone_seconds_time_basis_2026-11-02.py --apply    # write
"""
import argparse
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

from dotenv import load_dotenv
load_dotenv('.env')
from db_credentials_loader import set_database_url
set_database_url()

import psycopg2

ZONES = ', '.join(f'time_in_zone{i}' for i in range(1, 6))
ZONE_SUM = ' + '.join(f'COALESCE(time_in_zone{i}, 0)' for i in range(1, 6))
# Latest stored stream per activity (the getter reads the newest row) and its length.
STREAMS = """
    SELECT DISTINCT ON (activity_id) activity_id, jsonb_array_length(hr_data) AS n
    FROM hr_streams
    WHERE jsonb_typeof(hr_data) = 'array'
    ORDER BY activity_id, created_at DESC
"""
FACTOR = "(a.duration_minutes * 60.0 / s.n)"
ELIGIBLE = f"""
    a.activity_id = s.activity_id AND s.n > 0
    AND a.zone_time_basis IS NULL
    AND ({ZONE_SUM.replace('COALESCE(', 'COALESCE(a.')}) > 0
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE hr_streams ADD COLUMN IF NOT EXISTS time_data JSONB")
        cur.execute("ALTER TABLE activities ADD COLUMN IF NOT EXISTS zone_time_basis TEXT")

        cur.execute(f"""
            SELECT COUNT(*) FILTER (WHERE {FACTOR} > 1.0),
                   COUNT(*) FILTER (WHERE {FACTOR} <= 1.0 OR duration_minutes IS NULL),
                   ROUND(AVG({FACTOR}) FILTER (WHERE {FACTOR} > 1.0)::numeric, 2)
            FROM activities a, ({STREAMS}) s WHERE {ELIGIBLE}
        """)
        scale_n, keep_n, avg_factor = cur.fetchone()
        print(f"Rows to scale ('uniform'): {scale_n}  (mean factor {avg_factor})")
        print(f"Rows at >= 1 Hz, unchanged ('samples'): {keep_n}")

        cur.execute(f"""
            SELECT a.activity_id, a.date, a.duration_minutes, s.n,
                   {', '.join('a.' + z for z in ZONES.split(', '))}, ROUND({FACTOR}::numeric, 2)
            FROM activities a, ({STREAMS}) s
            WHERE {ELIGIBLE} AND a.user_id = 1 AND a.date >= '2026-10-25'
            ORDER BY a.date
        """)
        for r in cur.fetchall():
            print('  user 1 sample:', r)

        if not args.apply:
            conn.rollback()
            print("Dry run — no changes written. Re-run with --apply.")
            return

        sets = ', '.join(
            f"time_in_zone{i} = ROUND(COALESCE(a.time_in_zone{i}, 0) * {FACTOR})" for i in range(1, 6)
        )
        cur.execute(f"""
            UPDATE activities a SET {sets}, zone_time_basis = 'uniform'
            FROM ({STREAMS}) s
            WHERE {ELIGIBLE} AND a.duration_minutes IS NOT NULL AND {FACTOR} > 1.0
        """)
        scaled = cur.rowcount
        cur.execute(f"""
            UPDATE activities a SET zone_time_basis = 'samples'
            FROM ({STREAMS}) s WHERE {ELIGIBLE}
        """)
        kept = cur.rowcount
        conn.commit()
        print(f"Applied: scaled {scaled}, marked unchanged {kept}")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
