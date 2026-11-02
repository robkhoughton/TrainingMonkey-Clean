"""
One session-intensity classification, one zone source, one readiness computation.

- The dominance-rule classifiers (_classify_activity_intensity, classify_workout_by_hr_zones)
  that read the stored static-zone columns are gone; every consumer uses
  classify_session_dates -> session_zone_times_for_dates -> classify_session_polarized.
- get_ans_readiness_for_dates must give each date exactly what get_ans_readiness gives.
- long_run_violations enforces the long-run limits from the plan's own numbers.
"""
import inspect
import os
import sys
import unittest
from datetime import date, timedelta
from unittest import mock

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import coach_recommendations as cr
import llm_recommendations_module as m
import readiness_engine as re_


class TestNoParallelClassifiers(unittest.TestCase):
    def test_dominance_classifiers_removed(self):
        self.assertFalse(hasattr(m, '_classify_activity_intensity'))
        src = open(os.path.join(os.path.dirname(m.__file__), 'strava_app.py'), encoding='utf-8').read()
        self.assertNotIn('def classify_workout_by_hr_zones', src)

    def test_consumers_use_shared_classifier(self):
        for fn in (m.analyze_pattern_flags, m.load_divergence_projection,
                   m.analyze_training_patterns, m.compute_weekly_polarized_ratio):
            self.assertIn('classify_session_dates(', inspect.getsource(fn), fn.__name__)


class TestReadinessBatchMatchesSingle(unittest.TestCase):
    def _frame(self, end, days):
        dates = [end - timedelta(days=i) for i in range(days)][::-1]
        return pd.DataFrame({
            'date': pd.to_datetime(dates),
            'hrv': [50 + (i % 7) for i in range(days)],
            'rhr': [45 + (i % 3) for i in range(days)],
            'sleep_quality': [3] * days, 'sleep_score': [80] * days, 'spo2': [97] * days,
        })

    def test_each_date_equals_single_call(self):
        end = date(2026, 11, 1)
        full = self._frame(end, 140)

        def loader(user_id, days=90, as_of_date=None):
            lo = pd.Timestamp(as_of_date - timedelta(days=days))
            return full[(full['date'] >= lo) & (full['date'] <= pd.Timestamp(as_of_date))].reset_index(drop=True)

        targets = [end - timedelta(days=i) for i in (0, 3, 10, 30)]
        with mock.patch.object(re_, 'load_athlete_readiness_dataframe', side_effect=loader):
            batch = re_.get_ans_readiness_for_dates(1, targets)
            for d in targets:
                self.assertEqual(batch[d], re_.get_ans_readiness(1, as_of_date=d), d)


def _plan(long_miles, other_miles):
    days = [{'date': f'2026-11-0{i + 2}', 'workout_type': 'Easy Run', 'distance_miles': mi}
            for i, mi in enumerate(other_miles)]
    days.append({'date': '2026-11-09', 'workout_type': 'Long Run', 'distance_miles': long_miles})
    return {'daily_program': days}


class TestLongRunLimits(unittest.TestCase):
    def test_one_third_of_week(self):
        # 11 mi long run in a 32 mi week: other days total 21, so the cap is 10.5.
        v = cr.long_run_violations(_plan(11.0, [5, 4, 6.5, 4, 0, 1.5]), ceiling=11.7)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]['cap'], 10.5)

    def test_ceiling_binds_first(self):
        v = cr.long_run_violations(_plan(12.0, [8, 8, 8, 8, 0, 0]), ceiling=11.7)
        self.assertEqual(v[0]['cap'], 11.5)
        self.assertIn('ceiling', v[0]['reason'])

    def test_compliant_plan(self):
        self.assertEqual(cr.long_run_violations(_plan(10.0, [5, 5, 5, 5, 0, 0]), ceiling=11.7), [])


if __name__ == '__main__':
    unittest.main()
