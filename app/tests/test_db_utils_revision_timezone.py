"""
Tests locking db_utils.apply_revision() / dismiss_revision() to the
timezone-aware "today," not naive server-clock UTC.

UTC midnight lands at 5pm Pacific (PDT). A revision approved/dismissed after
5pm Pacific used to get logged with bare datetime.now().date() — tomorrow's
date in UTC — so the deviation_log entry recorded the wrong calendar day for
the athlete's action. Locks the fix: both now derive "today" from
get_user_current_date(user_id), which is Pacific-anchored.
"""
import os
import sys
import datetime
from unittest import mock
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import db_utils


class TestApplyRevisionTimezone(unittest.TestCase):
    @mock.patch.object(db_utils, 'execute_query')
    @mock.patch('timezone_utils.get_user_current_date')
    def test_apply_revision_uses_user_date_not_utc_now(self, mock_user_date, mock_execute_query):
        # Simulate a request at 7:41pm Pacific — bare datetime.now().date()
        # would already read tomorrow (UTC). The logged "date" must come from
        # get_user_current_date, not the server clock.
        mock_user_date.return_value = datetime.date(2026, 8, 1)
        mock_execute_query.return_value = None

        db_utils.apply_revision(user_id=1, week_start='2026-07-27')

        mock_user_date.assert_called_once_with(1)
        query_args = mock_execute_query.call_args[0][1]
        approval_entry_json = query_args[0]
        self.assertIn('2026-08-01', approval_entry_json)


class TestDismissRevisionTimezone(unittest.TestCase):
    @mock.patch.object(db_utils, 'execute_query')
    @mock.patch('timezone_utils.get_user_current_date')
    def test_dismiss_revision_uses_user_date_not_utc_now(self, mock_user_date, mock_execute_query):
        mock_user_date.return_value = datetime.date(2026, 8, 1)
        mock_execute_query.return_value = None

        db_utils.dismiss_revision(user_id=1, week_start='2026-07-27')

        mock_user_date.assert_called_once_with(1)
        query_args = mock_execute_query.call_args[0][1]
        dismissal_entry_json = query_args[0]
        self.assertIn('2026-08-01', dismissal_entry_json)


if __name__ == '__main__':
    unittest.main()
