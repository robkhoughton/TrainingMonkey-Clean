"""Long-run limits: distance ceiling (Frandsen 2025), load-miles ceiling (vert), weekly 1/3 share."""
import os
import sys
import unittest
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import coach_recommendations
from coach_recommendations import format_long_run_guideline, get_long_run_limits, long_run_limits
from external_load import RUNNING_ELEVATION_FACTOR, running_load_miles


class TestRunningLoadMiles(unittest.TestCase):
    def test_every_750_ft_counts_one_mile(self):
        self.assertEqual(RUNNING_ELEVATION_FACTOR, 750.0)
        self.assertAlmostEqual(running_load_miles(12.0, 4500.0), 18.0)
        self.assertAlmostEqual(running_load_miles(10.0, 0.0), 10.0)


class TestLongRunLimits(unittest.TestCase):
    def test_both_ceilings_are_ten_percent_over_their_own_maximum(self):
        # Longest run 14 mi flat; biggest run 12 mi / 4,500 ft = 18 load miles: different runs.
        limits = long_run_limits(14.0, 18.0)
        self.assertEqual(limits.distance_ceiling, 15.4)
        self.assertEqual(limits.load_ceiling, 19.8)

    def test_maxima_come_from_independent_aggregates(self):
        with mock.patch.object(coach_recommendations, 'execute_query',
                               return_value=[{'max_distance': 14.0, 'max_load': 18.0}]) as q:
            limits = get_long_run_limits(1, date(2026, 11, 8))
        sql = q.call_args[0][0]
        self.assertIn('MAX(distance_miles)', sql)
        self.assertIn('MAX(total_load_miles)', sql)
        self.assertEqual((limits.max_distance_miles, limits.max_load_miles), (14.0, 18.0))

    def test_no_recent_running_returns_none(self):
        with mock.patch.object(coach_recommendations, 'execute_query',
                               return_value=[{'max_distance': None, 'max_load': None}]):
            self.assertIsNone(get_long_run_limits(1, date(2026, 11, 8)))


class TestLongRunGuideline(unittest.TestCase):
    def test_states_all_three_limits_with_computed_values(self):
        text = format_long_run_guideline(long_run_limits(14.0, 18.0))
        self.assertIn('15.4 miles', text)
        self.assertIn('19.8 load miles', text)
        self.assertIn('1/3 of the week\'s total load miles', text)
        self.assertIn('elevation_gain_feet / 750', text)
        self.assertIn('all three limits', text)

    def test_no_history_falls_back_to_conservative_cap(self):
        self.assertIn('no more than 10 miles', format_long_run_guideline(None))


if __name__ == '__main__':
    unittest.main()
