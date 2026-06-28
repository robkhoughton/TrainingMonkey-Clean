"""
B-validate: dynamic-AeT validation report. READ-ONLY — writes NOTHING to the database.

Reconstructs trimp_dynamic in memory for historical activities (per-day effective AeT +
Edwards on the stored HR stream), then compares the dynamic internal ACWR / divergence
against the incumbent Banister series over a trailing window. Also reports the no-stream
load fraction (the open fork from B2). Output: a printed summary + a CSV in the scratch dir.

Usage (from repo root, proxy live):
    python scripts/validate_dynamic_aet.py [user_id] [window_days]
"""
import os
import sys
import csv

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app')
sys.path.insert(0, APP_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP_DIR, '.env'))
from db_credentials_loader import set_database_url
set_database_url()
import db_utils
from datetime import timedelta
from timezone_utils import get_app_current_date
from dynamic_aet import get_effective_aet, dynamic_divergence
from strava_training_load import dynamic_zone_times, edwards_trimp

USER_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
WINDOW = int(sys.argv[2]) if len(sys.argv) > 2 else 60

today = get_app_current_date()
load_start = today - timedelta(days=WINDOW + 28)

us = db_utils.execute_query(
    "SELECT resting_hr, max_hr, hr_zones_method, custom_hr_zones FROM user_settings WHERE id = %s",
    (USER_ID,), fetch=True
)[0]

acts = db_utils.execute_query(
    """SELECT a.activity_id, a.date,
              COALESCE(a.trimp, 0) AS trimp, COALESCE(a.total_load_miles, 0) AS load,
              (h.activity_id IS NOT NULL) AS has_stream
       FROM activities a
       LEFT JOIN hr_streams h ON h.activity_id = a.activity_id
       WHERE a.user_id = %s AND a.date BETWEEN %s AND %s AND a.activity_id > 0
       ORDER BY a.date""",
    (USER_ID, load_start.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')), fetch=True
) or []

print(f"Reconstructing trimp_dynamic for {len(acts)} activities (this may take a minute)...")
eff_cache = {}
enriched = []
for raw in acts:
    a = dict(raw)
    a['trimp'] = float(a['trimp']); a['load'] = float(a['load'])
    a['trimp_dynamic'] = None
    if a['has_stream']:
        d = a['date']
        if d not in eff_cache:
            eff_cache[d] = get_effective_aet(USER_ID, as_of_date=d)
        eff = eff_cache[d]
        if eff:
            stream = db_utils.get_hr_stream_data(a['activity_id'], USER_ID)
            if stream and stream.get('hr_data'):
                dz = dynamic_zone_times(stream['hr_data'], us['max_hr'], us['resting_hr'],
                                        us['hr_zones_method'], us['custom_hr_zones'],
                                        eff['effective_aet'])
                a['trimp_dynamic'] = edwards_trimp(dz)
    enriched.append(a)
acts = enriched


def _sum(ref, days, key):
    start = ref - timedelta(days=days - 1)
    return sum((x[key] or 0) for x in acts if start <= x['date'] <= ref)


rows = []
for i in range(WINDOW):
    ref = today - timedelta(days=i)
    ext28 = _sum(ref, 28, 'load') / 28
    ext = round((_sum(ref, 7, 'load') / 7) / ext28, 2) if ext28 > 0 else 0.0
    ban28 = _sum(ref, 28, 'trimp') / 28
    ban_int = round((_sum(ref, 7, 'trimp') / 7) / ban28, 2) if ban28 > 0 else 0.0
    dyn28 = _sum(ref, 28, 'trimp_dynamic') / 28
    dyn_int = round((_sum(ref, 7, 'trimp_dynamic') / 7) / dyn28, 2) if dyn28 > 0 else 0.0
    ban_div = dynamic_divergence(ext, ban_int)
    dyn_div = dynamic_divergence(ext, dyn_int)
    rows.append({'date': ref.strftime('%Y-%m-%d'), 'ext_acwr': ext,
                 'banister_int': ban_int, 'dynamic_int': dyn_int,
                 'banister_div': ban_div, 'dynamic_div': dyn_div})
rows.reverse()

# No-stream load fraction over the trailing 28 days.
tw_start = today - timedelta(days=27)
trail = [x for x in acts if tw_start <= x['date'] <= today]
total_trimp = sum(x['trimp'] for x in trail)
nostream_trimp = sum(x['trimp'] for x in trail if not x['has_stream'])
nostream_frac = (nostream_trimp / total_trimp) if total_trimp > 0 else 0.0

# Comparison stats on days where the dynamic track has coverage.
comp = [r for r in rows if r['dynamic_div'] is not None and r['banister_div'] is not None and r['dynamic_int'] > 0]
diffs = [abs(r['dynamic_div'] - r['banister_div']) for r in comp]
sign_flips = sum(1 for r in comp if (r['dynamic_div'] < 0) != (r['banister_div'] < 0))

print("\n" + "=" * 72)
print(f"DYNAMIC AeT VALIDATION - user {USER_ID}, trailing {WINDOW}d (as of {today})")
print("=" * 72)
print(f"Activities in load window: {len(acts)} | with HR stream: {sum(1 for x in acts if x['has_stream'])}")
print(f"No-stream load fraction (trailing 28d TRIMP): {nostream_frac*100:.1f}%  "
      f"({nostream_trimp:.0f} of {total_trimp:.0f})")
print(f"Days with dynamic coverage: {len(comp)} / {WINDOW}")
if diffs:
    print(f"Banister vs Dynamic divergence - mean abs-delta: {sum(diffs)/len(diffs):.3f} | "
          f"max abs-delta: {max(diffs):.3f} | sign flips: {sign_flips}/{len(comp)}")
print("\nLast 21 days (ext / banister_int / dynamic_int | banister_div / dynamic_div):")
for r in rows[-21:]:
    bd = f"{r['banister_div']:+.3f}" if r['banister_div'] is not None else "  n/a"
    dd = f"{r['dynamic_div']:+.3f}" if r['dynamic_div'] is not None else "  n/a"
    print(f"  {r['date']}  ext {r['ext_acwr']:.2f} | ban {r['banister_int']:.2f} dyn {r['dynamic_int']:.2f} | "
          f"div ban {bd} dyn {dd}")

scratch = os.environ.get('TEMP', '.')
out_csv = os.path.join(scratch, f"dynamic_aet_validation_user{USER_ID}.csv")
with open(out_csv, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"\nFull series CSV: {out_csv}")
print("NOTE: read-only — no database rows were written.")
