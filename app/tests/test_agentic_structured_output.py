"""The agentic generator must ask for, and the pipeline must be able to read, the
<structured_output> decision block.

Why this exists: enforce_safety_floor() reads decision.action from structured_output, and
floor_violation() returns False when there is no action. A generator whose prompt omits the
block therefore silently bypasses the physiology floor (found 2026-11-03: the agentic path
saved structured_output = {'meta': ...} only). The block's text now lives in one function,
structured_output_instructions(), used by every single-section daily generator.
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import llm_recommendations_module as M


class TestSharedInstructionBlock(unittest.TestCase):

    def test_block_carries_template_and_enums(self):
        text = M.structured_output_instructions('2026-11-03', 'aggressive')
        self.assertIn('<structured_output>', text)
        self.assertIn('</structured_output>', text)
        self.assertIn('"target_date": "2026-11-03"', text)
        self.assertIn('"risk_tolerance": "aggressive"', text)
        self.assertIn('decision.action: train | rest | cross_train | reduce', text)
        # the 'recovery' floor checks these two fields, so they must be requested
        self.assertIn('"intensity_target"', text)
        self.assertIn('"polarized_session_intent"', text)

    def test_missing_target_date_uses_placeholder(self):
        self.assertIn('"target_date": "YYYY-MM-DD"',
                      M.structured_output_instructions(None, 'balanced'))

    def test_standard_and_agentic_generators_use_the_shared_block(self):
        for name in ('create_enhanced_prompt_with_tone', 'generate_recommendations_agentic'):
            src = inspect.getsource(getattr(M, name))
            self.assertIn('structured_output_instructions(', src,
                          f'{name} must take its <structured_output> instructions from the '
                          'shared function, not a hand copy')
            self.assertNotIn('<structured_output>', src,
                             f'{name} carries its own copy of the structured_output template')


class TestFloorSeesAgenticDecision(unittest.TestCase):
    """A response in the shape the agentic prompt now asks for is parsed so the floor can
    act on it."""

    RESPONSE = (
        "DAILY RECOMMENDATION: Train easy today.\n\n"
        "<structured_output>\n"
        '{"target_date": "2026-11-03", "assessment": {"category": "overtraining_risk"},'
        ' "decision": {"action": "train", "intensity_target": "moderate",'
        ' "polarized_session_intent": "easy"}}\n'
        "</structured_output>"
    )

    def test_decision_is_parsed(self):
        sections = M.parse_llm_response(self.RESPONSE)
        self.assertEqual('train', M._decision_action_of(sections))

    def test_rest_floor_flags_a_train_decision(self):
        sections = M.parse_llm_response(self.RESPONSE)
        self.assertTrue(M.floor_violation('overtraining_risk', M._decision_of(sections)))

    def test_missing_block_gives_no_action(self):
        """Documents the hazard the prompt fix removes: with no block there is no action to
        check."""
        sections = M.parse_llm_response("DAILY RECOMMENDATION: Train easy today.")
        self.assertIsNone(M._decision_action_of(sections))


class TestFloorFailsSafeOnMissingDecision(unittest.TestCase):
    """No parsed decision.action on a rest/reduce floor is unverifiable, not compliant."""

    NO_DECISION = {'daily_recommendation': 'Train easy today.', 'structured_output': None}
    GOOD = (
        "DAILY RECOMMENDATION: Rest.\n<structured_output>"
        '{"decision": {"action": "rest", "intensity_target": "none",'
        ' "polarized_session_intent": "rest"}}</structured_output>'
    )

    def test_missing_decision_on_rest_floor_regenerates_and_recovers(self):
        from unittest import mock
        regen = mock.Mock(return_value=self.GOOD)
        res = M.enforce_safety_floor(self.NO_DECISION, {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual('ok', res['status'])
        regen.assert_called_once()
        self.assertIn('no parseable <structured_output>', regen.call_args[0][0])

    def test_missing_decision_persisting_falls_back(self):
        from unittest import mock
        regen = mock.Mock(return_value='DAILY RECOMMENDATION: Train easy again.')
        res = M.enforce_safety_floor(self.NO_DECISION, {}, 'overtraining_risk', 'P', regen, 1)
        self.assertEqual('fallback', res['status'])

    def test_missing_decision_on_train_allowed_floor_is_untouched(self):
        from unittest import mock
        regen = mock.Mock()
        res = M.enforce_safety_floor(self.NO_DECISION, {}, 'normal_progression', 'P', regen, 1)
        self.assertEqual('ok', res['status'])
        regen.assert_not_called()

    def test_floor_violation_itself_is_unchanged(self):
        """floor_violation() still treats a missing action as not-a-violation (pinned by
        test_safety_floor); the fail-safe lives in _floor_breached()."""
        self.assertFalse(M.floor_violation('overtraining_risk', None))
        self.assertTrue(M._floor_breached('overtraining_risk', None))
        self.assertTrue(M._floor_breached('overtraining_risk', {}))
        self.assertFalse(M._floor_breached('normal_progression', None))
        self.assertFalse(M._floor_breached('overtraining_risk', {'action': 'rest'}))


if __name__ == '__main__':
    unittest.main()
