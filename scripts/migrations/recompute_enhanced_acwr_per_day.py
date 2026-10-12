#!/usr/bin/env python3
"""
Recompute stored enhanced-ACWR values after the per-day chronic fix.

PURPOSE:
The enhanced (exponential-decay) ACWR path averaged its chronic load per activity ROW
while the acute average is per calendar DAY, so double sessions and 'rest' placeholder
rows written beside a real activity inflated stored External/Internal ACWR. The engine
now averages chronic load per calendar day over the configured period. This script
rewrites the stored values for every activity date since each enhanced user's
configuration was assigned.

Values come from the production calculation (ACWRConfigurationService.calculate_enhanced_acwr).
Its per-date activity queries are answered from one up-front load of the user's rows,
and all writes go over a single connection: one direct connection per query across
hundreds of dates makes the Cloud SQL proxy drop connections. The UPDATE writes the
same columns as the production writer (update_moving_averages_enhanced).

Normalized divergence is unaffected by the fix (load and TRIMP share the same weights),
so stored divergence should change only by rounding.

USAGE (from repo root, Cloud SQL proxy running):
    python scripts/migrations/recompute_enhanced_acwr_per_day.py            # dry run, no writes
    python scripts/migrations/recompute_enhanced_acwr_per_day.py --apply    # write

See .scratch/enhanced-acwr-chronic-per-day/spec.md.
"""
import argparse
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
import db_utils
import acwr_configuration_service as svc_module


def enhanced_users():
    return db_utils.execute_query(
        """
        SELECT uac.user_id, uac.assigned_at::date AS assigned_on,
               ac.id, ac.chronic_period_days, ac.decay_rate
        FROM user_acwr_configurations uac
        JOIN acwr_configurations ac ON ac.id = uac.configuration_id
        WHERE uac.is_active
        ORDER BY uac.user_id
        """,
        fetch=True,
    ) or []


def load_user_rows(user_id, since, chronic_days):
    return db_utils.execute_query(
        """
        SELECT date, total_load_miles, trimp, acute_chronic_ratio, trimp_acute_chronic_ratio,
               normalized_divergence
        FROM activities
        WHERE user_id = %s AND date >= %s
        ORDER BY date
        """,
        (user_id, since - timedelta(days=chronic_days)),
        fetch=True,
    ) or []


def in_memory_activities_query(rows):
    """Answers the service's (user_id, start, end) activities queries from loaded rows."""
    def fake(query, params, fetch=False):
        _user_id, start, end = params
        start_d = datetime.strptime(start, '%Y-%m-%d').date()
        end_d = datetime.strptime(end, '%Y-%m-%d').date()
        return [r for r in rows if start_d <= r['date'] <= end_d]
    return fake


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='write recomputed values (default: dry run)')
    args = parser.parse_args()

    service = svc_module.ACWRConfigurationService()
    for user in enhanced_users():
        user_id, since = user['user_id'], user['assigned_on']
        config = {'id': user['id'], 'chronic_period_days': user['chronic_period_days'],
                  'decay_rate': user['decay_rate']}
        rows = load_user_rows(user_id, since, config['chronic_period_days'])
        stored = {}
        for r in rows:
            if r['date'] >= since:
                stored.setdefault(r['date'], r)

        updates, changed, max_shift, max_div_shift = [], 0, 0.0, 0.0
        with patch.object(svc_module.db_utils, 'execute_query', side_effect=in_memory_activities_query(rows)):
            for day, old in sorted(stored.items()):
                result = service.calculate_enhanced_acwr(user_id, day.strftime('%Y-%m-%d'), config)
                if not result.get('success'):
                    raise RuntimeError(f"user {user_id} {day}: {result.get('error')}")
                shift = abs((old['acute_chronic_ratio'] or 0) - result['enhanced_acute_chronic_ratio'])
                max_shift = max(max_shift, shift)
                max_div_shift = max(max_div_shift,
                                    abs((old['normalized_divergence'] or 0) - result['enhanced_normalized_divergence']))
                if shift > 0.005:
                    changed += 1
                updates.append((result['acute_load_avg'], result['enhanced_chronic_load'],
                                result['acute_trimp_avg'], result['enhanced_chronic_trimp'],
                                result['enhanced_acute_chronic_ratio'], result['enhanced_trimp_acute_chronic_ratio'],
                                result['enhanced_normalized_divergence'], day, user_id))

        if args.apply:
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
            try:
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        UPDATE activities SET
                            seven_day_avg_load = %s,
                            twentyeight_day_avg_load = %s,
                            seven_day_avg_trimp = %s,
                            twentyeight_day_avg_trimp = %s,
                            acute_chronic_ratio = %s,
                            trimp_acute_chronic_ratio = %s,
                            normalized_divergence = %s
                        WHERE date = %s AND user_id = %s
                        """,
                        updates,
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

        print(f"user {user_id}: {len(updates)} dates since {since}; external ACWR changed on {changed} dates "
              f"(max shift {max_shift:.2f}); max divergence shift {max_div_shift:.3f}"
              f"{' [written]' if args.apply else ' [dry run, nothing written]'}")


if __name__ == '__main__':
    main()
