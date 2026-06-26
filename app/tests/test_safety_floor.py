"""
Tests for the safety-floor guardrail and the count-based recent-alignment signal
(Phase: safety floor + judgment).

The deterministic floor makes "rest when the verdict mandates rest" non-negotiable —
the LLM cannot rationalize a training day past it. Recent alignment is a raw number
over the last N autopsies by count (no fragile 3-day window, no word buckets).
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as m


class TestFloor(unittest.TestCase):
    def test_floor_mapping(self):
        self.assertEqual(m.mandated_floor('overtraining_risk'), 'rest')
        self.assertEqual(m.mandated_floor('mandatory_rest'), 'rest')
        self.assertEqual(m.mandated_floor('high_acwr_risk'), 'reduce')
        self.assertEqual(m.mandated_floor('recovery_needed'), 'reduce')
        self.assertEqual(m.mandated_floor('normal_progression'), 'train_allowed')
        self.assertEqual(m.mandated_floor('undertraining_opportunity'), 'train_allowed')

    def test_train_under_rest_floor_is_violation(self):
        self.assertTrue(m.floor_violation('overtraining_risk', 'train'))
        self.assertTrue(m.floor_violation('overtraining_risk', 'reduce'))  # rest floor: only rest allowed
        self.assertFalse(m.floor_violation('overtraining_risk', 'rest'))

    def test_train_under_reduce_floor_is_violation(self):
        self.assertTrue(m.floor_violation('high_acwr_risk', 'train'))
        self.assertFalse(m.floor_violation('high_acwr_risk', 'reduce'))
        self.assertFalse(m.floor_violation('high_acwr_risk', 'rest'))

    def test_train_allowed_never_violates(self):
        for action in ('train', 'reduce', 'rest', 'maintain', None):
            self.assertFalse(m.floor_violation('normal_progression', action))

    def test_missing_action_does_not_falsely_violate(self):
        # No structured action -> can't assert a violation.
        self.assertFalse(m.floor_violation('overtraining_risk', None))


class TestSafeFallback(unittest.TestCase):
    def test_rest_fallback(self):
        cm = {'external_acwr': 1.75, 'internal_acwr': 2.13, 'normalized_divergence': -0.20}
        out = m._safe_floor_recommendation('overtraining_risk', cm, '2026-06-27')
        self.assertEqual(out['structured_output']['decision']['action'], 'rest')
        self.assertIn('rest day', out['daily_recommendation'].lower())
        self.assertEqual(out['structured_output']['meta']['source'], 'floor_guardrail_fallback')

    def test_reduce_fallback(self):
        cm = {'external_acwr': 1.6, 'internal_acwr': 1.7, 'normalized_divergence': -0.06}
        out = m._safe_floor_recommendation('high_acwr_risk', cm, '2026-06-27')
        self.assertEqual(out['structured_output']['decision']['action'], 'reduce')
        self.assertIn('reduce', out['daily_recommendation'].lower())


class TestRecentAlignment(unittest.TestCase):
    @mock.patch.object(m, 'execute_query')
    def test_count_based_avg_and_trend(self, mock_q):
        # DESC order (most recent first): improving overall (9 vs 5 endpoints)
        mock_q.return_value = [
            {'alignment_score': 9.0, 'deviation_reason': None},
            {'alignment_score': 8.0, 'deviation_reason': 'external'},
            {'alignment_score': 6.0, 'deviation_reason': None},
            {'alignment_score': 7.0, 'deviation_reason': 'prescription_mismatch'},
            {'alignment_score': 5.0, 'deviation_reason': None},
        ]
        a = m.get_recent_alignment(1, n=5)
        self.assertEqual(a['n'], 5)
        self.assertEqual(a['avg'], 7.0)
        self.assertEqual(a['trend'], 'improving')
        self.assertEqual(a['reasons'], {'external': 1, 'prescription_mismatch': 1})

    @mock.patch.object(m, 'execute_query')
    def test_no_data_returns_insufficient(self, mock_q):
        mock_q.return_value = []
        a = m.get_recent_alignment(1, n=5)
        self.assertEqual(a['n'], 0)
        self.assertIsNone(a['avg'])
        self.assertEqual(a['trend'], 'insufficient_data')
        self.assertIn('no recent autopsy data', m.format_recent_execution_block(a))

    @mock.patch.object(m, 'execute_query')
    def test_block_states_raw_number_no_buckets(self, mock_q):
        mock_q.return_value = [{'alignment_score': 8.0, 'deviation_reason': None}] * 5
        block = m.format_recent_execution_block(m.get_recent_alignment(1, n=5))
        self.assertIn('8.0/10', block)
        for word in ('strong', 'moderate', 'weak'):
            self.assertNotIn(word, block.lower())


if __name__ == '__main__':
    unittest.main()
