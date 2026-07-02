"""
Tests for the aerobic-base metric in compute_zone_compliance.

Path 2 (decision d, 2026-07-02): Zone 2 is a fixed-width productive band that slides with
AeT, so the aerobic-base target is measured as productive Zone 2 time (>=45 min). Zone 1
(walking/recovery, below the slid floor) is NOT an adequate mitochondrial stimulus and does
not count. below_vt1_minutes (Z1+Z2) is retained for context only.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import llm_recommendations_module as m

HR = {'vt1_bpm': 140, 'vt2_bpm': 170, 'zones': {
    'zone1': {'min': 100, 'max': 126}, 'zone2': {'min': 126, 'max': 140},
    'zone3': {'min': 140, 'max': 160}, 'zone4': {'min': 160, 'max': 170},
    'zone5': {'min': 170, 'max': 185}}}


def _summary(z1=0, z2=0, z3=0, z4=0, z5=0):
    total = z1 + z2 + z3 + z4 + z5
    s = {'total_zone_seconds': total,
         'time_in_zone1': z1, 'time_in_zone2': z2, 'time_in_zone3': z3,
         'time_in_zone4': z4, 'time_in_zone5': z5}
    for i, v in enumerate([z1, z2, z3, z4, z5], 1):
        s[f'z{i}_pct'] = round(v / total * 100, 1) if total else 0.0
    return s


class TestAerobicBase(unittest.TestCase):
    def test_below_vt1_context_field_still_sums_z1_and_z2(self):
        zc = m.compute_zone_compliance(_summary(z1=1200, z2=1800), 'easy', HR)
        self.assertEqual(zc['below_vt1_minutes'], 50.0)  # context only
        self.assertEqual(zc['z2_minutes'], 30.0)

    def test_target_met_requires_productive_zone2(self):
        # 45 min in Zone 2 -> target MET.
        zc = m.compute_zone_compliance(_summary(z1=600, z2=2700), 'easy', HR)
        self.assertTrue(zc['aerobic_base_target_met'])

    def test_walking_zone1_does_not_count(self):
        # 40 min Z1 (walking) + only 10 min Z2 -> target NOT met (Z1 is not stimulus).
        zc = m.compute_zone_compliance(_summary(z1=2400, z2=600), 'easy', HR)
        self.assertFalse(zc['aerobic_base_target_met'])

    def test_target_none_when_not_easy(self):
        zc = m.compute_zone_compliance(_summary(z1=3000, z4=600), 'hard', HR)
        self.assertIsNone(zc['aerobic_base_target_met'])


class TestDiagnosticExemption(unittest.TestCase):
    """A drift/AeT test drifts into Zone 3 by protocol — that crossing is the measurement,
    so it must NOT be flagged as a black-hole compliance failure."""

    # A drift test that spends 38% of time in Zone 3 (HR drifted above AeT).
    DRIFT = dict(z1=330, z2=1236, z3=966)

    def test_easy_run_with_z3_drift_is_black_hole(self):
        # Baseline: an EASY-prescribed run with the same Z3 drift IS a black hole.
        zc = m.compute_zone_compliance(_summary(**self.DRIFT), 'easy', HR)
        self.assertTrue(zc['black_hole'])

    def test_diagnostic_exempts_black_hole_and_base(self):
        zc = m.compute_zone_compliance(_summary(**self.DRIFT), 'easy', HR, is_diagnostic=True)
        self.assertTrue(zc['diagnostic'])
        self.assertFalse(zc['black_hole'])
        self.assertIsNone(zc['aerobic_base_target_met'])
        self.assertFalse(zc['insufficient_intensity'])

    def test_none_intent_no_longer_defaults_to_easy(self):
        # An unprescribed session (None) must not be judged as a black-hole failure —
        # you cannot fail to comply with a plan that did not exist.
        zc = m.compute_zone_compliance(_summary(**self.DRIFT), None, HR)
        self.assertFalse(zc['black_hole'])
        self.assertIsNone(zc['aerobic_base_target_met'])


class TestDiagnosticDetection(unittest.TestCase):
    def test_detects_from_prescription_workout_type(self):
        self.assertTrue(m.is_diagnostic_session({'decision': {'workout_type': 'Aerobic Test'}}, {}))

    def test_detects_from_journal_notes(self):
        self.assertTrue(m.is_diagnostic_session(None, {'notes': 'Executed HR drift test at 8:00 pace'}))
        self.assertTrue(m.is_diagnostic_session(None, {'notes': 'AeT test on treadmill'}))

    def test_plain_easy_run_not_diagnostic(self):
        self.assertFalse(m.is_diagnostic_session({'decision': {'workout_type': 'Easy Run'}},
                                                 {'notes': 'nice easy jog in the hills'}))


if __name__ == '__main__':
    unittest.main()
