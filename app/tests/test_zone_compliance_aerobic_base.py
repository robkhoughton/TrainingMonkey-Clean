"""
Tests for the sub-VT1 aerobic-base metric in compute_zone_compliance.

Aerobic base is measured as time BELOW the effective VT1 (Z1 + Z2 combined), not Zone 2
alone, so a narrow dynamic Zone 2 never penalizes correctly-paced easy volume.
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
    def test_below_vt1_sums_z1_and_z2(self):
        # 20 min Z1 + 30 min Z2 = 50 min below VT1.
        zc = m.compute_zone_compliance(_summary(z1=1200, z2=1800), 'easy', HR)
        self.assertEqual(zc['below_vt1_minutes'], 50.0)
        self.assertEqual(zc['z2_minutes'], 30.0)

    def test_target_met_via_z1_plus_z2_even_with_narrow_z2(self):
        # Narrow Z2 (only 10 min) but 40 min Z1 -> 50 min below VT1 -> target MET.
        zc = m.compute_zone_compliance(_summary(z1=2400, z2=600), 'easy', HR)
        self.assertTrue(zc['aerobic_base_target_met'])

    def test_target_missed_when_sub_vt1_under_45(self):
        zc = m.compute_zone_compliance(_summary(z1=600, z2=600), 'easy', HR)  # 20 min total
        self.assertFalse(zc['aerobic_base_target_met'])

    def test_target_none_when_not_easy(self):
        zc = m.compute_zone_compliance(_summary(z1=3000, z4=600), 'hard', HR)
        self.assertIsNone(zc['aerobic_base_target_met'])


if __name__ == '__main__':
    unittest.main()
