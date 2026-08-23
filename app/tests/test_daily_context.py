"""Tests for the shared daily-prompt context seam (assemble_daily_context).

The bug class this guards against is silent signal drift: YTM builds its daily
recommendation through several prompt builders, and for a long time each assembled
its own context inline. A signal added to one never reached the others, so readiness
/ HRV, dynamic AeT and the coaching-context library reached some paths but not
others, while free-text journal notes reached only the post-workout path -- meaning
the nightly all-user path could not see an athlete writing "abandoned run, QL pain".

Following the precedent of test_safety_floor.py::TestFinalizeRecommendation, these
test the seam directly rather than requiring an end-to-end test per generator.
"""
import dataclasses
import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as M


# The substantive coaching signals. Every daily prompt builder must consume all of
# these from the seam -- that is what keeps the paths in parity.
#
# Deliberately excludes presentation/identity fields (current_date, start_date,
# end_date, days_analyzed, athlete_profile, athlete_age, formatted_metrics,
# assessment_category, thresholds, recommendation_style, target_date): each template
# renders those its own way, and requiring them everywhere would assert style, not
# signal.
REQUIRED_SIGNALS = frozenset({
    'metric_verdict',
    'effective_aet',
    'readiness',
    'coaching_library',
    'weekly',
    'athlete_model',
    'race_day',
    'race_goals',
    'autopsy',
    'journal_notes',
    'preference_feedback',
    'recent_execution',
    'training_stage',
    'pattern_flags',
    'recent_activities',
    'filtered_guide',
})

# Builders already routed through the seam.
BUILDERS_ON_SEAM = (
    'create_enhanced_prompt_with_tone',
    'create_autopsy_informed_decision_prompt',
)

# Known gap: the agentic generator still assembles its prompt inline, including a
# hand-copied duplicate of the readiness block. When it is moved onto the seam, add
# it to BUILDERS_ON_SEAM above and delete this list -- test_known_gap_is_still_real
# will fail if it is migrated but left listed here, so the two cannot drift apart.
BUILDERS_NOT_YET_ON_SEAM = (
    'generate_recommendations_agentic',
)


class TestDailyContextShape(unittest.TestCase):
    """DailyContext is the declared inventory of available context blocks."""

    def test_is_a_dataclass(self):
        self.assertTrue(dataclasses.is_dataclass(M.DailyContext))

    def test_required_signals_are_real_fields(self):
        """Catches a field rename that would silently orphan a signal."""
        fields = {f.name for f in dataclasses.fields(M.DailyContext)}
        missing = REQUIRED_SIGNALS - fields
        self.assertEqual(
            set(), missing,
            f"REQUIRED_SIGNALS names fields that no longer exist on DailyContext: {sorted(missing)}"
        )

    def test_new_fields_are_classified(self):
        """A newly added DailyContext field must be consciously classified as either a
        required coaching signal or a presentation field -- not silently ignored."""
        presentation = {
            'current_date', 'target_date', 'start_date', 'end_date', 'days_analyzed',
            'athlete_profile', 'athlete_age', 'formatted_metrics', 'assessment_category',
            'thresholds', 'recommendation_style',
        }
        fields = {f.name for f in dataclasses.fields(M.DailyContext)}
        unclassified = fields - REQUIRED_SIGNALS - presentation
        self.assertEqual(
            set(), unclassified,
            "New DailyContext field(s) are unclassified: "
            f"{sorted(unclassified)}. Add each to REQUIRED_SIGNALS (and interpolate it "
            "into every builder) or to the presentation set."
        )


class TestBuilderParity(unittest.TestCase):
    """The anti-drift mechanism.

    Adding a signal to the seam but interpolating it into only one builder is exactly
    how the paths diverged before. This fails the build when that happens again.
    """

    def test_every_builder_consumes_every_required_signal(self):
        failures = []
        for builder_name in BUILDERS_ON_SEAM:
            src = inspect.getsource(getattr(M, builder_name))
            for signal in sorted(REQUIRED_SIGNALS):
                if f'ctx.{signal}' not in src:
                    failures.append(f'{builder_name} does not consume ctx.{signal}')
        self.assertEqual([], failures, '\n'.join(failures))

    def test_builders_call_the_seam(self):
        for builder_name in BUILDERS_ON_SEAM:
            src = inspect.getsource(getattr(M, builder_name))
            self.assertIn(
                'assemble_daily_context(', src,
                f'{builder_name} must build its context through the shared seam'
            )

    def test_known_gap_is_still_real(self):
        """Guards the migration TODO itself: once the agentic path moves onto the seam,
        this fails, forcing BUILDERS_NOT_YET_ON_SEAM to be updated rather than left stale."""
        for builder_name in BUILDERS_NOT_YET_ON_SEAM:
            src = inspect.getsource(getattr(M, builder_name))
            self.assertNotIn(
                'assemble_daily_context(', src,
                f'{builder_name} now uses the seam -- move it into BUILDERS_ON_SEAM '
                'and remove it from BUILDERS_NOT_YET_ON_SEAM'
            )


class TestAutopsyBlockContract(unittest.TestCase):
    """The autopsy block carries facts only; each path appends its own framing."""

    def test_autopsy_facts_are_not_truncated(self):
        """The April 2026 fix removed truncation at the source because clipping dropped
        the scheduling guidance that lives late in the analysis text. A char limit must
        not creep back into the shared block."""
        src = inspect.getsource(M.assemble_daily_context)
        self.assertNotIn(
            "latest_insights', 'No specific insights')[:", src,
            'autopsy latest_insights must not be truncated'
        )
        self.assertNotIn("latest_insights[:", src)

    def test_each_path_has_its_own_adaptation_framing(self):
        self.assertTrue(M.AUTOPSY_ADAPTATION_STANDARD.strip())
        self.assertTrue(M.AUTOPSY_ADAPTATION_AUTOPSY_INFORMED.strip())
        self.assertNotEqual(
            M.AUTOPSY_ADAPTATION_STANDARD,
            M.AUTOPSY_ADAPTATION_AUTOPSY_INFORMED,
        )

    def test_shared_block_carries_no_path_framing(self):
        """Framing belongs in the per-path constants, not the shared facts block."""
        src = inspect.getsource(M.assemble_daily_context)
        self.assertNotIn('COACHING ADAPTATION STRATEGY', src)
        self.assertNotIn('AUTOPSY-INFORMED ADAPTATION', src)


class TestYesterdaySessionQuery(unittest.TestCase):
    """Regression: the yesterday-RPE lookup selected a column that does not exist
    (`activities.workout_type`), so it raised on every call and the surrounding
    except swallowed it -- the line never rendered on any path."""

    def test_does_not_select_nonexistent_column(self):
        src = inspect.getsource(M.assemble_daily_context)
        self.assertNotIn('SELECT workout_type', src)


if __name__ == '__main__':
    unittest.main()
