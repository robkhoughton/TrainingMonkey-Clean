"""
Tests for dynamic_aet.py — the effective (dynamic) Aerobic Threshold core.

Pure-function coverage (no DB): the offset function shape (dead-band, asymmetric slopes,
caps), the parasympathetic-overdrive hard guard, the staleness decay, the UNKNOWN
fallback, the boundary sanity clamps, and athlete-model parameter loading. These encode
the decisions from docs/design_dynamic_aet_2026-06-27.md.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DATABASE_URL', 'postgresql://test:test@localhost:5432/test')

import dynamic_aet as da


class TestOffsetShape(unittest.TestCase):
    def setUp(self):
        self.p = da.OffsetParams()  # population defaults

    def test_zero_in_deadband(self):
        self.assertEqual(da.compute_aet_offset(0.0, 'GREEN', 0, self.p), 0.0)
        self.assertEqual(da.compute_aet_offset(0.4, 'GREEN', 0, self.p), 0.0)
        self.assertEqual(da.compute_aet_offset(-0.4, 'GREEN', 0, self.p), 0.0)

    def test_continuous_at_deadband_edge(self):
        # At |z| == deadband the ramp starts from 0 — no cliff.
        self.assertAlmostEqual(da.compute_aet_offset(-0.5, 'GREEN', 0, self.p), 0.0)
        self.assertAlmostEqual(da.compute_aet_offset(0.5, 'GREEN', 0, self.p), 0.0)

    def test_downward_ramp(self):
        self.assertAlmostEqual(da.compute_aet_offset(-1.0, 'GREEN', 0, self.p), -2.0)
        self.assertAlmostEqual(da.compute_aet_offset(-1.5, 'GREEN', 0, self.p), -4.0)

    def test_upward_ramp_is_gentler(self):
        # slope_pos (1.5) < slope_neg (4.0): same |z| moves less upward than downward.
        up = da.compute_aet_offset(1.0, 'GREEN', 0, self.p)
        down = da.compute_aet_offset(-1.0, 'GREEN', 0, self.p)
        self.assertAlmostEqual(up, 0.75)
        self.assertLess(abs(up), abs(down))

    def test_caps(self):
        self.assertAlmostEqual(da.compute_aet_offset(-5.0, 'GREEN', 0, self.p), -8.0)
        self.assertAlmostEqual(da.compute_aet_offset(5.0, 'GREEN', 0, self.p), 3.0)


class TestHardGuard(unittest.TestCase):
    def setUp(self):
        self.p = da.OffsetParams()

    def test_deep_hole_never_raises(self):
        # High hrv_z would normally raise AeT; parasympathetic overdrive forbids it.
        self.assertLessEqual(
            da.compute_aet_offset(2.0, 'YELLOW_PARASYMPATHETIC', 0, self.p), 0.0)

    def test_red_never_raises(self):
        self.assertEqual(da.compute_aet_offset(2.0, 'RED', 0, self.p), 0.0)

    def test_guard_does_not_block_downward(self):
        # A suppressed reading in a no-raise state still lowers AeT.
        self.assertAlmostEqual(
            da.compute_aet_offset(-1.5, 'RED', 0, self.p), -4.0)


class TestStaleness(unittest.TestCase):
    def setUp(self):
        self.p = da.OffsetParams()  # staleness_days = 3

    def test_fresh_full_weight(self):
        self.assertAlmostEqual(da.compute_aet_offset(-1.5, 'GREEN', 3, self.p), -4.0)

    def test_partial_decay(self):
        # days=4 -> factor 1 - 1/3 = 0.667
        self.assertAlmostEqual(
            da.compute_aet_offset(-1.5, 'GREEN', 4, self.p), -4.0 * (2.0 / 3.0), places=3)

    def test_fully_decayed(self):
        self.assertEqual(da.compute_aet_offset(-1.5, 'GREEN', 6, self.p), 0.0)

    def test_none_age_zero(self):
        self.assertEqual(da.staleness_factor(None, 3), 0.0)


class TestUnknown(unittest.TestCase):
    def test_none_hrv_z_is_zero_offset(self):
        self.assertEqual(da.compute_aet_offset(None, 'UNKNOWN', None), 0.0)


class TestEffectiveAet(unittest.TestCase):
    def test_basic_shift(self):
        r = da.compute_effective_aet(135, -1.5, 'GREEN', 0)
        self.assertEqual(r['effective_aet'], 131)
        self.assertEqual(r['baseline_aet'], 135)
        self.assertAlmostEqual(r['offset'], -4.0)
        self.assertIsNone(r['fallback_reason'])

    def test_fallback_no_baseline(self):
        r = da.compute_effective_aet(135, None, 'UNKNOWN', None)
        self.assertEqual(r['effective_aet'], 135)
        self.assertEqual(r['fallback_reason'], 'no_hrv_baseline')

    def test_fallback_stale(self):
        r = da.compute_effective_aet(135, -1.5, 'GREEN', 5)
        self.assertEqual(r['fallback_reason'], 'hrv_stale')

    def test_floor_clamp(self):
        # baseline near the Z1/Z2 floor; downward offset cannot cross it.
        r = da.compute_effective_aet(122, -1.5, 'GREEN', 0, vt2=160, z1z2_floor=121)
        self.assertEqual(r['effective_aet'], 122)  # 121 + 1

    def test_ceiling_clamp(self):
        # baseline near VT2; upward offset cannot cross it.
        r = da.compute_effective_aet(138, 5.0, 'GREEN', 0, vt2=140, z1z2_floor=120)
        self.assertEqual(r['effective_aet'], 139)  # 140 - 1


class TestOffsetParams(unittest.TestCase):
    def test_defaults_when_none(self):
        p = da.OffsetParams.from_athlete_model(None)
        self.assertEqual(p.slope_neg, da.DEFAULT_SLOPE_NEG)
        self.assertEqual(p.staleness_days, da.DEFAULT_STALENESS_DAYS)

    def test_null_columns_fall_back(self):
        p = da.OffsetParams.from_athlete_model({'aet_offset_slope_neg': None})
        self.assertEqual(p.slope_neg, da.DEFAULT_SLOPE_NEG)

    def test_values_used(self):
        p = da.OffsetParams.from_athlete_model({
            'aet_offset_slope_neg': 5.0, 'aet_offset_cap_neg': -10.0,
            'aet_offset_staleness_days': 4,
        })
        self.assertEqual(p.slope_neg, 5.0)
        self.assertEqual(p.cap_neg, -10.0)
        self.assertEqual(p.staleness_days, 4)


class TestDynamicDivergence(unittest.TestCase):
    def test_sign_convention(self):
        # external > internal -> positive (recovery/detraining)
        self.assertGreater(da.dynamic_divergence(1.2, 1.0), 0)
        # internal > external -> negative (hidden stress)
        self.assertLess(da.dynamic_divergence(1.0, 1.2), 0)

    def test_equal_is_zero(self):
        self.assertEqual(da.dynamic_divergence(1.1, 1.1), 0.0)

    def test_none_inputs(self):
        self.assertIsNone(da.dynamic_divergence(None, 1.0))
        self.assertIsNone(da.dynamic_divergence(1.0, None))

    def test_both_zero(self):
        self.assertEqual(da.dynamic_divergence(0, 0), 0.0)

    def test_matches_formula(self):
        # (1.3 - 1.0) / 1.15 = 0.2609
        self.assertAlmostEqual(da.dynamic_divergence(1.3, 1.0), 0.2609, places=4)


class TestCutoverFlagSafety(unittest.TestCase):
    """The cutover flag must NOT be auto-enabled by admin status — it bypasses the
    is_feature_enabled catch-all so cutover stays a deliberate, post-recalibration flip."""

    def test_cutover_flag_off_for_admin(self):
        from utils.feature_flags import is_feature_enabled
        self.assertFalse(is_feature_enabled('dynamic_aet_divergence_cutover', 1))

    def test_cutover_flag_off_for_other_users(self):
        from utils.feature_flags import is_feature_enabled
        self.assertFalse(is_feature_enabled('dynamic_aet_divergence_cutover', 2))
        self.assertFalse(is_feature_enabled('dynamic_aet_divergence_cutover', None))

    def test_admin_catchall_still_works_for_other_features(self):
        # Guards that the special-case didn't break admin early-access generally.
        from utils.feature_flags import is_feature_enabled
        self.assertTrue(is_feature_enabled('some_unregistered_feature', 1))


if __name__ == '__main__':
    unittest.main()
