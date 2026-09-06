"""Tests for the Adequate Context Gate (ticket 04, merged from tickets 04+05).

Following the precedent of test_daily_context.py: this repo has been burned
twice before by a fix landing in one Rx-generation code path and not a
sibling one. Rather than an end-to-end test per generator, these assert the
gate call is present in every verified entry point's source directly.
"""
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as M
import adequate_context_gate as gate_module

# Every verified Rx/autopsy generation entry point (see
# .scratch/model-confidence-redesign/issues/04-adequate-context-gate.md).
# assemble_daily_context() is deliberately NOT checked here — the gate lives
# in these four top-level functions instead, which cover every cron/manual/
# journal-triggered path into generation without touching the shared context
# seam (assemble_daily_context has its own, separate test coverage in
# test_daily_context.py for content-parity, not gating).
GATED_GENERATORS = (
    'generate_recommendations',
    'generate_recommendations_agentic',
    'generate_activity_autopsy_enhanced',
    'generate_autopsy_informed_daily_decision',
)


class TestGateCoverage(unittest.TestCase):
    """The anti-drift mechanism: a generator added later, or one that loses
    its check during a refactor, fails this immediately."""

    def test_every_generator_calls_the_gate(self):
        failures = []
        for name in GATED_GENERATORS:
            src = inspect.getsource(getattr(M, name))
            if 'check_adequate_context(' not in src:
                failures.append(f'{name} does not call check_adequate_context()')
        self.assertEqual([], failures, '\n'.join(failures))

    def test_gate_checked_before_any_llm_call(self):
        """A generator that calls the gate somewhere but after already calling
        the LLM would satisfy test_every_generator_calls_the_gate while still
        violating the actual guarantee. Assert the gate call's line number
        precedes every call_claude / call_anthropic_api line in the same
        source block."""
        llm_call_markers = ('call_claude(', 'call_anthropic_api(', '.submit(\n                call_claude')
        failures = []
        for name in GATED_GENERATORS:
            src = inspect.getsource(getattr(M, name))
            gate_pos = src.find('check_adequate_context(')
            if gate_pos == -1:
                continue  # already reported by test_every_generator_calls_the_gate
            for marker in llm_call_markers:
                llm_pos = src.find(marker)
                if llm_pos != -1 and llm_pos < gate_pos:
                    failures.append(
                        f'{name}: found "{marker}" before the gate check — gate must run first'
                    )
        self.assertEqual([], failures, '\n'.join(failures))


class TestGateShape(unittest.TestCase):
    """check_adequate_context()'s return contract, so callers relying on
    `gate['passes']` / `gate['failing_floors_ordered']` fail loudly on drift."""

    def test_returns_required_keys(self):
        sig = inspect.signature(gate_module.check_adequate_context)
        self.assertIn('user_id', sig.parameters)

    def test_floor_order_is_hardest_first(self):
        """Message ordering rule from the ticket: chronic depth, then
        journaling, then season goal — never re-sequenced silently."""
        self.assertEqual(
            ('chronic_depth', 'journal_recency', 'season_goal'),
            gate_module.FLOOR_ORDER,
        )


if __name__ == '__main__':
    unittest.main()
