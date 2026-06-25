"""
Tests for the canonical race-context builders (refactor Phase 2).

These builders are the single source of truth for race context in every coaching
prompt. They replace ~10 ad-hoc get_race_goals/format inline injections that had
drifted apart and caused the "no race on the calendar" bug. The tests lock their
contract so future prompt paths can rely on them.

See docs/refactor_plan_race_context_2026-06-24.md.
"""
import os
import sys
import unittest
from datetime import date
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# db_utils enforces DATABASE_URL at import time; mocks cover every DB call.
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import coach_recommendations as cr

A_RACE = {
    'race_name': 'Mountain Lakes 100', 'race_date': '2026-09-19', 'priority': 'A',
    'race_type': 'Trail', 'target_time': '24:00', 'elevation_gain_feet': 10000,
    'distance_miles': 100.0,
}
PAST_RACE = {
    'race_name': 'Old 50K', 'race_date': '2026-01-01', 'priority': 'C',
    'race_type': '50K', 'target_time': None, 'elevation_gain_feet': None,
    'distance_miles': 31.0,
}
# get_app_current_date returns a date object; format_race_goals_for_prompt does
# date arithmetic with it, so the mock must too.
TODAY = date(2026, 6, 25)


class TestUpcomingRacesBlock(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(cr, 'get_app_current_date', return_value=TODAY)
        self.addCleanup(patcher.stop)
        patcher.start()

    @mock.patch.object(cr, 'get_race_goals', return_value=[PAST_RACE, A_RACE])
    def test_filters_past_and_includes_upcoming(self, _g):
        block = cr.build_upcoming_races_block(1)
        self.assertIn('### RACE GOALS', block)
        self.assertIn('Mountain Lakes 100', block)
        self.assertNotIn('Old 50K', block)

    @mock.patch.object(cr, 'get_race_goals', return_value=[PAST_RACE])
    def test_returns_empty_when_no_upcoming(self, _g):
        self.assertEqual(cr.build_upcoming_races_block(1), "")

    @mock.patch.object(cr, 'get_race_goals', side_effect=RuntimeError('db down'))
    def test_swallows_errors_safely(self, _g):
        self.assertEqual(cr.build_upcoming_races_block(1), "")


class TestRaceDayBlock(unittest.TestCase):
    @mock.patch.object(cr, 'get_race_on_date', return_value=A_RACE)
    def test_race_day_block_present_when_race_today(self, _r):
        block = cr.build_race_day_block(1, '2026-09-19')
        self.assertIn('### TODAY IS RACE DAY', block)
        self.assertIn('Mountain Lakes 100', block)

    @mock.patch.object(cr, 'get_race_on_date', return_value=None)
    def test_empty_when_no_race_today(self, _r):
        self.assertEqual(cr.build_race_day_block(1, '2026-06-25'), "")

    @mock.patch.object(cr, 'get_race_on_date', side_effect=RuntimeError('db down'))
    def test_swallows_errors_safely(self, _r):
        self.assertEqual(cr.build_race_day_block(1, '2026-06-25'), "")


class TestGetUpcomingRaceGoals(unittest.TestCase):
    @mock.patch.object(cr, 'get_app_current_date', return_value=TODAY)
    @mock.patch.object(cr, 'get_race_goals', return_value=[PAST_RACE, A_RACE])
    def test_returns_only_upcoming(self, _g, _d):
        upcoming = cr.get_upcoming_race_goals(1)
        self.assertEqual([r['race_name'] for r in upcoming], ['Mountain Lakes 100'])


if __name__ == '__main__':
    unittest.main()
