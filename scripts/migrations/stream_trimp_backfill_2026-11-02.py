#!/usr/bin/env python3
"""
Recompute TRIMP from stored HR streams for activities that got average-HR TRIMP, then
recompute moving averages, ACWR and normalized divergence from the earliest changed date.

PURPOSE:
Stream TRIMP was gated behind the 'enhanced_trimp_calculation' beta flag (users 1-3), so
every other user's activities got average-HR Banister TRIMP even when an HR stream was
stored (15,753 activities, 136 users on 2026-11-02). Internal ACWR and divergence for
those users therefore rest on average-HR TRIMP. Ingestion now always uses
strava_training_load.compute_activity_trimp (stream whenever one exists).

METHOD:
- TRIMP: compute_activity_trimp with the user's current resting/max HR and gender, the
  same call sync and the HR-settings recalculation make. Activities with no stored stream
  keep average-HR TRIMP (nothing else to compute from).
- Rolling metrics: the production update_moving_averages(date, user_id) runs for every
  activity date from the user's earliest changed date onward. Its activity queries are
  answered from one up-front load of the user's rows and its UPDATEs are collected, then
  written over a single connection (one connection per query across thousands of dates
  makes the Cloud SQL proxy drop connections).
- Fidelity check (dry run): the replay is first run with the OLD TRIMP and compared with
  the stored values; a mismatch means the in-memory replay is not reproducing production.

USAGE (from repo root, Cloud SQL proxy running):
    python scripts/migrations/stream_trimp_backfill_2026-11-02.py              # dry run
    python scripts/migrations/stream_trimp_backfill_2026-11-02.py --apply      # write
    python scripts/migrations/stream_trimp_backfill_2026-11-02.py --user 42    # one user
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

from dotenv import load_dotenv
load_dotenv('.env')
from db_credentials_loader import set_database_url
set_database_url()

import psycopg2
import psycopg2.extras
import strava_training_load as stl
import acwr_configuration_service as svc_module

logging.disable(logging.CRITICAL)
HISTORY_DAYS = 90  # rows loaded before the first recomputed date (covers 28d and enhanced chronic)
METRICS = ('seven_day_avg_load', 'twentyeight_day_avg_load', 'seven_day_avg_trimp',
           'twentyeight_day_avg_trimp', 'acute_chronic_ratio', 'trimp_acute_chronic_ratio',
           'normalized_divergence')


def fetch(cur, query, params=()):
    cur.execute(query, params)
    return cur.fetchall()


def as_date(v):
    return v if hasattr(v, 'year') and not isinstance(v, str) else datetime.strptime(str(v)[:10], '%Y-%m-%d').date()


def replay(user_id, rows, dates):
    """Run the production update_moving_averages for each date against in-memory rows.
    Returns {date: {metric: value}}."""
    captured = {}

    def stl_query(query, params=None, fetch=False):
        q = ' '.join(query.split())
        if q.startswith('SELECT COALESCE(SUM(total_load_miles), 0)') or q.startswith('SELECT COALESCE(SUM(trimp), 0)'):
            start, end, _uid = as_date(params[0]), as_date(params[1]), params[2]
            col = 'total_load_miles' if 'total_load_miles' in q else 'trimp'
            return [{'s': sum(float(r[col] or 0) for r in rows if start <= r['date'] <= end)}]
        if q.startswith('UPDATE activities SET seven_day_avg_load'):
            vals, day = params[:7], as_date(params[7])
            captured[day] = dict(zip(METRICS, vals))
            return 1
        raise RuntimeError(f'unexpected query in replay: {q[:80]}')

    def svc_query(query, params=None, fetch=False):
        _uid, start, end = params
        start, end = as_date(start), as_date(end)
        return [{'date': r['date'], 'total_load_miles': r['total_load_miles'], 'trimp': r['trimp']}
                for r in rows if start <= r['date'] <= end]

    # Read the user's ACWR configuration BEFORE patching: inside the patch its query would
    # hit svc_query, fail, and silently drop the enhanced path to the standard one.
    config = svc_module.ACWRConfigurationService().get_user_configuration(user_id)

    def cached_config(self, uid):
        return config

    with patch.object(stl, 'execute_query', side_effect=stl_query), \
         patch.object(svc_module.db_utils, 'execute_query', side_effect=svc_query), \
         patch.object(svc_module.ACWRConfigurationService, 'get_user_configuration', cached_config):
        for d in dates:
            stl.update_moving_averages(d.strftime('%Y-%m-%d'), user_id)
    return captured


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--user', type=int)
    args = ap.parse_args()

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    users = fetch(cur, """
        SELECT a.user_id, MIN(a.date) AS first_date, COUNT(*) AS n
        FROM activities a
        WHERE a.activity_id > 0 AND a.trimp_calculation_method = 'average'
          AND EXISTS (SELECT 1 FROM hr_streams h WHERE h.activity_id = a.activity_id)
          {}
        GROUP BY a.user_id ORDER BY a.user_id
    """.format('AND a.user_id = %s' if args.user else ''), (args.user,) if args.user else ())

    totals = {'users': 0, 'trimp_rows': 0, 'metric_rows': 0, 'fidelity_mismatch': 0}
    for u in users:
        user_id, first_date = u['user_id'], u['first_date']
        s = fetch(cur, "SELECT resting_hr, max_hr, gender FROM user_settings WHERE id = %s", (user_id,))
        if not s or not s[0]['resting_hr'] or not s[0]['max_hr']:
            print(f'user {user_id}: SKIPPED, no resting/max HR in settings')
            continue
        hr_config = {'resting_hr': s[0]['resting_hr'], 'max_hr': s[0]['max_hr'],
                     'gender': s[0]['gender'] or 'male'}

        targets = fetch(cur, """
            SELECT a.activity_id, a.duration_minutes, a.avg_heart_rate, a.trimp, s.hr_data, s.time_data
            FROM activities a
            JOIN LATERAL (SELECT hr_data, time_data FROM hr_streams h
                          WHERE h.activity_id = a.activity_id ORDER BY h.created_at DESC LIMIT 1) s ON TRUE
            WHERE a.user_id = %s AND a.activity_id > 0 AND a.trimp_calculation_method = 'average'
        """, (user_id,))
        trimp_updates, new_trimp = [], {}
        for t in targets:
            hr = json.loads(t['hr_data']) if isinstance(t['hr_data'], str) else t['hr_data']
            td = json.loads(t['time_data']) if isinstance(t['time_data'], str) else t['time_data']
            trimp, method, n = stl.compute_activity_trimp(
                float(t['duration_minutes'] or 0), float(t['avg_heart_rate'] or 0), hr_config, hr, td)
            new_trimp[t['activity_id']] = trimp
            trimp_updates.append((trimp, method, n, t['activity_id'], user_id))

        rows = [dict(r) for r in fetch(cur, """
            SELECT activity_id, date, total_load_miles, trimp, """ + ', '.join(METRICS) + """
            FROM activities WHERE user_id = %s AND date >= %s ORDER BY date
        """, (user_id, first_date - timedelta(days=HISTORY_DAYS)))]
        dates = sorted({r['date'] for r in rows if r['date'] >= first_date})

        # Fidelity: replay with the stored (old) TRIMP must reproduce the stored metrics.
        old = replay(user_id, rows, dates[-14:])
        stored = {}
        for r in rows:
            stored.setdefault(r['date'], r)
        # Only dates with a stored value can be compared; users whose rolling metrics were
        # never computed (NULL) have nothing to reproduce.
        comparable = {d: v for d, v in old.items() if stored[d]['trimp_acute_chronic_ratio'] is not None}
        mism = sum(1 for d, v in comparable.items()
                   if abs(float(stored[d]['trimp_acute_chronic_ratio']) - float(v['trimp_acute_chronic_ratio'] or 0)) > 0.011)
        totals['fidelity_mismatch'] += mism

        for r in rows:
            if r['activity_id'] in new_trimp:
                r['trimp'] = new_trimp[r['activity_id']]
        new = replay(user_id, rows, dates)
        metric_updates = [tuple(v[m] for m in METRICS) + (d, user_id) for d, v in sorted(new.items())]

        old_sum = sum(float(t['trimp'] or 0) for t in targets)
        new_sum = sum(new_trimp.values())
        last = dates[-1]
        print(f"user {user_id}: {len(targets)} activities, TRIMP total {old_sum:.0f} -> {new_sum:.0f} "
              f"({(new_sum / old_sum - 1) * 100 if old_sum else 0:+.1f}%); {len(dates)} dates; "
              f"latest {last} divergence {stored[last]['normalized_divergence']} -> {new[last]['normalized_divergence']}; "
              f"fidelity mismatches {mism}/{len(comparable)}")

        if args.apply and mism:
            print(f'user {user_id}: NOT WRITTEN, replay does not reproduce stored metrics')
            continue
        if args.apply:
            wcur = conn.cursor()
            try:
                wcur.executemany("""
                    UPDATE activities SET trimp = %s, trimp_calculation_method = %s,
                           hr_stream_sample_count = %s, trimp_processed_at = NOW()
                    WHERE activity_id = %s AND user_id = %s""", trimp_updates)
                wcur.executemany("""
                    UPDATE activities SET seven_day_avg_load = %s, twentyeight_day_avg_load = %s,
                           seven_day_avg_trimp = %s, twentyeight_day_avg_trimp = %s,
                           acute_chronic_ratio = %s, trimp_acute_chronic_ratio = %s,
                           normalized_divergence = %s
                    WHERE date = %s AND user_id = %s""", metric_updates)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                wcur.close()
        totals['users'] += 1
        totals['trimp_rows'] += len(trimp_updates)
        totals['metric_rows'] += len(metric_updates)

    cur.close()
    conn.close()
    print(f"\n{'APPLIED' if args.apply else 'DRY RUN'}: {totals}")


if __name__ == '__main__':
    main()
