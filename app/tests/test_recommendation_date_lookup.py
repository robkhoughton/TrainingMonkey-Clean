"""
Tests for get_todays_decision_for_date's date-attribution contract.

This function used to fall back to "most recent recommendation regardless of
date" when no exact target_date match existed, silently mislabeling a different
date's content as the requested date's prescribed action — the same bug class
the (now-deleted) get_unified_recommendation_for_date docstring called a
CRITICAL FIX, except this one was still live and feeding generate_autopsy_for_date's
prescribed-action comparison. It now returns None on no match instead, and the
caller's guard (`if not prescribed_action:`) relies on that contract.
"""
import os
import sys
import datetime
from unittest import mock
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import strava_app


class TestGetTodaysDecisionForDate(unittest.TestCase):
    USER_ID = 1

    def test_no_match_returns_none_not_a_different_dates_content(self):
        with mock.patch.object(strava_app.db_utils, 'execute_query', return_value=[]):
            result = strava_app.get_todays_decision_for_date(
                datetime.date(2026, 6, 27), self.USER_ID
            )
        self.assertIsNone(result)

    def test_match_returns_formatted_text_for_past_date(self):
        row = {'daily_recommendation': 'Easy 5 mile run.'}
        with mock.patch.object(strava_app.db_utils, 'execute_query', return_value=[row]), \
             mock.patch('timezone_utils.get_user_current_date', return_value=datetime.date(2026, 6, 28)):
            result = strava_app.get_todays_decision_for_date(
                datetime.date(2026, 6, 27), self.USER_ID
            )
        self.assertIn('Easy 5 mile run.', result)
        self.assertIn('WORKOUT for', result)

    def test_exception_returns_none_not_an_error_string(self):
        with mock.patch.object(strava_app.db_utils, 'execute_query', side_effect=RuntimeError('db down')):
            result = strava_app.get_todays_decision_for_date(
                datetime.date(2026, 6, 27), self.USER_ID
            )
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
