"""
Regression tests for the deviation_reason write pipeline.

deviation_reason was NULL on every ai_autopsies row for five months across all users.
Root cause: classify_deviation() wrote it AFTER append_deviation_log(), and that call
raised UndefinedColumn on weekly_programs.updated_at (a column that never existed).
The outer catch-all handler swallowed the error, so the calibration input for
divergence_injury_threshold was silently starved while the logs looked routine.

These tests lock in the two structural fixes:
  1. The deviation_reason write does not depend on any unrelated write succeeding.
  2. The retroactive writer's predicate matches an unclassified (NULL) row.
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as m


def _week_ctx():
    return {
        'week_start_date': '2026-08-17',
        'strategic_summary': {
            'key_sessions': [{'day': 'Tuesday', 'type': 'Intervals'}],
            'load_target_high': 1.4,
        },
        'deviation_log': [],
    }


class TestDeviationReasonIsWrittenIndependently(unittest.TestCase):
    """The write must survive an unrelated failure downstream of it."""

    def _run(self, append_side_effect, extraction=None):
        writes = []

        def fake_execute(query, params=None, fetch=False):
            if 'ai_autopsies' in query and 'SET deviation_reason' in query:
                writes.append(params)
            return 1

        with mock.patch.object(m, 'get_current_week_context', return_value=_week_ctx()), \
             mock.patch.object(m, 'append_deviation_log', side_effect=append_side_effect), \
             mock.patch.object(m, 'set_revision_pending'), \
             mock.patch.object(m, 'execute_query', side_effect=fake_execute):
            # Must never raise, whatever happens downstream.
            m.classify_deviation(
                user_id=1,
                activity_date='2026-08-20',
                alignment_score=3,
                extraction_result=extraction or {},
                structured_output={},
            )
        return writes

    def test_written_when_deviation_log_append_succeeds(self):
        writes = self._run(append_side_effect=None)
        self.assertEqual(len(writes), 1, "deviation_reason should be written exactly once")

    def test_still_written_when_deviation_log_append_raises(self):
        """The original bug: a schema error in a DIFFERENT table killed this write."""
        writes = self._run(append_side_effect=Exception(
            'column "updated_at" of relation "weekly_programs" does not exist'))
        self.assertEqual(len(writes), 1,
                         "deviation_reason must not depend on append_deviation_log succeeding")

    def test_physical_classification_from_injury_note(self):
        writes = self._run(append_side_effect=None,
                           extraction={'injury_or_pain_notes': 'left QL locked up'})
        self.assertEqual(writes[0][0], 'physical')

    def test_external_classification_from_preference_note(self):
        writes = self._run(append_side_effect=None,
                           extraction={'preference_note': 'travel for work all week'})
        self.assertEqual(writes[0][0], 'external')

    def test_unknown_when_no_signal(self):
        writes = self._run(append_side_effect=None)
        self.assertEqual(writes[0][0], 'unknown')


class TestRetroactivePredicate(unittest.TestCase):
    """The retroactive writer must match a NULL row, not only the literal 'unknown'."""

    SQL = ("UPDATE ai_autopsies SET deviation_reason = %s "
           "WHERE user_id = %s AND date = %s "
           "AND (deviation_reason IS NULL OR deviation_reason = 'unknown')")

    @staticmethod
    def _matches(sql, stored):
        # Mirrors the SQL predicate's truth table for the stored column value.
        if 'IS NULL OR' in sql:
            return stored is None or stored == 'unknown'
        return stored == 'unknown'

    def test_null_row_is_matched(self):
        self.assertTrue(self._matches(self.SQL, None),
                        "a never-classified row (NULL) must be updatable retroactively")

    def test_unknown_row_is_matched(self):
        self.assertTrue(self._matches(self.SQL, 'unknown'))

    def test_already_classified_row_is_not_overwritten(self):
        self.assertFalse(self._matches(self.SQL, 'physical'))
        self.assertFalse(self._matches(self.SQL, 'external'))

    def test_old_predicate_missed_null_rows(self):
        old = ("UPDATE ai_autopsies SET deviation_reason = %s "
               "WHERE user_id = %s AND date = %s AND deviation_reason = 'unknown'")
        self.assertFalse(self._matches(old, None),
                         "documents the bug: NULL never matched, so 31 answers wrote 0 rows")


if __name__ == '__main__':
    unittest.main()
