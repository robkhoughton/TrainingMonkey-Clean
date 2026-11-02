"""
The daily autopsy and the weekly polarized count must agree about every session.

Regression (user 1, week of 2026-10-25): the weekly synthesis reported "zero black hole
sessions" while the daily autopsies flagged Oct 26 (34% Z3), Oct 28 (21%) and Oct 31 (25%).
The weekly path read the stored static-zone time_in_zone* columns and used a 20% Z3 line;
the autopsy re-bucketed against that date's effective AeT and used 15%. Both now read zones
from strava_training_load.session_zone_times and share BLACK_HOLE_Z3_PCT.
"""
import os
import sys
import unittest
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import llm_recommendations_module as m
import strava_training_load
import unified_metrics_service as ums

HR = {'vt1_bpm': 144, 'vt2_bpm': 157, 'zones': {
    'zone1': {'min': 118, 'max': 132}, 'zone2': {'min': 132, 'max': 144},
    'zone3': {'min': 144, 'max': 157}, 'zone4': {'min': 157, 'max': 165},
    'zone5': {'min': 165, 'max': 178}}}


def _zones(z1=0, z2=0, z3=0, z4=0, z5=0):
    total = z1 + z2 + z3 + z4 + z5
    s = {'total_zone_seconds': total,
         'time_in_zone1': z1, 'time_in_zone2': z2, 'time_in_zone3': z3,
         'time_in_zone4': z4, 'time_in_zone5': z5}
    for i, v in enumerate([z1, z2, z3, z4, z5], 1):
        s[f'z{i}_pct'] = round(v / total * 100, 1) if total else 0.0
    return s


class TestSharedBlackHoleLine(unittest.TestCase):
    def test_threshold_is_15(self):
        self.assertEqual(m.BLACK_HOLE_Z3_PCT, 15)

    def test_weekly_class_and_daily_flag_agree_at_boundary(self):
        for z3, expect_black_hole in ((150, False), (151, True), (250, True)):
            z = _zones(z2=1000 - z3, z3=z3)
            daily = m.compute_zone_compliance(z, 'easy', HR)
            weekly = m.classify_session_polarized(z)
            self.assertEqual(daily['black_hole'], expect_black_hole, z3)
            self.assertEqual(weekly == 'Moderate', expect_black_hole, z3)


class TestWeeklyReadsSessionZoneTimes(unittest.TestCase):
    def test_weekly_count_uses_dynamic_aet_zones_not_stored_columns(self):
        # Stored columns would say Easy (static Z3 floor); the AeT re-bucket says 25% Z3.
        dates = [{'date': date(2026, 10, 31)}, {'date': date(2026, 10, 29)}]
        per_date = {'2026-10-31': _zones(z1=300, z2=1200, z3=500),
                    '2026-10-29': _zones(z1=600, z2=200)}
        with mock.patch.object(m, 'execute_query', return_value=dates), \
             mock.patch.object(strava_training_load, 'session_zone_times_for_dates',
                               side_effect=lambda uid, ds: {d: (per_date[d], None) for d in ds}) as szt:
            pr = m.compute_weekly_polarized_ratio(1, 'build', 60, week_start_date=date(2026, 10, 25))
        self.assertEqual(szt.call_count, 1)  # one batch, not a query per date
        self.assertEqual(pr['moderate_dates'], ['2026-10-31'])
        self.assertEqual(pr['easy_sessions'], 1)
        # A black-hole session is not Easy: 1 Easy of 2 classified = 50%, not 100%.
        self.assertEqual(pr['easy_pct'], 50.0)


class TestDaysSinceRestPrompt(unittest.TestCase):
    def test_states_last_rest_and_completed_days(self):
        text = ums.format_days_since_rest_for_prompt({
            'days_since_rest': 3,
            'last_rest_date': date(2026, 10, 30),
            'rest_as_of_date': date(2026, 11, 2)})
        self.assertIn('last rest day Fri Oct 30', text)
        self.assertIn('2 training days completed since (Sat Oct 31-Sun Nov 01)', text)
        self.assertIn('Mon Nov 02 is day 3', text)

    def test_missing_metrics(self):
        self.assertEqual(ums.format_days_since_rest_for_prompt(None), 'N/A')


if __name__ == '__main__':
    unittest.main()
