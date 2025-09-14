#!/usr/bin/env python3
"""
Test script for Exponential Decay Engine
Tests the core mathematical engine for ACWR calculations
"""

import sys
import os
import logging
import math
from datetime import datetime, date, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exponential_decay_engine import (
    ExponentialDecayEngine, ActivityData, DecayCalculationResult,
    calculate_exponential_weight, calculate_weighted_averages, calculate_enhanced_acwr
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_exponential_weight_calculation():
    """Test exponential weight calculation"""
    logger.info("Testing exponential weight calculation...")
    
    engine = ExponentialDecayEngine()
    
    # Test cases: (days_ago, decay_rate, expected_weight_range)
    test_cases = [
        (0, 0.05, (0.95, 1.0)),      # Today: weight should be close to 1.0
        (1, 0.05, (0.95, 1.0)),      # 1 day ago: weight should be ~0.951
        (7, 0.05, (0.70, 0.75)),     # 1 week ago: weight should be ~0.705
        (14, 0.05, (0.49, 0.55)),    # 2 weeks ago: weight should be ~0.497
        (28, 0.05, (0.24, 0.30)),    # 4 weeks ago: weight should be ~0.247
        (0, 0.1, (0.90, 1.0)),       # Higher decay rate: today should still be ~1.0
        (7, 0.1, (0.45, 0.55)),      # Higher decay rate: 1 week ago should be ~0.497
    ]
    
    for days_ago, decay_rate, expected_range in test_cases:
        weight = engine.calculate_exponential_weight(days_ago, decay_rate)
        
        assert expected_range[0] <= weight <= expected_range[1], \
            f"Weight for {days_ago} days ago with decay_rate {decay_rate} should be in range {expected_range}, got {weight}"
        
        # Verify mathematical formula
        expected_weight = math.exp(-decay_rate * days_ago)
        assert abs(weight - expected_weight) < 0.001, \
            f"Weight calculation doesn't match formula: expected {expected_weight}, got {weight}"
        
        logger.info(f"✅ {days_ago} days ago, decay_rate {decay_rate}: weight = {weight:.6f}")
    
    logger.info("✅ Exponential weight calculation test passed")
    return True

def test_exponential_weight_validation():
    """Test exponential weight validation"""
    logger.info("Testing exponential weight validation...")
    
    engine = ExponentialDecayEngine()
    
    # Test invalid inputs
    invalid_cases = [
        (-1, 0.05, "days_ago must be non-negative"),
        (0, -0.05, "decay_rate must be between 0 and 1"),
        (0, 0.0, "decay_rate must be between 0 and 1"),
        (0, 1.5, "decay_rate must be between 0 and 1"),
    ]
    
    for days_ago, decay_rate, expected_error in invalid_cases:
        try:
            weight = engine.calculate_exponential_weight(days_ago, decay_rate)
            assert False, f"Should have raised ValueError for days_ago={days_ago}, decay_rate={decay_rate}"
        except ValueError as e:
            assert expected_error in str(e), f"Expected error message '{expected_error}' not found in '{str(e)}'"
            logger.info(f"✅ Correctly rejected invalid input: days_ago={days_ago}, decay_rate={decay_rate}")
    
    logger.info("✅ Exponential weight validation test passed")
    return True

def test_weighted_averages_calculation():
    """Test weighted averages calculation"""
    logger.info("Testing weighted averages calculation...")
    
    engine = ExponentialDecayEngine()
    
    # Create test activities
    reference_date = date(2025, 9, 7)
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),  # Today
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=8.0, trimp=6.0),   # 1 day ago
        ActivityData(date=reference_date - timedelta(days=7), total_load_miles=12.0, trimp=10.0), # 1 week ago
        ActivityData(date=reference_date - timedelta(days=14), total_load_miles=6.0, trimp=4.0),  # 2 weeks ago
    ]
    
    decay_rate = 0.05
    result = engine.calculate_weighted_averages(activities, decay_rate, reference_date)
    
    # Verify result structure
    assert isinstance(result, DecayCalculationResult), "Result should be DecayCalculationResult"
    assert result.calculation_method == 'exponential_decay', "Calculation method should be exponential_decay"
    assert result.decay_rate == decay_rate, "Decay rate should match input"
    assert result.activity_count == 4, "Should have 4 activities"
    assert result.total_weight > 0, "Total weight should be positive"
    
    # Verify weighted averages are reasonable
    assert result.weighted_load_avg > 0, "Weighted load average should be positive"
    assert result.weighted_trimp_avg > 0, "Weighted TRIMP average should be positive"
    
    # Verify that recent activities have higher weights
    assert activities[0].weight > activities[1].weight, "Today's activity should have higher weight than yesterday's"
    assert activities[1].weight > activities[2].weight, "Yesterday's activity should have higher weight than last week's"
    
    logger.info(f"✅ Weighted averages: load_avg={result.weighted_load_avg:.3f}, trimp_avg={result.weighted_trimp_avg:.3f}")
    logger.info("✅ Weighted averages calculation test passed")
    return True

def test_empty_activities_handling():
    """Test handling of empty activities list"""
    logger.info("Testing empty activities handling...")
    
    engine = ExponentialDecayEngine()
    
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    result = engine.calculate_weighted_averages([], decay_rate, reference_date)
    
    assert result.weighted_load_sum == 0.0, "Empty activities should result in zero load sum"
    assert result.weighted_trimp_sum == 0.0, "Empty activities should result in zero TRIMP sum"
    assert result.total_weight == 0.0, "Empty activities should result in zero total weight"
    assert result.weighted_load_avg == 0.0, "Empty activities should result in zero load average"
    assert result.weighted_trimp_avg == 0.0, "Empty activities should result in zero TRIMP average"
    assert result.activity_count == 0, "Empty activities should result in zero activity count"
    
    logger.info("✅ Empty activities handling test passed")
    return True

def test_enhanced_acwr_calculation():
    """Test enhanced ACWR calculation"""
    logger.info("Testing enhanced ACWR calculation...")
    
    engine = ExponentialDecayEngine()
    
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create acute activities (7 days)
    acute_activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=reference_date - timedelta(days=3), total_load_miles=6.0, trimp=4.0),
        ActivityData(date=reference_date - timedelta(days=4), total_load_miles=9.0, trimp=7.0),
        ActivityData(date=reference_date - timedelta(days=5), total_load_miles=11.0, trimp=9.0),
        ActivityData(date=reference_date - timedelta(days=6), total_load_miles=7.0, trimp=5.0),
    ]
    
    # Create chronic activities (28 days)
    chronic_activities = []
    for i in range(28):
        chronic_activities.append(ActivityData(
            date=reference_date - timedelta(days=i),
            total_load_miles=8.0 + (i % 3),  # Vary load slightly
            trimp=6.0 + (i % 2)  # Vary TRIMP slightly
        ))
    
    result = engine.calculate_enhanced_acwr(acute_activities, chronic_activities, decay_rate, reference_date)
    
    # Verify result structure
    assert 'acute_load_avg' in result, "Result should contain acute_load_avg"
    assert 'acute_trimp_avg' in result, "Result should contain acute_trimp_avg"
    assert 'enhanced_chronic_load' in result, "Result should contain enhanced_chronic_load"
    assert 'enhanced_chronic_trimp' in result, "Result should contain enhanced_chronic_trimp"
    assert 'enhanced_acute_chronic_ratio' in result, "Result should contain enhanced_acute_chronic_ratio"
    assert 'enhanced_trimp_acute_chronic_ratio' in result, "Result should contain enhanced_trimp_acute_chronic_ratio"
    assert 'enhanced_normalized_divergence' in result, "Result should contain enhanced_normalized_divergence"
    assert 'decay_rate' in result, "Result should contain decay_rate"
    assert 'calculation_method' in result, "Result should contain calculation_method"
    
    # Verify values are reasonable
    assert result['acute_load_avg'] > 0, "Acute load average should be positive"
    assert result['acute_trimp_avg'] > 0, "Acute TRIMP average should be positive"
    assert result['enhanced_chronic_load'] > 0, "Enhanced chronic load should be positive"
    assert result['enhanced_chronic_trimp'] > 0, "Enhanced chronic TRIMP should be positive"
    assert result['enhanced_acute_chronic_ratio'] > 0, "ACWR ratio should be positive"
    assert result['enhanced_trimp_acute_chronic_ratio'] > 0, "TRIMP ACWR ratio should be positive"
    assert result['decay_rate'] == decay_rate, "Decay rate should match input"
    assert result['calculation_method'] == 'exponential_decay', "Calculation method should be exponential_decay"
    
    logger.info(f"✅ Enhanced ACWR: acute_ratio={result['enhanced_acute_chronic_ratio']:.3f}, "
               f"trimp_ratio={result['enhanced_trimp_acute_chronic_ratio']:.3f}")
    logger.info("✅ Enhanced ACWR calculation test passed")
    return True

def test_comparison_with_standard_calculation():
    """Test comparison with standard calculation"""
    logger.info("Testing comparison with standard calculation...")
    
    engine = ExponentialDecayEngine()
    
    reference_date = date(2025, 9, 7)
    decay_rate = 0.05
    
    # Create activities with varying loads
    activities = []
    for i in range(14):  # 2 weeks of activities
        activities.append(ActivityData(
            date=reference_date - timedelta(days=i),
            total_load_miles=10.0 + (i % 3),  # Vary load
            trimp=8.0 + (i % 2)  # Vary TRIMP
        ))
    
    comparison = engine.compare_with_standard_calculation(activities, decay_rate, reference_date)
    
    # Verify comparison structure
    assert 'exponential_decay' in comparison, "Comparison should contain exponential_decay results"
    assert 'standard_average' in comparison, "Comparison should contain standard_average results"
    assert 'differences' in comparison, "Comparison should contain differences"
    
    # Verify exponential decay results
    exp_result = comparison['exponential_decay']
    assert 'weighted_load_avg' in exp_result, "Exponential decay should contain weighted_load_avg"
    assert 'weighted_trimp_avg' in exp_result, "Exponential decay should contain weighted_trimp_avg"
    assert 'total_weight' in exp_result, "Exponential decay should contain total_weight"
    
    # Verify standard average results
    std_result = comparison['standard_average']
    assert 'load_avg' in std_result, "Standard average should contain load_avg"
    assert 'trimp_avg' in std_result, "Standard average should contain trimp_avg"
    
    # Verify differences
    diff_result = comparison['differences']
    assert 'load_difference' in diff_result, "Differences should contain load_difference"
    assert 'trimp_difference' in diff_result, "Differences should contain trimp_difference"
    assert 'load_percentage_diff' in diff_result, "Differences should contain load_percentage_diff"
    assert 'trimp_percentage_diff' in diff_result, "Differences should contain trimp_percentage_diff"
    
    # Verify that exponential decay gives different results than standard average
    assert abs(diff_result['load_difference']) > 0.001, "Load difference should be significant"
    assert abs(diff_result['trimp_difference']) > 0.001, "TRIMP difference should be significant"
    
    logger.info(f"✅ Comparison: load_diff={diff_result['load_difference']:.3f} "
               f"({diff_result['load_percentage_diff']:.1f}%), "
               f"trimp_diff={diff_result['trimp_difference']:.3f} "
               f"({diff_result['trimp_percentage_diff']:.1f}%)")
    logger.info("✅ Comparison with standard calculation test passed")
    return True

def test_decay_rate_validation():
    """Test decay rate validation"""
    logger.info("Testing decay rate validation...")
    
    engine = ExponentialDecayEngine()
    
    # Test valid decay rates
    valid_rates = [0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
    for rate in valid_rates:
        assert engine.validate_decay_rate(rate), f"Decay rate {rate} should be valid"
        logger.info(f"✅ Decay rate {rate} is valid")
    
    # Test invalid decay rates
    invalid_rates = [-0.1, 0.0, 1.1, 2.0, "invalid", None]
    for rate in invalid_rates:
        assert not engine.validate_decay_rate(rate), f"Decay rate {rate} should be invalid"
        logger.info(f"✅ Decay rate {rate} is correctly rejected")
    
    logger.info("✅ Decay rate validation test passed")
    return True

def test_weight_distribution():
    """Test weight distribution calculation"""
    logger.info("Testing weight distribution calculation...")
    
    engine = ExponentialDecayEngine()
    
    days_range = 14
    decay_rate = 0.05
    
    distribution = engine.get_weight_distribution(days_range, decay_rate)
    
    # Verify distribution structure
    assert len(distribution) == days_range, f"Distribution should have {days_range} entries"
    
    for i, entry in enumerate(distribution):
        assert 'days_ago' in entry, f"Entry {i} should contain days_ago"
        assert 'weight' in entry, f"Entry {i} should contain weight"
        assert 'weight_percentage' in entry, f"Entry {i} should contain weight_percentage"
        
        assert entry['days_ago'] == i, f"Entry {i} should have days_ago = {i}"
        assert 0 <= entry['weight'] <= 1, f"Entry {i} weight should be between 0 and 1"
        assert 0 <= entry['weight_percentage'] <= 100, f"Entry {i} weight_percentage should be between 0 and 100"
        
        # Verify weight decreases with days_ago
        if i > 0:
            assert entry['weight'] < distribution[i-1]['weight'], f"Weight should decrease with days_ago"
    
    logger.info(f"✅ Weight distribution calculated for {days_range} days")
    logger.info("✅ Weight distribution test passed")
    return True

def test_chronic_period_validation():
    """Test chronic period validation"""
    logger.info("Testing chronic period validation...")
    
    engine = ExponentialDecayEngine()
    
    # Test valid chronic periods
    valid_periods = [28, 35, 42, 56, 70, 90]
    for period in valid_periods:
        assert engine.validate_chronic_period(period), f"Chronic period {period} should be valid"
        logger.info(f"✅ Chronic period {period} is valid")
    
    # Test invalid chronic periods
    invalid_periods = [0, 14, 27, 91, 100, -5, "invalid", None]
    for period in invalid_periods:
        assert not engine.validate_chronic_period(period), f"Chronic period {period} should be invalid"
        logger.info(f"✅ Chronic period {period} is correctly rejected")
    
    logger.info("✅ Chronic period validation test passed")
    return True

def test_activity_data_validation():
    """Test activity data validation"""
    logger.info("Testing activity data validation...")
    
    engine = ExponentialDecayEngine()
    
    # Test valid activity data
    reference_date = date(2025, 9, 7)
    valid_activities = [
        ActivityData(date=reference_date, total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=0.0, trimp=0.0),
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=15.5, trimp=12.3),
    ]
    
    assert engine.validate_activity_data(valid_activities), "Valid activities should pass validation"
    logger.info("✅ Valid activity data passed validation")
    
    # Test invalid activity data
    invalid_activities_cases = [
        # Not a list
        ("not a list", "Activities must be a list"),
        # Invalid activity type
        ([{"date": reference_date, "total_load_miles": 10.0, "trimp": 8.0}], "Activity 0 must be ActivityData instance"),
        # Invalid date type
        ([ActivityData(date="2025-09-07", total_load_miles=10.0, trimp=8.0)], "Activity 0 date must be date instance"),
        # Invalid load type
        ([ActivityData(date=reference_date, total_load_miles="10.0", trimp=8.0)], "Activity 0 total_load_miles must be numeric"),
        # Negative load
        ([ActivityData(date=reference_date, total_load_miles=-5.0, trimp=8.0)], "Activity 0 total_load_miles must be non-negative"),
        # Invalid TRIMP type
        ([ActivityData(date=reference_date, total_load_miles=10.0, trimp="8.0")], "Activity 0 trimp must be numeric"),
        # Negative TRIMP
        ([ActivityData(date=reference_date, total_load_miles=10.0, trimp=-2.0)], "Activity 0 trimp must be non-negative"),
    ]
    
    for invalid_activities, expected_error in invalid_activities_cases:
        assert not engine.validate_activity_data(invalid_activities), f"Invalid activities should fail validation: {expected_error}"
        logger.info(f"✅ Invalid activity data correctly rejected: {expected_error}")
    
    logger.info("✅ Activity data validation test passed")
    return True

def test_convenience_functions():
    """Test convenience functions"""
    logger.info("Testing convenience functions...")
    
    # Test calculate_exponential_weight
    weight = calculate_exponential_weight(7, 0.05)
    expected_weight = math.exp(-0.05 * 7)
    assert abs(weight - expected_weight) < 0.001, "Convenience function should match direct calculation"
    
    # Test calculate_weighted_averages
    reference_date = date(2025, 9, 7)
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=8.0, trimp=6.0),
    ]
    
    result = calculate_weighted_averages(activities, 0.05, reference_date)
    assert isinstance(result, DecayCalculationResult), "Convenience function should return DecayCalculationResult"
    
    # Test calculate_enhanced_acwr
    acute_activities = activities[:1]
    chronic_activities = activities
    
    acwr_result = calculate_enhanced_acwr(acute_activities, chronic_activities, 0.05, reference_date)
    assert isinstance(acwr_result, dict), "Convenience function should return dictionary"
    assert 'enhanced_acute_chronic_ratio' in acwr_result, "Result should contain ACWR ratio"
    
    logger.info("✅ Convenience functions test passed")
    return True

def run_all_tests():
    """Run all exponential decay engine tests"""
    logger.info("=" * 60)
    logger.info("Exponential Decay Engine Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Exponential Weight Calculation", test_exponential_weight_calculation),
        ("Exponential Weight Validation", test_exponential_weight_validation),
        ("Weighted Averages Calculation", test_weighted_averages_calculation),
        ("Empty Activities Handling", test_empty_activities_handling),
        ("Enhanced ACWR Calculation", test_enhanced_acwr_calculation),
        ("Comparison with Standard Calculation", test_comparison_with_standard_calculation),
        ("Decay Rate Validation", test_decay_rate_validation),
        ("Chronic Period Validation", test_chronic_period_validation),
        ("Activity Data Validation", test_activity_data_validation),
        ("Weight Distribution", test_weight_distribution),
        ("Convenience Functions", test_convenience_functions)
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
        logger.info("🎉 All tests passed! Exponential Decay Engine is working correctly.")
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
