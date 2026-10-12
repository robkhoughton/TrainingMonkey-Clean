"""
Tests for the recovery gate: under overtraining_risk, Zone 1 easy sessions are allowed
(instead of rest only) when the worst Pain Score in the last 3 days is below 40% and no
journal note in that window signals injury or pain. Missing data, a positive veto, or a
failed veto keep the floor at rest.

Decided by Rob 2026-10-12. See .scratch/divergence-rest-projection/spec.md.
"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from recovery_gate import evaluate_recovery_gate

TARGET = date(2026, 10, 12)

# User 1's real journal, 2026-10-10 .. 2026-10-12.
USER1_JOURNAL = [
    {'date': date(2026, 10, 10), 'pain_percentage': 0,
     'notes': 'Aerobic drift test at the Avery track. Maintained RPE of 3 or 4.'},
    {'date': date(2026, 10, 11), 'pain_percentage': None,
     'notes': 'Decided to rest due to scheduled rest day.  Legs felt fresh in the afternoon. '
              'Mild tightness in right calf.  Minor bilateral lower leg edema.'},
    {'date': date(2026, 10, 12), 'pain_percentage': None, 'notes': None},
]


def no_signal(notes):
    return False


def signal(notes):
    return True


def broken(notes):
    raise RuntimeError('classifier unavailable')


class TestRecoveryGate(unittest.TestCase):

    def test_user1_today_passes_tightness_and_edema_without_pain_are_not_injury(self):
        seen = []
        gate = evaluate_recovery_gate(USER1_JOURNAL, TARGET, lambda notes: seen.extend(notes) or False)
        self.assertTrue(gate['passed'])
        self.assertEqual(gate['max_pain'], 0)
        self.assertEqual(gate['veto'], 'negative')
        # the rest-day note was read by the veto
        self.assertTrue(any('edema' in n for _, n in seen))

    def test_pain_below_40_passes(self):
        rows = [{'date': date(2026, 10, 11), 'pain_percentage': 39, 'notes': None}]
        self.assertTrue(evaluate_recovery_gate(rows, TARGET, no_signal)['passed'])

    def test_pain_at_40_fails(self):
        rows = [{'date': date(2026, 10, 11), 'pain_percentage': 40, 'notes': None}]
        gate = evaluate_recovery_gate(rows, TARGET, no_signal)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['reason'], 'pain')
        self.assertEqual(gate['max_pain'], 40)

    def test_worst_reading_in_window_counts(self):
        rows = [{'date': date(2026, 10, 10), 'pain_percentage': 60, 'notes': None},
                {'date': date(2026, 10, 12), 'pain_percentage': 0, 'notes': None}]
        self.assertFalse(evaluate_recovery_gate(rows, TARGET, no_signal)['passed'])

    def test_readings_older_than_three_days_are_ignored(self):
        rows = [{'date': date(2026, 10, 9), 'pain_percentage': 80, 'notes': None},
                {'date': date(2026, 10, 10), 'pain_percentage': 0, 'notes': None}]
        self.assertTrue(evaluate_recovery_gate(rows, TARGET, no_signal)['passed'])

    def test_no_pain_readings_fails(self):
        rows = [{'date': date(2026, 10, 11), 'pain_percentage': None, 'notes': 'felt good'}]
        gate = evaluate_recovery_gate(rows, TARGET, no_signal)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['reason'], 'no_pain_readings')

    def test_positive_veto_fails(self):
        gate = evaluate_recovery_gate(USER1_JOURNAL, TARGET, signal)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['reason'], 'journal_injury_signal')
        self.assertEqual(gate['veto'], 'positive')

    def test_veto_error_fails_safe(self):
        gate = evaluate_recovery_gate(USER1_JOURNAL, TARGET, broken)
        self.assertFalse(gate['passed'])
        self.assertEqual(gate['veto'], 'error')

    def test_no_notes_means_no_classifier_call(self):
        rows = [{'date': date(2026, 10, 11), 'pain_percentage': 0, 'notes': '  '}]
        gate = evaluate_recovery_gate(rows, TARGET, broken)
        self.assertTrue(gate['passed'])
        self.assertEqual(gate['veto'], 'no_notes')

    def test_pain_failure_skips_the_classifier(self):
        rows = [{'date': date(2026, 10, 11), 'pain_percentage': 50, 'notes': 'sore'}]
        gate = evaluate_recovery_gate(rows, TARGET, broken)
        self.assertEqual(gate['reason'], 'pain')
        self.assertEqual(gate['veto'], 'not_run')


if __name__ == '__main__':
    unittest.main()
