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

    def test_path2_slide_preserves_zone2_width(self):
        # Path 2: Z2 ceiling = effective AeT and Z1/Z2 floor slides by the same offset,
        # so Zone 2 keeps its width; VT2 and above unchanged.
        base, _ = s._build_zone_boundaries(200, 50, 'percentage')  # Z2 = [120, 140]
        base_w = base[1][1] - base[1][0]
        slid, _ = s._build_zone_boundaries(200, 50, 'percentage',
                                           vt1_override=132, aet_offset=-8)
        self.assertEqual(slid[1][1], 132.0)          # ceiling = effective AeT
        self.assertEqual(slid[1][0], base[1][0] - 8)  # floor slid down 8
        self.assertEqual(slid[0][1], base[1][0] - 8)  # Z1 ceiling tracks the slid floor
        self.assertEqual(slid[1][1] - slid[1][0], base_w)  # width preserved
        self.assertEqual(slid[3][0], base[3][0])      # Z3/Z4 line (VT2 region) unchanged

    def test_path2_floor_clamped_above_zone1_floor(self):
        # An extreme downward slide can't push the Z2 floor below Zone 1's own floor.
        slid, _ = s._build_zone_boundaries(200, 50, 'percentage',
                                           vt1_override=105, aet_offset=-40)
        self.assertGreater(slid[1][0], slid[0][0])


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


class TestEdwardsLoad(unittest.TestCase):
    def test_edwards_weighting(self):
        # 1 min each in Z1,Z2,Z3 -> 1*1 + 1*2 + 1*3 = 6.0
        self.assertEqual(s.edwards_trimp([60, 60, 60, 0, 0]), 6.0)

    def test_edwards_zero(self):
        self.assertEqual(s.edwards_trimp([0, 0, 0, 0, 0]), 0.0)

    def test_higher_zones_weigh_more(self):
        z2_only = s.edwards_trimp([0, 600, 0, 0, 0])   # 10 min Z2
        z4_only = s.edwards_trimp([0, 0, 0, 600, 0])   # 10 min Z4
        self.assertEqual(z2_only, 20.0)
        self.assertEqual(z4_only, 40.0)

    def test_dynamic_load_rises_when_aet_drops(self):
        # Same 130 bpm effort: Z2 at AeT=140 -> Z3 at AeT=127, so Edwards load rises.
        hr = [130] * 600  # 10 minutes
        hi = s.dynamic_zone_times(hr, 200, 50, 'percentage', None, 140)
        lo = s.dynamic_zone_times(hr, 200, 50, 'percentage', None, 127)
        self.assertEqual(s.edwards_trimp(hi), 20.0)  # all Z2 -> 10*2
        self.assertEqual(s.edwards_trimp(lo), 30.0)  # all Z3 -> 10*3


if __name__ == '__main__':
    unittest.main()
