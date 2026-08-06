"""
Tests for the server-side metric verdict (assessment category + authoritative
verdict block) injected into the daily prompts.

Root cause these guard: the autopsy daily prompt left metric classification to the
LLM, which fabricated a "-0.110 breakdown threshold" and argued with itself in the
prose. The verdict is now computed server-side and stated as fact. These tests lock
the classifier boundaries and that the verdict block reports the REAL thresholds.

See docs/refactor_plan_race_context_2026-06-24.md (decision-quality follow-up).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as m

# Aggressive-style thresholds (shape matches get_adjusted_thresholds output).
THRESHOLDS = {
    'acwr_high_risk': 1.5,
    'acwr_undertraining': 0.75,
    'divergence_overtraining': -0.20,
    'divergence_moderate_risk': -0.08,
    'days_since_rest_max': 8,
}


def metrics(**kw):
    base = {
        'external_acwr': 1.0, 'internal_acwr': 1.0, 'normalized_divergence': 0.0,
        'days_since_rest': 1, 'acwr_high_threshold': 1.5,
        'divergence_warn_threshold': -0.20, 'divergence_moderate_threshold': -0.08,
        'days_since_rest_max': 8, 'injury_risk_label': 'LOW', 'injury_risk_score': 10,
    }
    base.update(kw)
    return base


class TestDeriveAssessmentCategory(unittest.TestCase):
    def test_divergence_at_overtraining_boundary_is_overtraining(self):
        # The bug day: divergence exactly on the threshold must classify as overtraining.
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.75, internal_acwr=2.13, normalized_divergence=-0.20),
            THRESHOLDS)
        self.assertEqual(cat, 'overtraining_risk')

    def test_both_acwr_high_without_divergence_is_high_acwr_risk(self):
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.75, internal_acwr=1.6, normalized_divergence=0.0),
            THRESHOLDS)
        self.assertEqual(cat, 'high_acwr_risk')

    def test_days_since_rest_exceeded_is_mandatory_rest(self):
        cat = m.derive_assessment_category(metrics(days_since_rest=9), THRESHOLDS)
        self.assertEqual(cat, 'mandatory_rest')

    def test_clean_metrics_is_normal_progression(self):
        cat = m.derive_assessment_category(metrics(), THRESHOLDS)
        self.assertEqual(cat, 'normal_progression')

    def test_weight_drop_with_elevated_acwr_is_underfueling_risk(self):
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.6, internal_acwr=1.0, normalized_divergence=0.0,
                    weight_change_pct_28d=-3.5),
            THRESHOLDS)
        self.assertEqual(cat, 'underfueling_risk')

    def test_weight_drop_without_elevated_acwr_is_not_underfueling_risk(self):
        # This is the more concerning, load-independent case medically — but it must
        # NOT gate today's training action, since the drop isn't training-load-driven.
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.0, internal_acwr=1.0, normalized_divergence=0.0,
                    weight_change_pct_28d=-3.5),
            THRESHOLDS)
        self.assertEqual(cat, 'normal_progression')

    def test_small_weight_drop_below_threshold_does_not_trigger(self):
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.6, internal_acwr=1.6, normalized_divergence=0.0,
                    weight_change_pct_28d=-1.2),
            THRESHOLDS)
        self.assertEqual(cat, 'high_acwr_risk')

    def test_overtraining_takes_priority_over_underfueling(self):
        cat = m.derive_assessment_category(
            metrics(external_acwr=1.75, internal_acwr=2.13, normalized_divergence=-0.20,
                    weight_change_pct_28d=-5.0),
            THRESHOLDS)
        self.assertEqual(cat, 'overtraining_risk')


class TestVerdictBlock(unittest.TestCase):
    def test_states_real_thresholds_and_mandate(self):
        cm = metrics(external_acwr=1.75, internal_acwr=2.13, normalized_divergence=-0.20,
                     days_since_rest=3, injury_risk_label='MODERATE', injury_risk_score=55)
        cat = m.derive_assessment_category(cm, THRESHOLDS)
        block = m.format_metric_verdict_block(cm, cat, THRESHOLDS)
        self.assertIn('OVERTRAINING_RISK', block)
        self.assertIn('-0.2', block)          # real overtraining threshold
        self.assertIn('1.5', block)           # real ACWR high-risk threshold
        self.assertIn('ACTION MANDATE', block)
        self.assertIn('MODERATE', block)

    def test_does_not_invent_breakdown_threshold(self):
        cm = metrics(normalized_divergence=-0.20)
        block = m.format_metric_verdict_block(cm, 'overtraining_risk', THRESHOLDS)
        # The fabricated value from the bug must never appear.
        self.assertNotIn('0.11', block)

    def test_underfueling_verdict_states_redS_pattern(self):
        cm = metrics(external_acwr=1.6, internal_acwr=1.0, normalized_divergence=0.0,
                     weight_change_pct_28d=-3.5)
        block = m.format_metric_verdict_block(cm, 'underfueling_risk', THRESHOLDS)
        self.assertIn('RED-S', block)
        self.assertIn('-3.5%', block)
        self.assertIn('REDUCE', block)

    def test_load_independent_weight_drop_suggests_medical_followup_without_gating_action(self):
        cm = metrics(external_acwr=1.0, internal_acwr=1.0, normalized_divergence=0.0,
                     weight_change_pct_28d=-4.0)
        block = m.format_metric_verdict_block(cm, 'normal_progression', THRESHOLDS)
        self.assertIn('doctor', block)
        self.assertIn('PROCEED', block)  # normal_progression mandate — action not gated


if __name__ == '__main__':
    unittest.main()
