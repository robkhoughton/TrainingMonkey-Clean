"""
Zone time must be real seconds, not HR sample counts.

Strava downsamples long activities (user 1, 2026-10-31: 1,874 samples over 5,720 s), so
counting one second per sample stored 29 min of zone time for a 94 min run. Samples are
weighted by the time stream when it exists, else moving time is spread evenly.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import strava_training_load as s

ZONES, _ = s._build_zone_boundaries(200, 50, 'percentage')  # Z2 120-140, Z3 140-160


class TestSampleSeconds(unittest.TestCase):
    def test_time_stream_weights_by_gap(self):
        self.assertEqual(s.hr_sample_seconds(4, [0, 3, 6, 9]), [3, 3, 3, 3])

    def test_pause_gets_median_gap_not_its_length(self):
        # A 600 s auto-pause is not recorded time.
        self.assertEqual(s.hr_sample_seconds(4, [0, 2, 602, 604]), [2, 2, 2, 2])

    def test_uniform_fallback_from_moving_time(self):
        self.assertEqual(s.hr_sample_seconds(3, None, 9.0), [3.0, 3.0, 3.0])

    def test_mismatched_time_stream_falls_back(self):
        self.assertEqual(s.hr_sample_seconds(3, [0, 1], 6.0), [2.0, 2.0, 2.0])

    def test_no_source_returns_none(self):
        self.assertIsNone(s.hr_sample_seconds(3))


class TestWeightedBucketing(unittest.TestCase):
    def test_downsampled_stream_counts_real_seconds(self):
        hr = [130] * 10 + [150] * 10                  # 20 samples, one every 3 s
        weights = s.hr_sample_seconds(20, list(range(0, 60, 3)))
        self.assertEqual(s.bucket_hr_samples(hr, ZONES, weights), [0, 30, 30, 0, 0])

    def test_uneven_sampling_shifts_percentages(self):
        # Smart recording samples densely when HR changes: 8 Z2 samples cover 8 s, the
        # 2 Z3 samples cover 10 s + the last sample's median gap (1 s) = 11 s.
        # Counting samples would call this 20% Z3; it is 58%.
        hr = [130] * 8 + [150] * 2
        times = list(range(8)) + [8, 18]
        zt = s.bucket_hr_samples(hr, ZONES, s.hr_sample_seconds(10, times))
        self.assertEqual(zt[1], 8)
        self.assertEqual(zt[2], 11)

    def test_default_is_one_second_per_sample(self):
        self.assertEqual(s.bucket_hr_samples([130, 150], ZONES), [0, 1, 1, 0, 0])


if __name__ == '__main__':
    unittest.main()
