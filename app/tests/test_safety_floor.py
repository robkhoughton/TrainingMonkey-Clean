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


def _sections(action):
    return {'structured_output': {'decision': {'action': action}},
            'daily_recommendation': f'rec {action}', 'weekly_recommendation': '', 'pattern_insights': ''}


class TestEnforceSafetyFloor(unittest.TestCase):
    def test_no_violation_does_not_regenerate(self):
        regen = mock.Mock()
        res = m.enforce_safety_floor(_sections('rest'), {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual(res['status'], 'ok')
        regen.assert_not_called()

    @mock.patch.object(m, 'parse_llm_response')
    def test_violation_then_compliant_regeneration(self, mock_parse):
        mock_parse.return_value = _sections('rest')
        regen = mock.Mock(return_value='RAW COMPLIANT')
        res = m.enforce_safety_floor(_sections('train'), {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual(res['status'], 'ok')
        self.assertEqual(res['response'], 'RAW COMPLIANT')
        regen.assert_called_once()

    @mock.patch.object(m, 'parse_llm_response')
    def test_violation_persists_falls_back(self, mock_parse):
        mock_parse.return_value = _sections('train')
        regen = mock.Mock(return_value='RAW STILL BAD')
        res = m.enforce_safety_floor(_sections('train'), {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual(res['status'], 'fallback')

    def test_empty_regeneration_falls_back(self):
        regen = mock.Mock(return_value='')
        res = m.enforce_safety_floor(_sections('train'), {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual(res['status'], 'fallback')


class TestMetricCitationRepair(unittest.TestCase):
    METRICS = {'external_acwr': 1.75, 'internal_acwr': 2.13, 'normalized_divergence': -0.20}

    def test_corrects_wrong_internal_acwr_only(self):
        prose = ("External ACWR sits at 1.75, well above the high-risk threshold of 1.5. "
                 "Internal ACWR is 1.13, also above that same threshold. Normalized divergence "
                 "is -0.200, which breaches your breakdown threshold of -0.110.")
        fixed, reps = m.repair_metric_citations(prose, self.METRICS)
        self.assertEqual(reps, [('Internal ACWR', '1.13', '2.13')])
        self.assertIn('Internal ACWR is 2.13', fixed)

    def test_preserves_threshold_numbers(self):
        prose = "Internal ACWR is 1.13, above the high-risk threshold of 1.5, breakdown -0.110."
        fixed, _ = m.repair_metric_citations(prose, self.METRICS)
        self.assertIn('threshold of 1.5', fixed)   # not changed to an ACWR value
        self.assertIn('-0.110', fixed)             # breakdown threshold untouched

    def test_noop_when_all_correct(self):
        prose = "External ACWR is 1.75, Internal ACWR is 2.13, divergence is -0.200."
        fixed, reps = m.repair_metric_citations(prose, self.METRICS)
        self.assertEqual(reps, [])
        self.assertEqual(fixed, prose)

    def test_formatting_difference_not_flagged(self):
        # -0.20 and -0.200 are the same value; must not be "repaired".
        prose = "Normalized divergence is -0.20 today."
        _, reps = m.repair_metric_citations(prose, self.METRICS)
        self.assertEqual(reps, [])

    def test_repairs_wrong_divergence(self):
        prose = "Normalized divergence is -0.150, in the moderate band."
        fixed, reps = m.repair_metric_citations(prose, self.METRICS)
        self.assertEqual(reps, [('divergence', '-0.150', '-0.200')])
        self.assertIn('-0.200', fixed)


if __name__ == '__main__':
    unittest.main()
