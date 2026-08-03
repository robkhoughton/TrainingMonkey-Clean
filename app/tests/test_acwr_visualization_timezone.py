"""
Tests locking the /api/visualization/sensitivity endpoint's default
analysis_date to the timezone-aware "today," not naive server-clock UTC.

UTC midnight lands at 5pm Pacific (PDT). A request after 5pm Pacific with no
explicit analysis_date used to default to bare datetime.now().date() —
tomorrow's date in UTC — shifting the whole 84-day lookback window used for
the ACWR sensitivity chart by a day. Locks the fix: the default now comes
from get_user_current_date(user_id), which is Pacific-anchored.
"""
import os
import sys
import datetime
from unittest import mock
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from flask import Flask
import acwr_visualization_routes as routes_module


class TestSensitivityAnalysisDateDefaultTimezone(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(routes_module.acwr_visualization_routes)
        self.client = self.app.test_client()

    @mock.patch('db_utils.execute_query')
    @mock.patch('timezone_utils.get_user_current_date')
    def test_missing_analysis_date_defaults_to_user_date_not_utc_now(
        self, mock_user_date, mock_execute_query
    ):
        # Simulate a request at 7:41pm Pacific — bare datetime.now().date()
        # would already read tomorrow (UTC). The query window must be
        # anchored to get_user_current_date, not the server clock.
        mock_user_date.return_value = datetime.date(2026, 8, 1)
        mock_execute_query.return_value = [
            {'date': datetime.date(2026, 8, 1), 'total_load_miles': 5.0, 'trimp': 100.0}
        ]

        response = self.client.post('/api/visualization/sensitivity', json={'user_id': 1})

        mock_user_date.assert_called_once_with(1)
        query_args = mock_execute_query.call_args[0][1]
        called_end_date = query_args[2]
        self.assertEqual(called_end_date, '2026-08-01')


if __name__ == '__main__':
    unittest.main()
