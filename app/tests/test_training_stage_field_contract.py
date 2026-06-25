"""
Contract tests for race-context field naming (refactor Phase 1).

Guards the canonical "weeks to race" key on get_current_training_stage. The
"no race on the calendar" bug class was caused by a reader querying the legacy
key `weeks_to_race` and getting None *exactly when a race existed*, because the
function returned `weeks_to_race` on its no-race path but `weeks_until_race` on
its has-race path. These tests lock both paths to the single canonical key.

See docs/refactor_plan_race_context_2026-06-24.md.
"""
import os
import sys
import types
import unittest
from unittest import mock

# Make app modules importable regardless of where pytest is invoked from.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# db_utils enforces DATABASE_URL at import time. These tests mock every DB call,
# so a dummy URL satisfies the import guard without opening a connection.
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import coach_recommendations


class TestTrainingStageFieldContract(unittest.TestCase):
    CANONICAL_KEY = 'weeks_until_race'
    LEGACY_KEY = 'weeks_to_race'

    @mock.patch.object(coach_recommendations, 'get_race_goals', return_value=[])
    def test_no_race_path_exposes_canonical_key(self, _mock_goals):
        info = coach_recommendations.get_current_training_stage(user_id=1)
        self.assertIn(self.CANONICAL_KEY, info)
        self.assertNotIn(self.LEGACY_KEY, info)
        self.assertIsNone(info[self.CANONICAL_KEY])
        # Casing parity with the has-race path (lowercase 'base').
        self.assertEqual(info['stage'], 'base')

    @mock.patch.object(coach_recommendations, 'get_race_goals')
    def test_has_race_path_exposes_canonical_key(self, mock_goals):
        mock_goals.return_value = [{
            'race_name': 'Mountain Lakes 100',
            'race_date': '2026-09-19',
            'priority': 'A',
        }]
        fake_stage = {
            'stage': 'base',
            'stage_description': 'Base building phase',
            'week_number': 4,
            'total_weeks': 16,
            'weeks_until_race': 12.4,
            'days_until_race': 87,
        }
        # get_current_training_stage does `from strava_app import _calculate_training_stage`
        # at call time; inject a lightweight stub so we don't import the heavy app module.
        fake_strava = types.ModuleType('strava_app')
        fake_strava._calculate_training_stage = lambda race_date, current_date: dict(fake_stage)
        with mock.patch.dict(sys.modules, {'strava_app': fake_strava}):
            info = coach_recommendations.get_current_training_stage(user_id=1)

        self.assertIn(self.CANONICAL_KEY, info)
        self.assertNotIn(self.LEGACY_KEY, info)
        self.assertIsNotNone(info[self.CANONICAL_KEY])
        self.assertEqual(info['race_name'], 'Mountain Lakes 100')

    @mock.patch.object(coach_recommendations, 'get_race_goals', return_value=[])
    def test_no_race_path_has_shape_parity(self, _mock_goals):
        """No-race and has-race paths must expose the same keys readers rely on."""
        info = coach_recommendations.get_current_training_stage(user_id=1)
        for key in ('stage', 'weeks_until_race', 'race_name', 'priority'):
            self.assertIn(key, info)


if __name__ == '__main__':
    unittest.main()
