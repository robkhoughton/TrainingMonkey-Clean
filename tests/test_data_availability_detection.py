#!/usr/bin/env python3
"""
Test script for Data Availability Detection
Tests the data availability detection and optimal chronic period functionality
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exponential_decay_engine import (
    ExponentialDecayEngine, ActivityData
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_no_data_availability():
    """Test data availability detection with no data"""
    logger.info("Testing no data availability...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    result = engine.detect_data_availability([], reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert not result['available'], "Should not be available with no data"
    assert result['reason'] == 'no_data', "Should identify no data reason"
    assert result['days_available'] == 0, "Should have 0 days available"
    assert result['chronic_period_days'] == 28, "Should preserve chronic period days"
    assert result['minimum_required_days'] == 7, "Should preserve minimum required days"
    
    logger.info("✅ No data availability test passed")
    return True

def test_insufficient_data_availability():
    """Test data availability detection with insufficient data"""
    logger.info("Testing insufficient data availability...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create only 3 days of data (less than minimum 7)
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=12.0, trimp=10.0),
    ]
    
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert not result['available'], "Should not be available with insufficient data"
    assert result['reason'] == 'insufficient_data', "Should identify insufficient data reason"
    assert result['days_available'] == 3, "Should have 3 days available"
    assert "Only 3 days of data available" in result['message'], "Should mention insufficient days"
    assert 'chronic_activities' in result, "Should include chronic activities"
    
    logger.info("✅ Insufficient data availability test passed")
    return True

def test_sufficient_data_availability():
    """Test data availability detection with sufficient data"""
    logger.info("Testing sufficient data availability...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create 14 days of data (more than minimum 7)
    activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0 + i, trimp=8.0 + i)
        for i in range(14)
    ]
    
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert result['available'], "Should be available with sufficient data"
    assert result['reason'] == 'sufficient_data', "Should identify sufficient data reason"
    assert result['days_available'] == 14, "Should have 14 days available"
    assert result['coverage_percentage'] == 50.0, "Should have 50% coverage (14/28)"
    assert 'gap_analysis' in result, "Should include gap analysis"
    assert 'data_quality' in result, "Should include data quality assessment"
    assert 'chronic_activities' in result, "Should include chronic activities"
    
    logger.info(f"✅ Sufficient data: {result['days_available']} days, {result['coverage_percentage']:.1f}% coverage")
    logger.info("✅ Sufficient data availability test passed")
    return True

def test_data_gap_analysis():
    """Test data gap analysis functionality"""
    logger.info("Testing data gap analysis...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create activities with gaps but enough days to meet minimum requirement
    activities = [
        ActivityData(date=reference_date - timedelta(days=0), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=8.0, trimp=6.0),  # Gap of 1 day
        ActivityData(date=reference_date - timedelta(days=5), total_load_miles=12.0, trimp=10.0), # Gap of 2 days
        ActivityData(date=reference_date - timedelta(days=10), total_load_miles=9.0, trimp=7.0),  # Gap of 4 days
        ActivityData(date=reference_date - timedelta(days=12), total_load_miles=11.0, trimp=9.0), # Gap of 1 day
        ActivityData(date=reference_date - timedelta(days=15), total_load_miles=7.0, trimp=5.0),  # Gap of 2 days
        ActivityData(date=reference_date - timedelta(days=18), total_load_miles=13.0, trimp=11.0), # Gap of 2 days
        ActivityData(date=reference_date - timedelta(days=20), total_load_miles=6.0, trimp=4.0),  # Gap of 1 day
    ]  # Total: 8 activities, 8 unique days, meets minimum requirement of 7
    
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert result['available'], "Should be available despite gaps"
    assert 'gap_analysis' in result, "Should include gap analysis"
    
    gap_analysis = result['gap_analysis']
    assert gap_analysis['total_gaps'] == 7, f"Should detect 7 gaps, got {gap_analysis['total_gaps']}"
    assert gap_analysis['gap_days'] == 13, f"Should have 13 gap days total, got {gap_analysis['gap_days']}"
    assert gap_analysis['largest_gap'] == 4, f"Should have largest gap of 4 days, got {gap_analysis['largest_gap']}"
    assert len(gap_analysis['gaps']) == 7, f"Should have 7 gap entries, got {len(gap_analysis['gaps'])}"
    
    # Test gap details
    gap_days = [gap['gap_days'] for gap in gap_analysis['gaps']]
    assert 1 in gap_days, "Should have 1-day gap"
    assert 2 in gap_days, "Should have 2-day gap"
    assert 4 in gap_days, "Should have 4-day gap"
    
    logger.info(f"✅ Gap analysis: {gap_analysis['total_gaps']} gaps, {gap_analysis['gap_days']} gap days")
    logger.info("✅ Data gap analysis test passed")
    return True

def test_data_quality_assessment():
    """Test data quality assessment"""
    logger.info("Testing data quality assessment...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test excellent quality (28 days, no gaps)
    excellent_activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(28)
    ]
    
    result = engine.detect_data_availability(excellent_activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    assert result['data_quality'] == 'excellent', f"Should be excellent quality, got {result['data_quality']}"
    
    # Test good quality (21 days, small gaps)
    good_activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(0, 21, 1)  # Every day for 21 days
    ]
    
    result = engine.detect_data_availability(good_activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    assert result['data_quality'] in ['good', 'excellent'], f"Should be good or excellent quality, got {result['data_quality']}"
    
    # Test fair quality (14 days, some gaps)
    fair_activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(0, 14, 1)  # Every day for 14 days
    ]
    
    result = engine.detect_data_availability(fair_activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    assert result['data_quality'] in ['fair', 'good'], f"Should be fair or good quality, got {result['data_quality']}"
    
    # Test poor quality (7 days, many gaps)
    poor_activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(0, 7, 1)  # Every day for 7 days
    ]
    
    result = engine.detect_data_availability(poor_activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    assert result['data_quality'] in ['poor', 'fair'], f"Should be poor or fair quality, got {result['data_quality']}"
    
    logger.info("✅ Data quality assessment test passed")
    return True

def test_optimal_chronic_period_detection():
    """Test optimal chronic period detection"""
    logger.info("Testing optimal chronic period detection...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create 21 days of data (should recommend 21-day period)
    activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(21)
    ]
    
    result = engine.get_optimal_chronic_period(activities, reference_date, preferred_period=28, max_period=90)
    
    assert result['optimal_period'] > 0, "Should find optimal period"
    assert result['recommendation'] == 'optimal_found', "Should find optimal recommendation"
    assert 'available_periods' in result, "Should include available periods"
    assert 'optimal_period_info' in result, "Should include optimal period info"
    
    # Verify optimal period is reasonable
    optimal_period = result['optimal_period']
    assert 7 <= optimal_period <= 21, f"Optimal period should be between 7 and 21, got {optimal_period}"
    
    # Verify available periods
    available_periods = result['available_periods']
    assert len(available_periods) > 0, "Should have available periods"
    
    # Check that all available periods have sufficient data
    for period_info in available_periods:
        assert period_info['days_available'] >= 7, "All periods should have at least 7 days"
        assert period_info['coverage_percentage'] > 0, "All periods should have coverage"
        assert period_info['data_quality'] in ['excellent', 'good', 'fair', 'poor'], "Should have valid quality"
    
    logger.info(f"✅ Optimal period: {result['optimal_period']} days")
    logger.info(f"✅ Available periods: {len(available_periods)}")
    logger.info("✅ Optimal chronic period detection test passed")
    return True

def test_optimal_chronic_period_no_data():
    """Test optimal chronic period detection with no data"""
    logger.info("Testing optimal chronic period detection with no data...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    result = engine.get_optimal_chronic_period([], reference_date, preferred_period=28, max_period=90)
    
    assert result['optimal_period'] == 0, "Should have 0 optimal period with no data"
    assert result['recommendation'] == 'no_data', "Should identify no data recommendation"
    assert result['available_periods'] == [], "Should have no available periods"
    assert 'No activity data available' in result['message'], "Should mention no data"
    
    logger.info("✅ Optimal chronic period no data test passed")
    return True

def test_optimal_chronic_period_insufficient_data():
    """Test optimal chronic period detection with insufficient data"""
    logger.info("Testing optimal chronic period detection with insufficient data...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create only 3 days of data (less than minimum 7)
    activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(3)
    ]
    
    result = engine.get_optimal_chronic_period(activities, reference_date, preferred_period=28, max_period=90)
    
    assert result['optimal_period'] == 0, "Should have 0 optimal period with insufficient data"
    assert result['recommendation'] == 'insufficient_data', "Should identify insufficient data recommendation"
    assert result['available_periods'] == [], "Should have no available periods"
    assert 'No chronic period has sufficient data' in result['message'], "Should mention insufficient data"
    
    logger.info("✅ Optimal chronic period insufficient data test passed")
    return True

def test_chronic_period_filtering():
    """Test chronic period filtering"""
    logger.info("Testing chronic period filtering...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create activities spanning 60 days
    activities = [
        ActivityData(date=reference_date - timedelta(days=i), total_load_miles=10.0, trimp=8.0)
        for i in range(60)
    ]
    
    # Test 28-day chronic period
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert result['available'], "Should be available with 28-day period"
    assert result['days_available'] == 28, "Should have 28 days available"
    assert result['coverage_percentage'] == 100.0, "Should have 100% coverage"
    
    # Test 14-day chronic period
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=14, minimum_required_days=7)
    
    assert result['available'], "Should be available with 14-day period"
    assert result['days_available'] == 14, "Should have 14 days available"
    assert result['coverage_percentage'] == 100.0, "Should have 100% coverage"
    
    # Test 7-day chronic period
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=7, minimum_required_days=7)
    
    assert result['available'], "Should be available with 7-day period"
    assert result['days_available'] == 7, "Should have 7 days available"
    assert result['coverage_percentage'] == 100.0, "Should have 100% coverage"
    
    logger.info("✅ Chronic period filtering test passed")
    return True

def test_data_availability_edge_cases():
    """Test data availability edge cases"""
    logger.info("Testing data availability edge cases...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test with future dates (should be filtered out)
    activities = [
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date + timedelta(days=1), total_load_miles=12.0, trimp=10.0),  # Future date
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=8.0, trimp=6.0),
    ]
    
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert not result['available'], "Should not be available with insufficient data after filtering"
    assert result['days_available'] == 2, "Should have 2 days available (future date filtered out)"
    
    # Test with duplicate dates (should count as one day)
    activities = [
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=reference_date - timedelta(days=1), total_load_miles=12.0, trimp=10.0),  # Same date
        ActivityData(date=reference_date - timedelta(days=2), total_load_miles=8.0, trimp=6.0),
    ]
    
    result = engine.detect_data_availability(activities, reference_date, chronic_period_days=28, minimum_required_days=7)
    
    assert not result['available'], "Should not be available with insufficient unique days"
    assert result['days_available'] == 2, "Should have 2 unique days available"
    
    logger.info("✅ Data availability edge cases test passed")
    return True

def run_all_tests():
    """Run all data availability detection tests"""
    logger.info("=" * 60)
    logger.info("Data Availability Detection Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("No Data Availability", test_no_data_availability),
        ("Insufficient Data Availability", test_insufficient_data_availability),
        ("Sufficient Data Availability", test_sufficient_data_availability),
        ("Data Gap Analysis", test_data_gap_analysis),
        ("Data Quality Assessment", test_data_quality_assessment),
        ("Optimal Chronic Period Detection", test_optimal_chronic_period_detection),
        ("Optimal Chronic Period No Data", test_optimal_chronic_period_no_data),
        ("Optimal Chronic Period Insufficient Data", test_optimal_chronic_period_insufficient_data),
        ("Chronic Period Filtering", test_chronic_period_filtering),
        ("Data Availability Edge Cases", test_data_availability_edge_cases)
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
        logger.info("🎉 All tests passed! Data availability detection is working correctly.")
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
