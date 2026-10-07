"""Stage boundaries, masters taper shift, and single-source-of-truth guards."""
import os
import sys
import unittest
from datetime import date, timedelta
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from training_stage import calculate_training_stage, in_race_preparation_window
import workout_library

RACE = date(2026, 11, 14)


def stage_at(days_out, age=None):
    return calculate_training_stage(RACE, RACE - timedelta(days=days_out), age)['stage']


class TestStageBoundaries(unittest.TestCase):
    def test_order_counting_back_from_race(self):
        self.assertEqual(stage_at(-1), 'recovery')
        self.assertEqual(stage_at(0), 'peak')
        self.assertEqual(stage_at(13), 'peak')
        self.assertEqual(stage_at(14), 'taper')
        self.assertEqual(stage_at(20), 'taper')
        self.assertEqual(stage_at(21), 'specificity')
        self.assertEqual(stage_at(55), 'specificity')
        self.assertEqual(stage_at(56), 'build')
        self.assertEqual(stage_at(83), 'build')
        self.assertEqual(stage_at(84), 'base')

    def test_masters_taper_starts_a_week_earlier(self):
        self.assertEqual(stage_at(24, age=59), 'specificity')
        self.assertEqual(stage_at(24, age=60), 'taper')
        self.assertEqual(stage_at(27, age=65), 'taper')
        self.assertEqual(stage_at(28, age=65), 'specificity')
        self.assertEqual(stage_at(13, age=65), 'peak')

    def test_peak_is_explained_as_readiness_not_load(self):
        info = calculate_training_stage(RACE, RACE - timedelta(days=7))
        self.assertIn('readiness', info['stage_description'].lower())
        self.assertIn('not peak training load', info['details'])

    def test_every_stage_has_details(self):
        for d in (-3, 5, 15, 30, 60, 100):
            self.assertTrue(calculate_training_stage(RACE, RACE - timedelta(days=d))['details'])

    def test_race_preparation_window(self):
        def window(days, age=None):
            return in_race_preparation_window(calculate_training_stage(RACE, RACE - timedelta(days=days), age))
        self.assertTrue(window(3))
        self.assertTrue(window(18))
        self.assertTrue(window(27))        # final specificity week before a 3-wk taper
        self.assertFalse(window(28))
        self.assertTrue(window(34, age=62))  # final specificity week before a 4-wk taper
        self.assertFalse(window(35, age=62))
        self.assertFalse(window(-2))


class TestLactateShuttleWindow(unittest.TestCase):
    """The ~10-day shuttle straddles taper/peak and must fire from days-to-race."""

    def rules(self, days_out, age=None):
        info = calculate_training_stage(RACE, RACE - timedelta(days=days_out), age)
        return workout_library.get_phase_interval_rules(
            info['stage'], info['weeks_until_race'], RACE - timedelta(days=days_out))

    def test_shuttle_fires_in_week_containing_race_minus_10(self):
        for d in range(10, 17):
            self.assertEqual(self.rules(d)['protocol_key'], 'lactate_shuttle', f'{d} days out')

    def test_no_shuttle_outside_window(self):
        for d in (3, 7, 9, 17, 20):
            self.assertFalse(self.rules(d)['interval_allowed'], f'{d} days out')


class TestSingleSourceOfTruth(unittest.TestCase):
    def test_agentic_tool_reports_canonical_stage(self):
        import coach_recommendations
        import llm_context_tools
        today = date(2026, 10, 6)
        race = today + timedelta(days=10)
        row = {'id': 1, 'race_name': 'Rim Run', 'race_date': race, 'race_type': 'trail',
               'priority': 'A', 'target_time': None, 'notes': None, 'elevation_gain_feet': None,
               'distance_miles': None}

        with mock.patch.object(llm_context_tools, 'execute_query', return_value=[row]), \
             mock.patch.object(coach_recommendations, 'execute_query',
                               side_effect=lambda q, *a, **k: [{'age': 62}] if 'age' in q else [row]), \
             mock.patch.object(coach_recommendations, 'get_app_current_date', return_value=today):
            tool = llm_context_tools.get_race_goals(user_id=1)

        canonical = calculate_training_stage(race, today, 62)
        self.assertEqual(tool['training_stage'], canonical['stage'])
        self.assertEqual(tool['training_stage'], 'peak')
        self.assertEqual(tool['weeks_to_a_race'], canonical['weeks_until_race'])

    def test_taper_context_gated_on_a_race_stage_not_nearest_race(self):
        import coach_recommendations
        import llm_recommendations_module as lrm
        target = '2026-10-06'

        def load(goals):
            with mock.patch.object(coach_recommendations, 'get_race_goals', return_value=goals), \
                 mock.patch.object(coach_recommendations, 'execute_query', return_value=[{'age': 50}]):
                return lrm._load_coaching_context(1, 'GREEN', target)

        c_race_close = [{'race_name': 'C', 'race_date': '2026-10-20', 'priority': 'C'},
                        {'race_name': 'A', 'race_date': '2026-12-20', 'priority': 'A'}]
        a_race_in_taper = [{'race_name': 'A', 'race_date': '2026-10-24', 'priority': 'A'}]
        self.assertNotIn('TAPER AND RACE PREPARATION', load(c_race_close))
        self.assertIn('TAPER AND RACE PREPARATION', load(a_race_in_taper))

    def test_no_local_stage_bucketing_outside_training_stage(self):
        app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        for fname in ('llm_context_tools.py', 'strava_app.py', 'coach_recommendations.py'):
            with open(os.path.join(app_dir, fname), encoding='utf-8') as f:
                src = f.read()
            self.assertNotIn("training_stage = 'taper'", src, fname)
            self.assertNotIn('def _calculate_training_stage', src, fname)


if __name__ == '__main__':
    unittest.main()
