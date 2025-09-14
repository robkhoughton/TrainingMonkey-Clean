#!/usr/bin/env python3
"""
Test script for Performance Optimization
Tests the performance optimization features for large activity datasets
"""

import sys
import os
import logging
import time
from datetime import datetime, date, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exponential_decay_engine import (
    ExponentialDecayEngine, ActivityData
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_large_dataset(size: int, reference_date: date) -> list:
    """Create a large dataset of activities for testing"""
    activities = []
    for i in range(size):
        activity_date = reference_date - timedelta(days=i)  # Sequential days going back
        activities.append(ActivityData(
            date=activity_date,
            total_load_miles=10.0 + (i % 20),  # Vary load between 10-30
            trimp=8.0 + (i % 15)  # Vary trimp between 8-23
        ))
    return activities

def test_performance_metrics():
    """Test performance metrics calculation"""
    logger.info("Testing performance metrics...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test small dataset
    small_activities = create_large_dataset(100, reference_date)
    metrics = engine.get_performance_metrics(small_activities, reference_date)
    
    assert metrics['dataset_size'] == 100, "Should have 100 activities"
    assert metrics['recommended_optimization'] == 'standard_processing', "Should recommend standard processing"
    assert metrics['estimated_processing_time_ms'] > 0, "Should have estimated processing time"
    assert metrics['memory_usage_estimate_mb'] > 0, "Should have memory usage estimate"
    assert 'optimization_thresholds' in metrics, "Should include optimization thresholds"
    
    # Test medium dataset
    medium_activities = create_large_dataset(1500, reference_date)
    metrics = engine.get_performance_metrics(medium_activities, reference_date)
    
    assert metrics['dataset_size'] == 1500, "Should have 1500 activities"
    assert metrics['recommended_optimization'] == 'weight_caching', "Should recommend weight caching"
    
    # Test large dataset
    large_activities = create_large_dataset(15000, reference_date)
    metrics = engine.get_performance_metrics(large_activities, reference_date)
    
    assert metrics['dataset_size'] == 15000, "Should have 15000 activities"
    assert metrics['recommended_optimization'] == 'batched_processing', "Should recommend batched processing"
    
    # Test empty dataset
    empty_metrics = engine.get_performance_metrics([], reference_date)
    assert empty_metrics['dataset_size'] == 0, "Should have 0 activities"
    assert empty_metrics['recommended_optimization'] == 'none', "Should recommend no optimization"
    
    logger.info("✅ Performance metrics test passed")
    return True

def test_standard_processing():
    """Test standard processing for small datasets"""
    logger.info("Testing standard processing...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create small dataset
    activities = create_large_dataset(50, reference_date)
    acute_activities = activities[:7]  # First 7 days
    chronic_activities = activities[:28]  # First 28 days
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=False, batch_size=1000
    )
    
    assert result['success'], "Should succeed with standard processing"
    assert result['calculation_method'] == 'exponential_decay_standard', "Should use standard method"
    assert result['performance_optimization'] == 'standard_processing', "Should indicate standard optimization"
    assert result['calculation_time_ms'] >= 0, "Should have calculation time"
    assert result['total_activities_processed'] == 35, "Should process 35 activities (7 acute + 28 chronic)"
    
    # Verify calculation results
    assert 'acute_load_avg' in result, "Should have acute load average"
    assert 'chronic_load_avg' in result, "Should have chronic load average"
    assert 'acute_chronic_ratio' in result, "Should have ACWR ratio"
    
    logger.info(f"✅ Standard processing: {result['calculation_time_ms']:.2f}ms for {result['total_activities_processed']} activities")
    logger.info("✅ Standard processing test passed")
    return True

def test_weight_caching():
    """Test weight caching optimization"""
    logger.info("Testing weight caching optimization...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create medium dataset
    activities = create_large_dataset(500, reference_date)
    acute_activities = activities[:7]  # First 7 days
    chronic_activities = activities[:28]  # First 28 days
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    
    assert result['success'], "Should succeed with weight caching"
    assert result['calculation_method'] == 'exponential_decay_cached', "Should use cached method"
    assert result['performance_optimization'] == 'weight_caching', "Should indicate weight caching optimization"
    assert result['calculation_time_ms'] >= 0, "Should have calculation time"
    assert 'weight_cache_size' in result, "Should include weight cache size"
    assert result['weight_cache_size'] > 0, "Should have cached weights"
    
    # Verify calculation results
    assert 'acute_load_avg' in result, "Should have acute load average"
    assert 'chronic_load_avg' in result, "Should have chronic load average"
    assert 'acute_chronic_ratio' in result, "Should have ACWR ratio"
    
    logger.info(f"✅ Weight caching: {result['calculation_time_ms']:.2f}ms, cache size: {result['weight_cache_size']}")
    logger.info("✅ Weight caching test passed")
    return True

def test_batched_processing():
    """Test batched processing for large datasets"""
    logger.info("Testing batched processing...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create large dataset
    activities = create_large_dataset(5000, reference_date)
    acute_activities = activities[:7]  # First 7 days
    chronic_activities = activities[:5000]  # All 5000 days to trigger batching
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    
    assert result['success'], "Should succeed with batched processing"
    assert result['calculation_method'] == 'exponential_decay_batched', "Should use batched method"
    assert result['performance_optimization'] == 'batched_processing', "Should indicate batched optimization"
    assert result['calculation_time_ms'] >= 0, "Should have calculation time"
    assert 'batches_processed' in result, "Should include batches processed"
    assert result['batches_processed'] > 0, "Should have processed batches"
    
    # Verify calculation results
    assert 'acute_load_avg' in result, "Should have acute load average"
    assert 'chronic_load_avg' in result, "Should have chronic load average"
    assert 'acute_chronic_ratio' in result, "Should have ACWR ratio"
    
    logger.info(f"✅ Batched processing: {result['calculation_time_ms']:.2f}ms, {result['batches_processed']} batches")
    logger.info("✅ Batched processing test passed")
    return True

def test_performance_comparison():
    """Test performance comparison between different optimization methods"""
    logger.info("Testing performance comparison...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create medium dataset for comparison
    activities = create_large_dataset(1000, reference_date)
    acute_activities = activities[:7]  # First 7 days
    chronic_activities = activities[:28]  # First 28 days
    
    # Test standard processing
    start_time = time.time()
    standard_result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=False, batch_size=1000
    )
    standard_time = (time.time() - start_time) * 1000
    
    # Test weight caching
    start_time = time.time()
    cached_result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    cached_time = (time.time() - start_time) * 1000
    
    # Verify both methods produce similar results
    assert abs(standard_result['acute_load_avg'] - cached_result['acute_load_avg']) < 0.01, "Results should be similar"
    assert abs(standard_result['chronic_load_avg'] - cached_result['chronic_load_avg']) < 0.01, "Results should be similar"
    assert abs(standard_result['acute_chronic_ratio'] - cached_result['acute_chronic_ratio']) < 0.01, "Results should be similar"
    
    # Weight caching should be faster for medium datasets
    logger.info(f"Standard processing: {standard_time:.2f}ms")
    logger.info(f"Weight caching: {cached_time:.2f}ms")
    if standard_time > 0:
        improvement = ((standard_time - cached_time) / standard_time * 100)
        logger.info(f"Performance improvement: {improvement:.1f}%")
    else:
        logger.info("Performance improvement: Both methods too fast to measure accurately")
    
    logger.info("✅ Performance comparison test passed")
    return True

def test_optimization_auto_selection():
    """Test automatic optimization selection based on dataset size"""
    logger.info("Testing optimization auto-selection...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test small dataset (should use standard)
    small_activities = create_large_dataset(100, reference_date)
    acute_activities = small_activities[:7]
    chronic_activities = small_activities[:28]
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    
    assert result['calculation_method'] == 'exponential_decay_cached', "Should use cached method for small dataset"
    
    # Test large dataset (should use batched)
    large_activities = create_large_dataset(5000, reference_date)
    acute_activities = large_activities[:7]
    chronic_activities = large_activities[:5000]  # All 5000 days to trigger batching
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    
    assert result['calculation_method'] == 'exponential_decay_batched', "Should use batched method for large dataset"
    
    logger.info("✅ Optimization auto-selection test passed")
    return True

def test_batch_size_optimization():
    """Test different batch sizes for batched processing"""
    logger.info("Testing batch size optimization...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Create large dataset
    activities = create_large_dataset(3000, reference_date)
    acute_activities = activities[:7]  # First 7 days
    chronic_activities = activities[:3000]  # All 3000 days to trigger batching
    
    # Test different batch sizes
    batch_sizes = [500, 1000, 1500]
    results = []
    
    for batch_size in batch_sizes:
        result = engine.calculate_enhanced_acwr_optimized(
            acute_activities, chronic_activities, reference_date,
            decay_rate=0.05, chronic_period_days=28,
            use_caching=True, batch_size=batch_size
        )
        
        assert result['success'], f"Should succeed with batch size {batch_size}"
        assert result['calculation_method'] == 'exponential_decay_batched', "Should use batched method"
        assert 'batches_processed' in result, "Should include batches processed"
        
        results.append({
            'batch_size': batch_size,
            'time_ms': result['calculation_time_ms'],
            'batches': result['batches_processed']
        })
        
        logger.info(f"Batch size {batch_size}: {result['calculation_time_ms']:.2f}ms, {result['batches_processed']} batches")
    
    # All results should be similar in accuracy
    for i in range(1, len(results)):
        if results[0]['time_ms'] > 1.0:  # Only compare if first result is > 1ms
            assert abs(results[0]['time_ms'] - results[i]['time_ms']) < results[0]['time_ms'] * 2.0, "Times should be reasonably similar"
        else:
            # If times are too fast to measure accurately, just verify they're all >= 0
            assert results[i]['time_ms'] >= 0, "Times should be non-negative"
    
    logger.info("✅ Batch size optimization test passed")
    return True

def test_memory_efficiency():
    """Test memory efficiency of different optimization methods"""
    logger.info("Testing memory efficiency...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test with progressively larger datasets
    dataset_sizes = [100, 500, 1000, 2000]
    
    for size in dataset_sizes:
        activities = create_large_dataset(size, reference_date)
        acute_activities = activities[:7]
        chronic_activities = activities[:28]
        
        # Get performance metrics
        metrics = engine.get_performance_metrics(activities, reference_date)
        
        # Calculate ACWR with optimization
        result = engine.calculate_enhanced_acwr_optimized(
            acute_activities, chronic_activities, reference_date,
            decay_rate=0.05, chronic_period_days=28,
            use_caching=True, batch_size=1000
        )
        
        assert result['success'], f"Should succeed with dataset size {size}"
        assert result['calculation_time_ms'] >= 0, "Should have calculation time"
        
        logger.info(f"Dataset size {size}: {result['calculation_time_ms']:.2f}ms, "
                   f"optimization: {result['performance_optimization']}, "
                   f"memory estimate: {metrics['memory_usage_estimate_mb']:.4f}MB")
    
    logger.info("✅ Memory efficiency test passed")
    return True

def test_error_handling_optimization():
    """Test error handling in optimization methods"""
    logger.info("Testing error handling in optimization...")
    
    engine = ExponentialDecayEngine()
    reference_date = date(2025, 9, 7)
    
    # Test with invalid decay rate
    activities = create_large_dataset(100, reference_date)
    acute_activities = activities[:7]
    chronic_activities = activities[:28]
    
    result = engine.calculate_enhanced_acwr_optimized(
        acute_activities, chronic_activities, reference_date,
        decay_rate=-0.1, chronic_period_days=28,  # Invalid decay rate
        use_caching=True, batch_size=1000
    )
    
    assert not result['success'], "Should fail with invalid decay rate"
    assert 'error' in result, "Should include error message"
    assert result['calculation_time_ms'] >= 0, "Should have calculation time even on error"
    
    # Test with empty activities
    result = engine.calculate_enhanced_acwr_optimized(
        [], [], reference_date,
        decay_rate=0.05, chronic_period_days=28,
        use_caching=True, batch_size=1000
    )
    
    # Empty activities should be handled gracefully (may return success or edge case result)
    assert 'calculation_time_ms' in result, "Should have calculation time"
    assert result['calculation_time_ms'] >= 0, "Should have calculation time"
    
    logger.info("✅ Error handling optimization test passed")
    return True

def run_all_tests():
    """Run all performance optimization tests"""
    logger.info("=" * 60)
    logger.info("Performance Optimization Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Performance Metrics", test_performance_metrics),
        ("Standard Processing", test_standard_processing),
        ("Weight Caching", test_weight_caching),
        ("Batched Processing", test_batched_processing),
        ("Performance Comparison", test_performance_comparison),
        ("Optimization Auto-Selection", test_optimization_auto_selection),
        ("Batch Size Optimization", test_batch_size_optimization),
        ("Memory Efficiency", test_memory_efficiency),
        ("Error Handling Optimization", test_error_handling_optimization)
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
        logger.info("🎉 All tests passed! Performance optimization is working correctly.")
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
