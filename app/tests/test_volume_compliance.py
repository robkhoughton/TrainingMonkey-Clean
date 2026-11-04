"""Autopsy volume compliance: prescribed vs actual load miles computed in code, not by the model."""
import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

import coach_recommendations
import llm_recommendations_module as lrm
from coach_recommendations import long_run_limits
from external_load import format_volume_compliance, volume_compliance


def _fake_strava_app(structured_output):
    mod = types.ModuleType('strava_app')
    mod.get_recommendation_meta_for_date = lambda d, u: (structured_output, None)
    return mod


def _rx(distance, vert):
    return {'decision': {'action': 'train', 'target_distance_miles': distance,
                         'target_elevation_gain_feet': vert}}


class TestVolumeCompliance(unittest.TestCase):
    def test_oct_31_session_combines_distance_and_vert(self):
        # Rx 4.5 mi +300 ft; actual 10.66 mi +1,270 ft. The model reported +137% / +323% separately.
        vc = volume_compliance(4.5, 300, 10.66, 1270, 10.66 + 1270 / 750)
        self.assertAlmostEqual(vc.target_load_miles, 4.9)
        text = format_volume_compliance(vc)
        self.assertIn('= 4.9 load miles', text)
        self.assertIn('= 12.4 load miles', text)
        self.assertIn('Load miles: +152%', text)
        self.assertIn('distance +137%', text)
        self.assertIn('vert +323%', text)

    def test_flat_target_reports_vert_as_no_target(self):
        # Nov 2: Rx 5 mi flat, actual 4.27 mi +801 ft — load is on target, distance short.
        text = format_volume_compliance(volume_compliance(5.0, 0, 4.27, 801, 4.27 + 801 / 750))
        self.assertIn('Load miles: +7%', text)
        self.assertIn('distance -15%', text)
        self.assertIn('vert no target', text)


class TestVolumeComplianceBlock(unittest.TestCase):
    def _block(self, structured_output, rows, limits=None):
        with mock.patch.dict(sys.modules, {'strava_app': _fake_strava_app(structured_output)}), \
             mock.patch.object(lrm, 'execute_query', return_value=rows), \
             mock.patch.object(coach_recommendations, 'get_long_run_limits', return_value=limits):
            return lrm.build_volume_compliance_block(1, '2026-10-31')

    def test_uses_stored_total_load_miles_for_actual(self):
        rows = [{'distance_miles': 10.66, 'elevation_gain_feet': 1270, 'total_load_miles': 12.35}]
        block = self._block(_rx(4.5, 300), rows)
        self.assertIn('VOLUME COMPLIANCE', block)
        self.assertIn('= 12.3 load miles', block)
        self.assertNotIn('SINGLE-RUN SPIKE', block)

    def test_no_target_means_no_block(self):
        rows = [{'distance_miles': 5, 'elevation_gain_feet': 0, 'total_load_miles': 5}]
        self.assertEqual(self._block({'decision': {'action': 'train'}}, rows), '')
        self.assertEqual(self._block(None, rows), '')

    def test_no_activity_means_no_block(self):
        self.assertEqual(self._block(_rx(5, 0), []), '')

    def test_flags_spike_against_each_ceiling(self):
        # Ceilings: distance 11.7 mi, load 13.6 load miles. A 10 mi / 3,000 ft run spikes load only.
        rows = [{'distance_miles': 10.0, 'elevation_gain_feet': 3000, 'total_load_miles': 14.0}]
        block = self._block(_rx(10, 3000), rows, limits=long_run_limits(10.66, 12.35))
        self.assertIn('SINGLE-RUN SPIKE: load 14.0 load miles > ceiling 13.6', block)
        self.assertNotIn('distance 10.0 mi > ceiling', block)

    def test_spike_is_per_session_not_day_total(self):
        # Two 7-mile runs: day total 14 mi, but neither session exceeds the 11.7 mi ceiling.
        rows = [{'distance_miles': 7.0, 'elevation_gain_feet': 0, 'total_load_miles': 7.0}] * 2
        block = self._block(_rx(14, 0), rows, limits=long_run_limits(10.66, 12.35))
        self.assertNotIn('SINGLE-RUN SPIKE', block)


class TestAlignmentPrompt(unittest.TestCase):
    def test_volume_block_reaches_the_alignment_prompt(self):
        with mock.patch.object(lrm, 'load_training_guide', return_value=''):
            prompt = lrm.create_enhanced_autopsy_prompt_with_scoring(
                '2026-10-31', 'Rx', 'Run', {'pain_percentage': None}, volume_block='VOLUME COMPLIANCE (computed)\n')
        self.assertIn('VOLUME COMPLIANCE (computed)', prompt)
        self.assertIn('in load miles', prompt)

    def test_both_rx_schemas_request_targets(self):
        src = open(lrm.__file__, encoding='utf-8').read()
        self.assertEqual(src.count('"target_distance_miles": null'), 2)
        self.assertEqual(src.count('"target_elevation_gain_feet": null'), 2)


if __name__ == '__main__':
    unittest.main()
