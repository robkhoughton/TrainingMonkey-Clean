#!/usr/bin/env python3
"""
Comprehensive test suite for enhanced TRIMP calculation system
Tests the enhanced calculate_banister_trimp() function with heart rate stream data
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strava_training_load import calculate_banister_trimp, _calculate_trimp_from_stream, _calculate_trimp_from_average, _validate_hr_stream_data, _round_trimp_value


class TestEnhancedTrimpCalculation(unittest.TestCase):
    """Test cases for enhanced TRIMP calculation with heart rate stream data"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hr_config = {
            'resting_hr': 50,
            'max_hr': 180,
            'gender': 'male'
        }
        
        # Sample heart rate stream data (1 sample per second for 10 minutes = 600 samples)
        self.sample_hr_stream = [120, 125, 130, 135, 140, 145, 150, 155, 160, 165] * 60  # 600 samples
        
        # Sample average heart rate
        self.sample_avg_hr = 142.5
        
        # Sample duration in minutes
        self.duration_minutes = 10.0
    
    def test_calculate_banister_trimp_with_stream_data(self):
        """Test TRIMP calculation with heart rate stream data"""
        trimp = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config,
            hr_stream=self.sample_hr_stream
        )
        
        # Verify TRIMP is calculated and is a positive number
        self.assertIsInstance(trimp, (int, float))
        self.assertGreater(trimp, 0)
        self.assertLess(trimp, 1000)  # Reasonable upper bound
        
        # Verify TRIMP is rounded to 2 decimal places
        self.assertEqual(len(str(trimp).split('.')[-1]), 2)
    
    def test_calculate_banister_trimp_without_stream_data(self):
        """Test TRIMP calculation without heart rate stream data (fallback to average)"""
        trimp = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config
        )
        
        # Verify TRIMP is calculated and is a positive number
        self.assertIsInstance(trimp, (int, float))
        self.assertGreater(trimp, 0)
        self.assertLess(trimp, 1000)  # Reasonable upper bound
        
        # Verify TRIMP is rounded to 2 decimal places
        self.assertEqual(len(str(trimp).split('.')[-1]), 2)
    
    def test_calculate_banister_trimp_backward_compatibility(self):
        """Test that existing function calls still work (backward compatibility)"""
        # This should work exactly as before
        trimp = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config
        )
        
        self.assertIsInstance(trimp, (int, float))
        self.assertGreater(trimp, 0)
    
    def test_calculate_trimp_from_stream_valid_data(self):
        """Test stream-based TRIMP calculation with valid data"""
        trimp = _calculate_trimp_from_stream(
            duration_minutes=self.duration_minutes,
            hr_stream=self.sample_hr_stream,
            hr_config=self.hr_config
        )
        
        self.assertIsInstance(trimp, (int, float))
        self.assertGreater(trimp, 0)
        self.assertLess(trimp, 1000)
    
    def test_calculate_trimp_from_stream_invalid_data(self):
        """Test stream-based TRIMP calculation with invalid data (should fallback)"""
        # Test with empty stream
        trimp_empty = _calculate_trimp_from_stream(
            duration_minutes=self.duration_minutes,
            hr_stream=[],
            hr_config=self.hr_config
        )
        
        # Should fallback to average HR calculation
        self.assertIsInstance(trimp_empty, (int, float))
        self.assertGreater(trimp_empty, 0)
        
        # Test with None stream
        trimp_none = _calculate_trimp_from_stream(
            duration_minutes=self.duration_minutes,
            hr_stream=None,
            hr_config=self.hr_config
        )
        
        self.assertIsInstance(trimp_none, (int, float))
        self.assertGreater(trimp_none, 0)
    
    def test_calculate_trimp_from_stream_physiological_bounds(self):
        """Test stream-based TRIMP calculation with HR data outside physiological bounds"""
        # Test with HR values too low
        low_hr_stream = [20, 25, 30] * 200  # 600 samples with very low HR
        trimp_low = _calculate_trimp_from_stream(
            duration_minutes=self.duration_minutes,
            hr_stream=low_hr_stream,
            hr_config=self.hr_config
        )
        
        # Should still calculate but may be very low
        self.assertIsInstance(trimp_low, (int, float))
        self.assertGreaterEqual(trimp_low, 0)
        
        # Test with HR values too high
        high_hr_stream = [200, 210, 220] * 200  # 600 samples with very high HR
        trimp_high = _calculate_trimp_from_stream(
            duration_minutes=self.duration_minutes,
            hr_stream=high_hr_stream,
            hr_config=self.hr_config
        )
        
        # Should still calculate but may be very high
        self.assertIsInstance(trimp_high, (int, float))
        self.assertGreater(trimp_high, 0)
    
    def test_calculate_trimp_from_average(self):
        """Test average HR-based TRIMP calculation"""
        trimp = _calculate_trimp_from_average(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config
        )
        
        self.assertIsInstance(trimp, (int, float))
        self.assertGreater(trimp, 0)
        self.assertLess(trimp, 1000)
    
    def test_validate_hr_stream_data_valid(self):
        """Test HR stream data validation with valid data"""
        is_valid, error_msg = _validate_hr_stream_data(self.sample_hr_stream, self.duration_minutes)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_hr_stream_data_empty(self):
        """Test HR stream data validation with empty data"""
        is_valid, error_msg = _validate_hr_stream_data([], self.duration_minutes)
        
        self.assertFalse(is_valid)
        self.assertIn("empty", error_msg.lower())
    
    def test_validate_hr_stream_data_none(self):
        """Test HR stream data validation with None data"""
        is_valid, error_msg = _validate_hr_stream_data(None, self.duration_minutes)
        
        self.assertFalse(is_valid)
        self.assertIn("none", error_msg.lower())
    
    def test_validate_hr_stream_data_insufficient_samples(self):
        """Test HR stream data validation with insufficient samples"""
        short_stream = [120, 125, 130]  # Only 3 samples for 10 minutes
        is_valid, error_msg = _validate_hr_stream_data(short_stream, self.duration_minutes)
        
        self.assertFalse(is_valid)
        self.assertIn("insufficient", error_msg.lower())
    
    def test_validate_hr_stream_data_invalid_hr_values(self):
        """Test HR stream data validation with invalid HR values"""
        invalid_stream = [120, -10, 130, 300, 140] * 120  # 600 samples with invalid values
        is_valid, error_msg = _validate_hr_stream_data(invalid_stream, self.duration_minutes)
        
        self.assertFalse(is_valid)
        self.assertIn("invalid", error_msg.lower())
    
    def test_round_trimp_value(self):
        """Test TRIMP value rounding to 2 decimal places"""
        # Test with various decimal places
        self.assertEqual(_round_trimp_value(123.456789), 123.46)
        self.assertEqual(_round_trimp_value(123.4), 123.40)
        self.assertEqual(_round_trimp_value(123), 123.00)
        self.assertEqual(_round_trimp_value(123.1), 123.10)
        self.assertEqual(_round_trimp_value(123.12), 123.12)
        self.assertEqual(_round_trimp_value(123.125), 123.13)  # Round up
    
    def test_trimp_calculation_consistency(self):
        """Test that TRIMP calculations are consistent for the same input"""
        # Calculate TRIMP multiple times with same input
        trimp1 = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config,
            hr_stream=self.sample_hr_stream
        )
        
        trimp2 = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config,
            hr_stream=self.sample_hr_stream
        )
        
        # Results should be identical
        self.assertEqual(trimp1, trimp2)
    
    def test_trimp_calculation_different_methods(self):
        """Test that stream-based and average-based calculations can produce different results"""
        # Calculate with stream data
        trimp_stream = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config,
            hr_stream=self.sample_hr_stream
        )
        
        # Calculate with average HR only
        trimp_average = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=self.hr_config
        )
        
        # Both should be valid TRIMP values
        self.assertIsInstance(trimp_stream, (int, float))
        self.assertIsInstance(trimp_average, (int, float))
        self.assertGreater(trimp_stream, 0)
        self.assertGreater(trimp_average, 0)
        
        # They may or may not be equal depending on the HR stream variation
        # This is expected behavior - stream-based should be more accurate
    
    def test_trimp_calculation_edge_cases(self):
        """Test TRIMP calculation with edge cases"""
        # Very short duration
        trimp_short = calculate_banister_trimp(
            duration_minutes=0.1,
            avg_hr=120,
            hr_config=self.hr_config
        )
        self.assertGreaterEqual(trimp_short, 0)
        
        # Very long duration
        trimp_long = calculate_banister_trimp(
            duration_minutes=480,  # 8 hours
            avg_hr=120,
            hr_config=self.hr_config
        )
        self.assertGreater(trimp_long, 0)
        self.assertLess(trimp_long, 10000)  # Reasonable upper bound
        
        # HR at resting level
        trimp_resting = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.hr_config['resting_hr'],
            hr_config=self.hr_config
        )
        self.assertGreaterEqual(trimp_resting, 0)
        
        # HR at max level
        trimp_max = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.hr_config['max_hr'],
            hr_config=self.hr_config
        )
        self.assertGreater(trimp_max, 0)
    
    def test_hr_config_validation(self):
        """Test TRIMP calculation with various HR configurations"""
        # Test with different resting HR
        hr_config_low_resting = self.hr_config.copy()
        hr_config_low_resting['resting_hr'] = 40
        
        trimp_low_resting = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=hr_config_low_resting
        )
        self.assertGreater(trimp_low_resting, 0)
        
        # Test with different max HR
        hr_config_high_max = self.hr_config.copy()
        hr_config_high_max['max_hr'] = 200
        
        trimp_high_max = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=hr_config_high_max
        )
        self.assertGreater(trimp_high_max, 0)
        
        # Test with female gender
        hr_config_female = self.hr_config.copy()
        hr_config_female['gender'] = 'female'
        
        trimp_female = calculate_banister_trimp(
            duration_minutes=self.duration_minutes,
            avg_hr=self.sample_avg_hr,
            hr_config=hr_config_female
        )
        self.assertGreater(trimp_female, 0)


class TestTrimpCalculationIntegration(unittest.TestCase):
    """Integration tests for TRIMP calculation with real-world scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.hr_config = {
            'resting_hr': 50,
            'max_hr': 180,
            'gender': 'male'
        }
    
    def test_cycling_workout_trimp(self):
        """Test TRIMP calculation for a typical cycling workout"""
        # 2-hour cycling workout with varying intensity
        duration = 120.0  # minutes
        avg_hr = 140
        
        # Create realistic HR stream with warm-up, main effort, and cool-down
        hr_stream = []
        # Warm-up: 10 minutes at 110-120 bpm
        hr_stream.extend([110 + i for i in range(10)] * 6)  # 60 samples
        # Main effort: 100 minutes at 140-160 bpm with variation
        for i in range(100):
            base_hr = 140 + (i % 20)  # Vary between 140-160
            hr_stream.extend([base_hr + j for j in range(6)])  # 6 samples per minute
        # Cool-down: 10 minutes at 110-120 bpm
        hr_stream.extend([120 - i for i in range(10)] * 6)  # 60 samples
        
        trimp = calculate_banister_trimp(
            duration_minutes=duration,
            avg_hr=avg_hr,
            hr_config=self.hr_config,
            hr_stream=hr_stream
        )
        
        # Should be a substantial TRIMP value for a 2-hour workout
        self.assertGreater(trimp, 100)
        self.assertLess(trimp, 2000)
    
    def test_running_workout_trimp(self):
        """Test TRIMP calculation for a typical running workout"""
        # 45-minute running workout
        duration = 45.0  # minutes
        avg_hr = 155
        
        # Create realistic HR stream for running
        hr_stream = []
        # Gradual increase in HR over the workout
        for minute in range(45):
            base_hr = 130 + minute  # HR increases from 130 to 175
            hr_stream.extend([base_hr + (i % 3) for i in range(6)])  # 6 samples per minute
        
        trimp = calculate_banister_trimp(
            duration_minutes=duration,
            avg_hr=avg_hr,
            hr_config=self.hr_config,
            hr_stream=hr_stream
        )
        
        # Should be a moderate TRIMP value for a 45-minute run
        self.assertGreater(trimp, 50)
        self.assertLess(trimp, 1000)
    
    def test_interval_workout_trimp(self):
        """Test TRIMP calculation for an interval workout"""
        # 30-minute interval workout
        duration = 30.0  # minutes
        avg_hr = 150
        
        # Create HR stream with intervals (high/low intensity)
        hr_stream = []
        for interval in range(6):  # 6 intervals of 5 minutes each
            if interval % 2 == 0:  # High intensity intervals
                hr_stream.extend([170 + (i % 5) for i in range(30)])  # 30 samples at high HR
            else:  # Recovery intervals
                hr_stream.extend([120 + (i % 3) for i in range(30)])  # 30 samples at low HR
        
        trimp = calculate_banister_trimp(
            duration_minutes=duration,
            avg_hr=avg_hr,
            hr_config=self.hr_config,
            hr_stream=hr_stream
        )
        
        # Should be a high TRIMP value due to intervals
        self.assertGreater(trimp, 30)
        self.assertLess(trimp, 500)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
