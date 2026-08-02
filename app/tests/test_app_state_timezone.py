"""
Tests locking get_app_state() and _sync_recent_strava_activities() to the
timezone-aware "today," not naive server-clock UTC.

UTC midnight lands at 5pm Pacific (PDT). Any request after 5pm Pacific used to
get tomorrow's date from bare datetime.now(), so the morning-entry check (and
the 48h Strava sync window) silently rolled over hours early — a journal
entry saved that evening filed itself under the wrong day, making the next
morning's actual check-in look already-done and suppressing the "log your
morning status" modal. Locks the fix: both now derive "today" from
get_user_current_date(user_id), which is Pacific-anchored.
"""
import os
import sys
import datetime
from unittest import mock
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import strava_app


class MockCurrentUser:
    def __init__(self, user_id=1):
        self.id = user_id
        self.is_authenticated = True


class TestSyncRecentStravaActivitiesTimezone(unittest.TestCase):
    @mock.patch.object(strava_app, 'update_moving_averages')
    @mock.patch.object(strava_app, 'ensure_daily_records')
    @mock.patch.object(strava_app, 'process_activities_for_date_range')
    @mock.patch.object(strava_app, 'SimpleTokenManager')
    @mock.patch.object(strava_app.db_utils, 'execute_query')
    @mock.patch('timezone_utils.get_user_current_date')
    def test_sync_window_anchored_to_user_date_not_utc_now(
        self, mock_user_date, mock_execute_query, mock_token_mgr,
        mock_process, mock_ensure, mock_update_avg
    ):
        # Simulate a request at 7:41pm Pacific — server-local UTC datetime.now()
        # would already read tomorrow. get_user_current_date must be what
        # actually drives the sync window, not a bare datetime.now() call.
        mock_user_date.return_value = datetime.date(2026, 8, 1)
        mock_execute_query.return_value = [{'resting_hr': 44, 'max_hr': 178, 'gender': 'male'}]
        mock_client = mock.Mock()
        mock_token_mgr.return_value.get_working_strava_client.return_value = mock_client

        strava_app._sync_recent_strava_activities(user_id=1)

        mock_user_date.assert_called_once_with(1)
        called_start, called_end = mock_process.call_args[0][1], mock_process.call_args[0][2]
        self.assertEqual(called_end, '2026-08-01')
        self.assertEqual(called_start, '2026-07-30')


class TestGetAppStateTimezone(unittest.TestCase):
    @mock.patch.object(strava_app, '_sync_recent_strava_activities')
    @mock.patch.object(strava_app, 'get_last_activity_journal_status')
    @mock.patch.object(strava_app.db_utils, 'execute_query')
    @mock.patch('timezone_utils.get_user_current_date')
    def test_morning_entry_check_uses_user_date_not_utc_now(
        self, mock_user_date, mock_execute_query, mock_journal_status, mock_sync
    ):
        # No activity pending journal, and no morning entry yet for the
        # user's actual today — route should be 'morning'.
        mock_user_date.return_value = datetime.date(2026, 8, 2)
        mock_journal_status.return_value = {'reason': 'no_recent_activity', 'has_activity': False}
        mock_execute_query.return_value = []

        with strava_app.app.test_request_context('/api/app-state'):
            with mock.patch('strava_app.current_user', MockCurrentUser(user_id=1)):
                # Call the undecorated function directly — @login_required
                # (flask_login's real decorator here, not the USE_MOCK_DB
                # no-op) checks its own internal current_user and would
                # reject this synthetic request before the patch above ever
                # takes effect inside the function body.
                response = strava_app.get_app_state.__wrapped__()

        mock_user_date.assert_called_once_with(1)
        # execute_query's morning-entry lookup must be keyed on the mocked
        # user-local date, not whatever datetime.now() would have produced.
        query_args = mock_execute_query.call_args[0][1]
        self.assertIn('2026-08-02', query_args)
        self.assertEqual(response.get_json()['route'], 'morning')


if __name__ == '__main__':
    unittest.main()
