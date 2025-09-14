#!/usr/bin/env python3
"""
Mathematical Validation Tests for Exponential Decay Formula
Tests the mathematical accuracy and precision of the decay formula
"""

import sys
import os
import logging
import math
from datetime import datetime, date, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exponential_decay_engine import (
    ExponentialDecayEngine, ActivityData, DecayCalculationResult
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_exponential_decay_formula_accuracy():
    """Test mathematical accuracy of exponential decay formula"""
    logger.info("Testing exponential decay formula accuracy...")
    
    engine = ExponentialDecayEngine()
    
    # Test cases with known mathematical results
    test_cases = [
        # (days_ago, decay_rate, expected_weight, tolerance)
        (0, 0.05, 1.0, 1e-10),           # e^(-0.05 * 0) = e^0 = 1.0
        (1, 0.05, math.exp(-0.05), 1e-10),  # e^(-0.05 * 1) = e^(-0.05)
        (7, 0.05, math.exp(-0.35), 1e-10),  # e^(-0.05 * 7) = e^(-0.35)
        (14, 0.05, math.exp(-0.7), 1e-10),  # e^(-0.05 * 14) = e^(-0.7)
        (28, 0.05, math.exp(-1.4), 1e-10),  # e^(-0.05 * 28) = e^(-1.4)
        (0, 0.1, 1.0, 1e-10),            # e^(-0.1 * 0) = e^0 = 1.0
        (1, 0.1, math.exp(-0.1), 1e-10),    # e^(-0.1 * 1) = e^(-0.1)
        (7, 0.1, math.exp(-0.7), 1e-10),    # e^(-0.1 * 7) = e^(-0.7)
        (14, 0.1, math.exp(-1.4), 1e-10),   # e^(-0.1 * 14) = e^(-1.4)
        (28, 0.1, math.exp(-2.8), 1e-10),   # e^(-0.1 * 28) = e^(-2.8)
    ]
    
    for days_ago, decay_rate, expected_weight, tolerance in test_cases:
        calculated_weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        
        assert abs(calculated_weight - expected_weight) < tolerance, \
            f"Weight calculation error: days_ago={days_ago}, decay_rate={decay_rate}, " \
            f"expected={expected_weight:.10f}, calculated={calculated_weight:.10f}, " \
            f"difference={abs(calculated_weight - expected_weight):.2e}"
        
        logger.info(f"✅ {days_ago} days ago, decay_rate {decay_rate}: "
                   f"expected={expected_weight:.6f}, calculated={calculated_weight:.6f}")
    
    logger.info("✅ Exponential decay formula accuracy test passed")
    return True

def test_weight_monotonicity():
    """Test that weights decrease monotonically with days_ago"""
    logger.info("Testing weight monotonicity...")
    
    engine = ExponentialDecayEngine()
    decay_rate = 0.05
    
    # Test weights for consecutive days
    weights = []
    for days_ago in range(30):
        weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        weights.append(weight)
        
        # Weight should be between 0 and 1
        assert 0 <= weight <= 1, f"Weight should be between 0 and 1, got {weight} for {days_ago} days ago"
        
        # Weight should decrease with days_ago (monotonicity)
        if days_ago > 0:
            assert weight < weights[days_ago - 1], \
                f"Weight should decrease with days_ago: {days_ago-1} days = {weights[days_ago-1]:.6f}, " \
                f"{days_ago} days = {weight:.6f}"
    
    logger.info(f"✅ Weight monotonicity verified for {len(weights)} consecutive days")
    logger.info("✅ Weight monotonicity test passed")
    return True

def test_decay_rate_impact():
    """Test impact of different decay rates on weight calculation"""
    logger.info("Testing decay rate impact...")
    
    engine = ExponentialDecayEngine()
    days_ago = 7  # Fixed number of days ago
    
    decay_rates = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
    weights = []
    
    for decay_rate in decay_rates:
        weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        weights.append(weight)
        
        # Higher decay rate should result in lower weight
        expected_weight = math.exp(-decay_rate * days_ago)
        assert abs(weight - expected_weight) < 1e-10, \
            f"Weight calculation error for decay_rate {decay_rate}: expected={expected_weight:.10f}, " \
            f"calculated={weight:.10f}"
        
        logger.info(f"✅ decay_rate {decay_rate}: weight = {weight:.6f}")
    
    # Verify that higher decay rates result in lower weights
    for i in range(1, len(decay_rates)):
        assert weights[i] < weights[i-1], \
            f"Higher decay rate should result in lower weight: decay_rate {decay_rates[i-1]} = {weights[i-1]:.6f}, " \
            f"decay_rate {decay_rates[i]} = {weights[i]:.6f}"
    
    logger.info("✅ Decay rate impact test passed")
    return True

def test_weighted_average_mathematical_properties():
    """Test mathematical properties of weighted averages"""
    logger.info("Testing weighted average mathematical properties...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create test activities with known values
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),  # Weight = 1.0
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=20.0, trimp=16.0), # Weight = e^(-0.05)
        ActivityData(date=reference_date - timedelta(days=7), total_load_miles=30.0, trimp=24.0), # Weight = e^(-0.35)
    ]
    
    result = engine.calculate_weighted_averages(activities, decay_rate, reference_date)
    
    # Calculate expected weighted averages manually
    w0 = math.exp(-0.05 * 0)  # 1.0
    w1 = math.exp(-0.05 * 1)  # e^(-0.05)
    w7 = math.exp(-0.05 * 7)  # e^(-0.35)
    
    expected_weighted_load_sum = 10.0 * w0 + 20.0 * w1 + 30.0 * w7
    expected_weighted_trimp_sum = 8.0 * w0 + 16.0 * w1 + 24.0 * w7
    expected_total_weight = w0 + w1 + w7
    expected_weighted_load_avg = expected_weighted_load_sum / expected_total_weight
    expected_weighted_trimp_avg = expected_weighted_trimp_sum / expected_total_weight
    
    # Verify calculations (account for rounding to 3 decimal places)
    assert abs(result.weighted_load_sum - expected_weighted_load_sum) < 1e-3, \
        f"Weighted load sum error: expected={expected_weighted_load_sum:.10f}, " \
        f"calculated={result.weighted_load_sum:.10f}"
    
    assert abs(result.weighted_trimp_sum - expected_weighted_trimp_sum) < 1e-3, \
        f"Weighted TRIMP sum error: expected={expected_weighted_trimp_sum:.10f}, " \
        f"calculated={result.weighted_trimp_sum:.10f}"
    
    assert abs(result.total_weight - expected_total_weight) < 1e-3, \
        f"Total weight error: expected={expected_total_weight:.10f}, " \
        f"calculated={result.total_weight:.10f}"
    
    assert abs(result.weighted_load_avg - expected_weighted_load_avg) < 1e-3, \
        f"Weighted load average error: expected={expected_weighted_load_avg:.10f}, " \
        f"calculated={result.weighted_load_avg:.10f}"
    
    assert abs(result.weighted_trimp_avg - expected_weighted_trimp_avg) < 1e-3, \
        f"Weighted TRIMP average error: expected={expected_weighted_trimp_avg:.10f}, " \
        f"calculated={result.weighted_trimp_avg:.10f}"
    
    logger.info(f"✅ Weighted averages: load_avg={result.weighted_load_avg:.6f}, trimp_avg={result.weighted_trimp_avg:.6f}")
    logger.info("✅ Weighted average mathematical properties test passed")
    return True

def test_acwr_ratio_mathematical_properties():
    """Test mathematical properties of ACWR ratios"""
    logger.info("Testing ACWR ratio mathematical properties...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create acute activities (simple average)
    acute_activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=20.0, trimp=16.0),
    ]
    
    # Create chronic activities (exponential weighted average)
    chronic_activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=15.0, trimp=12.0)
        for i in range(28)  # 28 days of consistent data
    ]
    
    result = engine.calculate_enhanced_acwr(acute_activities, chronic_activities, decay_rate, reference_date)
    
    # Calculate expected values
    expected_acute_load_avg = (10.0 + 20.0) / 2  # 15.0
    expected_acute_trimp_avg = (8.0 + 16.0) / 2  # 12.0
    
    # Chronic activities are all the same, so weighted average should be 15.0 and 12.0
    expected_chronic_load_avg = 15.0
    expected_chronic_trimp_avg = 12.0
    
    expected_acute_chronic_ratio = expected_acute_load_avg / expected_chronic_load_avg  # 15.0 / 15.0 = 1.0
    expected_trimp_acute_chronic_ratio = expected_acute_trimp_avg / expected_chronic_trimp_avg  # 12.0 / 12.0 = 1.0
    
    # Verify calculations
    assert abs(result['acute_load_avg'] - expected_acute_load_avg) < 1e-10, \
        f"Acute load average error: expected={expected_acute_load_avg}, calculated={result['acute_load_avg']}"
    
    assert abs(result['acute_trimp_avg'] - expected_acute_trimp_avg) < 1e-10, \
        f"Acute TRIMP average error: expected={expected_acute_trimp_avg}, calculated={result['acute_trimp_avg']}"
    
    assert abs(result['enhanced_chronic_load'] - expected_chronic_load_avg) < 1e-6, \
        f"Enhanced chronic load error: expected={expected_chronic_load_avg}, calculated={result['enhanced_chronic_load']}"
    
    assert abs(result['enhanced_chronic_trimp'] - expected_chronic_trimp_avg) < 1e-6, \
        f"Enhanced chronic TRIMP error: expected={expected_chronic_trimp_avg}, calculated={result['enhanced_chronic_trimp']}"
    
    assert abs(result['enhanced_acute_chronic_ratio'] - expected_acute_chronic_ratio) < 1e-6, \
        f"ACWR ratio error: expected={expected_acute_chronic_ratio}, calculated={result['enhanced_acute_chronic_ratio']}"
    
    assert abs(result['enhanced_trimp_acute_chronic_ratio'] - expected_trimp_acute_chronic_ratio) < 1e-6, \
        f"TRIMP ACWR ratio error: expected={expected_trimp_acute_chronic_ratio}, calculated={result['enhanced_trimp_acute_chronic_ratio']}"
    
    logger.info(f"✅ ACWR ratios: load_ratio={result['enhanced_acute_chronic_ratio']:.6f}, "
               f"trimp_ratio={result['enhanced_trimp_acute_chronic_ratio']:.6f}")
    logger.info("✅ ACWR ratio mathematical properties test passed")
    return True

def test_precision_and_rounding():
    """Test precision and rounding of calculations"""
    logger.info("Testing precision and rounding...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create activities with precise values
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.123456789, trimp=8.987654321),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=20.987654321, trimp=16.123456789),
        ActivityData(date=reference_date - timedelta(days=7), total_load_miles=30.555555555, trimp=24.444444444),
    ]
    
    result = engine.calculate_weighted_averages(activities, decay_rate, reference_date)
    
    # Verify that results are rounded to 3 decimal places
    assert result.weighted_load_avg == round(result.weighted_load_avg, 3), \
        f"Weighted load average should be rounded to 3 decimal places: {result.weighted_load_avg}"
    
    assert result.weighted_trimp_avg == round(result.weighted_trimp_avg, 3), \
        f"Weighted TRIMP average should be rounded to 3 decimal places: {result.weighted_trimp_avg}"
    
    # Test ACWR calculation precision
    acute_activities = activities[:1]
    chronic_activities = activities
    
    acwr_result = engine.calculate_enhanced_acwr(acute_activities, chronic_activities, decay_rate, reference_date)
    
    # Verify all ACWR values are rounded to 3 decimal places
    for key in ['acute_load_avg', 'acute_trimp_avg', 'enhanced_chronic_load', 'enhanced_chronic_trimp',
                'enhanced_acute_chronic_ratio', 'enhanced_trimp_acute_chronic_ratio', 'enhanced_normalized_divergence']:
        assert acwr_result[key] == round(acwr_result[key], 3), \
            f"{key} should be rounded to 3 decimal places: {acwr_result[key]}"
    
    logger.info(f"✅ Precision test: load_avg={result.weighted_load_avg}, trimp_avg={result.weighted_trimp_avg}")
    logger.info("✅ Precision and rounding test passed")
    return True

def test_boundary_conditions():
    """Test boundary conditions for mathematical calculations"""
    logger.info("Testing boundary conditions...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test decay rate boundaries
    assert engine.calculate_exponential_weight(0, 0.001) == 1.0, "Weight should be 1.0 for 0 days ago"
    assert engine.calculate_exponential_weight(0, 1.0) == 1.0, "Weight should be 1.0 for 0 days ago"
    
    # Test very small decay rate
    weight_small_decay = engine.calculate_exponential_weight(1, 0.001)
    expected_small_decay = math.exp(-0.001)
    assert abs(weight_small_decay - expected_small_decay) < 1e-10, \
        f"Small decay rate error: expected={expected_small_decay:.10f}, calculated={weight_small_decay:.10f}"
    
    # Test maximum decay rate
    weight_max_decay = engine.calculate_exponential_weight(1, 1.0)
    expected_max_decay = math.exp(-1.0)
    assert abs(weight_max_decay - expected_max_decay) < 1e-10, \
        f"Max decay rate error: expected={expected_max_decay:.10f}, calculated={weight_max_decay:.10f}"
    
    # Test large number of days ago
    weight_large_days = engine.calculate_exponential_weight(100, 0.05)
    expected_large_days = math.exp(-5.0)
    assert abs(weight_large_days - expected_large_days) < 1e-10, \
        f"Large days ago error: expected={expected_large_days:.10f}, calculated={weight_large_days:.10f}"
    
    logger.info("✅ Boundary conditions test passed")
    return True

def test_mathematical_consistency():
    """Test mathematical consistency across different calculation methods"""
    logger.info("Testing mathematical consistency...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create consistent test data
    activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0 + i, trimp=8.0 + i)
        for i in range(14)
    ]
    
    # Test 1: Direct weight calculation vs weighted averages
    direct_weights = []
    for activity in activities:
        days_ago = (reference_date - activity.date).days
        weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        direct_weights.append(weight)
    
    result = engine.calculate_weighted_averages(activities, decay_rate, reference_date)
    
    # Verify that the weights used in weighted averages match direct calculations
    for i, activity in enumerate(activities):
        days_ago = (reference_date - activity.date).days
        expected_weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        assert abs(activity.weight - expected_weight) < 1e-10, \
            f"Weight consistency error for activity {i}: expected={expected_weight:.10f}, " \
            f"stored={activity.weight:.10f}"
    
    # Test 2: Comparison with standard calculation
    comparison = engine.compare_with_standard_calculation(activities, decay_rate, reference_date)
    
    # Verify that exponential decay result matches our calculation
    assert abs(comparison['exponential_decay']['weighted_load_avg'] - result.weighted_load_avg) < 1e-10, \
        f"Comparison consistency error: weighted_averages={result.weighted_load_avg:.10f}, " \
        f"comparison={comparison['exponential_decay']['weighted_load_avg']:.10f}"
    
    logger.info("✅ Mathematical consistency test passed")
    return True

def run_all_tests():
    """Run all mathematical validation tests"""
    logger.info("=" * 60)
    logger.info("Mathematical Validation Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Exponential Decay Formula Accuracy", test_exponential_decay_formula_accuracy),
        ("Weight Monotonicity", test_weight_monotonicity),
        ("Decay Rate Impact", test_decay_rate_impact),
        ("Weighted Average Mathematical Properties", test_weighted_average_mathematical_properties),
        ("ACWR Ratio Mathematical Properties", test_acwr_ratio_mathematical_properties),
        ("Precision and Rounding", test_precision_and_rounding),
        ("Boundary Conditions", test_boundary_conditions),
        ("Mathematical Consistency", test_mathematical_consistency)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 All tests passed! Mathematical validation is complete.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

def main():
    """Run the test suite"""
    success = run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
