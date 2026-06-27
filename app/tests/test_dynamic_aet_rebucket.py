"""
Tests for the dynamic-AeT zone re-bucketing helpers in strava_training_load.py
(Phase A1): _build_zone_boundaries and bucket_hr_samples.

The keystone behavior: when the effective AeT drops, a fixed-HR effort moves from Z2 into
Z3 ("130 bpm scored as Z3 glycolytic when AeT dropped") — and ONLY the Z2/Z3 line moves
(decision d). The refactor must also preserve the original boundary values used by the
sync path.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import strava_training_load as s


class TestBoundaries(unittest.TestCase):
    def test_percentage(self):
        zones, label = s._build_zone_boundaries(200, 50, 'percentage')
        self.assertEqual(label, 'percentage')
        self.assertEqual(zones[1][1], 0.70 * 200)  # Z2 ceiling = 140
        self.assertEqual(zones[2][0], 0.70 * 200)  # Z3 floor = 140

    def test_karvonen(self):
        zones, label = s._build_zone_boundaries(200, 50, 'karvonen')
        self.assertEqual(label, 'karvonen')
        self.assertEqual(zones[1][1], 50 + 0.70 * 150)  # 155

    def test_custom_override_applied(self):
        zones, label = s._build_zone_boundaries(
            200, 50, 'custom', custom_hr_zones={'zone2': {'max': 138}})
        self.assertEqual(label, 'custom')
        self.assertEqual(zones[1][1], 138.0)

    def test_vt1_override_moves_only_z2z3_line(self):
        base, _ = s._build_zone_boundaries(200, 50, 'percentage')
        zones, _ = s._build_zone_boundaries(200, 50, 'percentage', vt1_override=127)
        self.assertEqual(zones[1][1], 127.0)   # Z2 ceiling moved
        self.assertEqual(zones[2][0], 127.0)   # Z3 floor moved
        self.assertEqual(zones[0][1], base[0][1])  # Z1/Z2 line unchanged
        self.assertEqual(zones[3][0], base[3][0])  # Z3/Z4 line unchanged
        self.assertEqual(zones[3][1], base[3][1])  # Z4/Z5 line unchanged

    def test_vt1_override_wins_over_custom(self):
        # Effective AeT is authoritative — applied AFTER custom overrides.
        zones, _ = s._build_zone_boundaries(
            200, 50, 'custom', custom_hr_zones={'zone2': {'max': 138}}, vt1_override=127)
        self.assertEqual(zones[1][1], 127.0)


class TestBucketing(unittest.TestCase):
    def test_basic_counts(self):
        zones, _ = s._build_zone_boundaries(200, 50, 'percentage')  # Z2 120-140
        hr = [110] * 5 + [130] * 5 + [150] * 5
        self.assertEqual(s.bucket_hr_samples(hr, zones), [5, 5, 5, 0, 0])

    def test_ignores_nonpositive(self):
        zones, _ = s._build_zone_boundaries(200, 50, 'percentage')
        self.assertEqual(sum(s.bucket_hr_samples([0, -1, 130], zones)), 1)

    def test_keystone_z2_to_z3_on_aet_drop(self):
        # Same 130 bpm effort: Z2 when AeT=140, Z3 when AeT drops to 127.
        hi, _ = s._build_zone_boundaries(200, 50, 'percentage', vt1_override=140)
        lo, _ = s._build_zone_boundaries(200, 50, 'percentage', vt1_override=127)
        hr = [130] * 30
        self.assertEqual(s.bucket_hr_samples(hr, hi)[1], 30)  # all Z2
        self.assertEqual(s.bucket_hr_samples(hr, lo)[2], 30)  # all Z3


if __name__ == '__main__':
    unittest.main()
