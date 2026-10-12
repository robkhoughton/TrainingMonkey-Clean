"""
Tests for the enhanced (exponential-decay) ACWR path, through its production seam:
ACWRConfigurationService.calculate_enhanced_acwr, with the activities query patched.

Root cause these guard: the chronic average was normalised per activity ROW
(sum(w*x) / sum(w) over rows) while the acute average is per calendar DAY (7-day sum / 7).
A double session or a 'rest' placeholder row written alongside a real activity added
weight to the chronic denominator and inflated both ACWRs; a day with no row did the
opposite. The chronic average must be per calendar day over the configured period.

See .scratch/enhanced-acwr-chronic-per-day/spec.md.
"""
import os
import sys
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import acwr_configuration_service as svc_module

CONFIG = {'id': 1, 'chronic_period_days': 42, 'decay_rate': 0.05}

# User 1, real activities rows 2026-08-31 .. 2026-10-11 (date, total_load_miles, trimp).
# 2026-09-19 carries both a 'rest' placeholder row and the real activity row.
USER1_ROWS = [
    ('2026-08-31', 0.0, 0.0), ('2026-09-01', 8.917334, 85.7), ('2026-09-02', 7.26, 68.12),
    ('2026-09-03', 9.776667, 100.43), ('2026-09-04', 5.714667, 53.4), ('2026-09-05', 11.61, 141.91),
    ('2026-09-06', 0.0, 0.0), ('2026-09-07', 6.178, 55.94), ('2026-09-08', 8.68, 100.75),
    ('2026-09-09', 4.322, 40.65), ('2026-09-10', 15.88, 209.37), ('2026-09-11', 4.34, 28.23),
    ('2026-09-12', 4.888, 40.5), ('2026-09-13', 0.0, 0.0), ('2026-09-14', 3.3313334, 21.64),
    ('2026-09-15', 1.9833333, 11.85), ('2026-09-16', 0.0, 0.0), ('2026-09-17', 2.48, 26.91),
    ('2026-09-18', 0.0, 0.0), ('2026-09-19', 0.0, 0.0), ('2026-09-19', 102.7, 1221.37),
    ('2026-09-20', 0.0, 0.0), ('2026-09-21', 0.0, 0.0), ('2026-09-22', 0.0, 0.0),
    ('2026-09-23', 0.0, 0.0), ('2026-09-24', 2.47, 15.97), ('2026-09-25', 0.0, 0.0),
    ('2026-09-26', 0.0, 0.0), ('2026-09-27', 2.62, 23.45), ('2026-09-28', 3.34, 30.32),
    ('2026-09-29', 1.51, 13.24), ('2026-09-30', 3.28, 30.98), ('2026-10-01', 3.2386668, 28.53),
    ('2026-10-02', 3.74, 32.06), ('2026-10-03', 5.346667, 60.02), ('2026-10-04', 0.0, 0.0),
    ('2026-10-05', 2.66, 24.81), ('2026-10-06', 0.0, 0.0), ('2026-10-07', 4.45, 60.99),
    ('2026-10-08', 5.38, 64.63), ('2026-10-09', 0.0, 0.0), ('2026-10-10', 6.82, 102.86),
    ('2026-10-11', 0.0, 0.0),
]


def _fake_execute_query(rows):
    """Stand-in for db_utils.execute_query: answers the date-ranged activities queries."""
    parsed = [(datetime.strptime(d, '%Y-%m-%d').date(), l, t) for d, l, t in rows]

    def fake(query, params, fetch=False):
        _user_id, start, end = params
        start_d = datetime.strptime(start, '%Y-%m-%d').date()
        end_d = datetime.strptime(end, '%Y-%m-%d').date()
        return [{'date': d, 'total_load_miles': l, 'trimp': t}
                for d, l, t in parsed if start_d <= d <= end_d]
    return fake


def enhanced(rows, as_of='2026-10-11', config=CONFIG):
    with patch.object(svc_module.db_utils, 'execute_query', side_effect=_fake_execute_query(rows)):
        result = svc_module.ACWRConfigurationService.__new__(svc_module.ACWRConfigurationService)
        result.logger = svc_module.logger
        out = result.calculate_enhanced_acwr(1, as_of, config)
    assert out['success'], out
    return out


def _without_rest_placeholder_on_0919(rows):
    return [r for r in rows if not (r[0] == '2026-09-19' and r[1] == 0.0)]


class TestEnhancedChronicIsPerDay(unittest.TestCase):

    def test_user1_fixture_matches_per_day_definition(self):
        out = enhanced(USER1_ROWS)
        self.assertEqual(out['enhanced_acute_chronic_ratio'], 0.59)
        self.assertEqual(out['enhanced_trimp_acute_chronic_ratio'], 0.69)
        self.assertAlmostEqual(out['enhanced_normalized_divergence'], -0.14, places=2)

    def test_duplicate_rest_row_does_not_change_acwr(self):
        with_dup = enhanced(USER1_ROWS)
        without_dup = enhanced(_without_rest_placeholder_on_0919(USER1_ROWS))
        self.assertEqual(with_dup['enhanced_acute_chronic_ratio'], without_dup['enhanced_acute_chronic_ratio'])
        self.assertEqual(with_dup['enhanced_trimp_acute_chronic_ratio'],
                         without_dup['enhanced_trimp_acute_chronic_ratio'])

    def test_double_session_equals_single_session_of_same_total(self):
        single = list(USER1_ROWS)
        split = [r for r in USER1_ROWS if r[0] != '2026-09-10']
        split += [('2026-09-10', 10.0, 120.0), ('2026-09-10', 5.88, 89.37)]
        a, b = enhanced(single), enhanced(split)
        self.assertEqual(a['enhanced_acute_chronic_ratio'], b['enhanced_acute_chronic_ratio'])
        self.assertEqual(a['enhanced_trimp_acute_chronic_ratio'], b['enhanced_trimp_acute_chronic_ratio'])
        self.assertEqual(a['enhanced_chronic_load'], b['enhanced_chronic_load'])

    def test_missing_day_equals_zero_load_rest_row(self):
        with_rest_rows = enhanced(USER1_ROWS)
        no_rest_rows = enhanced([r for r in USER1_ROWS if r[1] != 0.0])
        self.assertEqual(with_rest_rows['enhanced_acute_chronic_ratio'], no_rest_rows['enhanced_acute_chronic_ratio'])
        self.assertEqual(with_rest_rows['enhanced_chronic_load'], no_rest_rows['enhanced_chronic_load'])

    def test_divergence_unchanged_by_row_layout(self):
        # Divergence depends only on acute vs chronic TRIMP-per-load, so the per-row vs
        # per-day denominator never affected it.
        self.assertEqual(enhanced(USER1_ROWS)['enhanced_normalized_divergence'],
                         enhanced([r for r in USER1_ROWS if r[1] != 0.0])['enhanced_normalized_divergence'])


if __name__ == '__main__':
    unittest.main()
