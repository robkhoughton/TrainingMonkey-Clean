"""
TRIMP comes from the HR stream whenever one exists; average-HR TRIMP only without a stream.

Regression: stream TRIMP sat behind the 'enhanced_trimp_calculation' beta flag (users 1-3),
so ~15k activities of other users had average-HR TRIMP despite a stored stream.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import strava_training_load as s

HR = {'resting_hr': 50, 'max_hr': 190, 'gender': 'male'}


class TestComputeActivityTrimp(unittest.TestCase):
    def test_stream_used_when_present(self):
        trimp, method, n = s.compute_activity_trimp(10, 140, HR, [140] * 600)
        self.assertEqual(method, 'stream')
        self.assertEqual(n, 600)
        self.assertGreater(trimp, 0)

    def test_average_only_without_stream(self):
        _, method, n = s.compute_activity_trimp(10, 140, HR, None)
        self.assertEqual((method, n), ('average', 0))

    def test_constant_hr_stream_equals_average(self):
        stream, _, _ = s.compute_activity_trimp(30, 150, HR, [150] * 1800)
        avg, _, _ = s.compute_activity_trimp(30, 150, HR, None)
        self.assertAlmostEqual(stream, avg, places=1)

    def test_variable_hr_scores_above_average(self):
        # Banister weighting is convex: half at 120 + half at 180 > all at 150.
        stream, _, _ = s.compute_activity_trimp(30, 150, HR, [120] * 900 + [180] * 900)
        avg, _, _ = s.compute_activity_trimp(30, 150, HR, None)
        self.assertGreater(stream, avg)

    def test_time_weighted_downsampled_stream(self):
        # 3 s per sample with a time stream == the same effort at 1 Hz.
        one_hz, _, _ = s.compute_activity_trimp(30, 150, HR, [150] * 1800)
        down, _, _ = s.compute_activity_trimp(30, 150, HR, [150] * 600, list(range(0, 1800, 3)))
        self.assertAlmostEqual(one_hz, down, places=0)

    def test_dropouts_filled_not_averaged(self):
        # 10% dropout (zeros) is filled at the session's own intensity.
        clean, _, _ = s.compute_activity_trimp(30, 150, HR, [150] * 1800)
        gappy, method, _ = s.compute_activity_trimp(30, 150, HR, [150] * 1620 + [0] * 180)
        self.assertEqual(method, 'stream')
        self.assertAlmostEqual(clean, gappy, places=1)

    def test_no_feature_flag_gate(self):
        import inspect
        self.assertNotIn('enhanced_trimp_calculation', inspect.getsource(s.calculate_training_load))


if __name__ == '__main__':
    unittest.main()
