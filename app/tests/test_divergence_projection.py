"""
Tests for Normalized Divergence on an empty acute window, and for the divergence
projection under rest vs easy-session scenarios.

Root cause these guard: divergence is (Ext ACWR - Int ACWR) / avg, which reduces to a
function of acute vs chronic TRIMP-per-load-mile only. Rest days add zero to both, so
rest moves divergence only through window turnover and can deepen a breach. When the
acute window empties, both ACWRs are 0 and the ratio is 0/0 - undefined, not 0. A
reported 0 read as "balanced" after a week of rest the metric itself caused.

See .scratch/divergence-rest-projection/spec.md.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

from datetime import date, timedelta

from unified_metrics_service import UnifiedMetricsService
from dynamic_aet import dynamic_divergence
from divergence_projection import project_divergence
from tests.test_enhanced_acwr_chronic import USER1_ROWS

ENHANCED = {'kind': 'enhanced', 'chronic_period_days': 42, 'decay_rate': 0.05}
STANDARD = {'kind': 'standard'}
REST = {'kind': 'rest'}
AS_OF = date(2026, 10, 11)


def by_date(path):
    return {p['date']: p for p in path}


class TestEmptyAcuteWindowIsUndefined(unittest.TestCase):

    def test_canonical_both_zero_is_undefined(self):
        self.assertIsNone(UnifiedMetricsService._calculate_normalized_divergence(0, 0))

    def test_dynamic_both_zero_is_undefined(self):
        self.assertIsNone(dynamic_divergence(0, 0))

    def test_canonical_still_computes_normal_values(self):
        self.assertEqual(UnifiedMetricsService._calculate_normalized_divergence(0.61, 0.70), -0.137)



class TestRestProjection(unittest.TestCase):
    """User 1, 2026-10-11: divergence -0.14 against a -0.11 breakdown threshold."""

    def test_day0_matches_stored_enhanced_values(self):
        day0 = by_date(project_divergence(USER1_ROWS, AS_OF, ENHANCED, REST, horizon=7))[AS_OF]
        # Stored values are rounded to 2 dp, so allow half a unit either way.
        self.assertAlmostEqual(day0['external_acwr'], 0.59, delta=0.006)
        self.assertAlmostEqual(day0['internal_acwr'], 0.69, delta=0.006)
        self.assertAlmostEqual(day0['normalized_divergence'], -0.143, delta=0.002)

    def test_rest_deepens_the_breach_then_goes_undefined_enhanced(self):
        path = by_date(project_divergence(USER1_ROWS, AS_OF, ENHANCED, REST, horizon=7))
        self.assertAlmostEqual(path[date(2026, 10, 12)]['normalized_divergence'], -0.188, delta=0.002)
        self.assertAlmostEqual(path[date(2026, 10, 15)]['normalized_divergence'], -0.275, delta=0.002)
        for d in (date(2026, 10, 17), date(2026, 10, 18)):
            self.assertIsNone(path[d]['normalized_divergence'])

    def test_rest_projection_standard_method(self):
        path = by_date(project_divergence(USER1_ROWS, AS_OF, STANDARD, REST, horizon=7))
        self.assertAlmostEqual(path[AS_OF]['normalized_divergence'], -0.141, delta=0.002)
        self.assertAlmostEqual(path[date(2026, 10, 12)]['normalized_divergence'], -0.176, delta=0.002)
        self.assertAlmostEqual(path[date(2026, 10, 15)]['normalized_divergence'], -0.262, delta=0.002)
        self.assertIsNone(path[date(2026, 10, 17)]['normalized_divergence'])

    def test_horizon_covers_as_of_plus_seven_days(self):
        path = project_divergence(USER1_ROWS, AS_OF, ENHANCED, REST, horizon=7)
        self.assertEqual([p['date'] for p in path], [AS_OF + timedelta(days=i) for i in range(8)])


class TestEasyProjection(unittest.TestCase):

    def test_cheap_easy_sessions_clear_the_breach_where_rest_cannot(self):
        easy = {'kind': 'easy', 'load': 4.0, 'trimp_per_load': 9.0}
        easy_path = by_date(project_divergence(USER1_ROWS, AS_OF, ENHANCED, easy, horizon=7))
        rest_path = by_date(project_divergence(USER1_ROWS, AS_OF, ENHANCED, REST, horizon=7))
        days = [AS_OF + timedelta(days=i) for i in range(1, 8)]
        self.assertTrue(any(easy_path[d]['normalized_divergence'] > -0.11 for d in days[:3]))
        for d in days:
            if rest_path[d]['normalized_divergence'] is not None:
                self.assertGreater(easy_path[d]['normalized_divergence'], rest_path[d]['normalized_divergence'])


class TestProjectionProperties(unittest.TestCase):

    def test_volume_alone_never_moves_divergence(self):
        # Constant TRIMP-per-load-mile, wildly varying volume including a big acute spike:
        # ACWR moves a lot, divergence stays exactly 0 (the identity r_chronic / r_acute).
        rows = [((AS_OF - timedelta(days=i)).isoformat(), load, load * 11.0)
                for i, load in enumerate([20.0, 0.0, 15.0, 3.0] + [4.0, 0.0, 6.0] * 15)]
        for method in (STANDARD, ENHANCED):
            path = project_divergence(rows, AS_OF, method, REST, horizon=3)
            self.assertGreater(path[0]['external_acwr'], 1.3)
            for p in path:
                self.assertEqual(p['normalized_divergence'], 0.0)

    def _history(self, acute):
        """28 chronic days at TRIMP/load 10, then the given acute sessions on days -2, -1, 0."""
        rows = [((AS_OF - timedelta(days=i)).isoformat(), 5.0, 50.0) for i in range(3, 28)]
        for offset, (load, trimp) in zip((2, 1, 0), acute):
            rows.append(((AS_OF - timedelta(days=offset)).isoformat(), load, trimp))
        return rows

    def test_rest_worsens_divergence_when_oldest_acute_sessions_are_cheapest(self):
        rows = self._history([(5.0, 40.0), (5.0, 60.0), (5.0, 80.0)])  # oldest cheapest
        path = project_divergence(rows, AS_OF, STANDARD, REST, horizon=7)
        start = path[0]['normalized_divergence']
        later = [p['normalized_divergence'] for p in path if p['normalized_divergence'] is not None][-1]
        self.assertLess(later, start)

    def test_rest_improves_divergence_when_oldest_acute_sessions_are_most_expensive(self):
        rows = self._history([(5.0, 80.0), (5.0, 60.0), (5.0, 40.0)])  # oldest most expensive
        path = project_divergence(rows, AS_OF, STANDARD, REST, horizon=7)
        start = path[0]['normalized_divergence']
        later = [p['normalized_divergence'] for p in path if p['normalized_divergence'] is not None][-1]
        self.assertGreater(later, start)


if __name__ == '__main__':
    unittest.main()
