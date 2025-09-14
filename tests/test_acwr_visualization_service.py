#!/usr/bin/env python3
"""
Test script for ACWR Visualization Service
Tests the comprehensive visualization data generation functionality
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock
import numpy as np

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_visualization_service import ACWRVisualizationService, ParameterCombination, VisualizationDataPoint, TimeSeriesPoint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_visualization_service_initialization():
    """Test that visualization service initializes correctly"""
    logger.info("Testing visualization service initialization...")
    
    try:
        service = ACWRVisualizationService()
        
        # Check that service has required attributes
        if hasattr(service, 'config_service'):
            logger.info("✅ Config service initialized")
        else:
            logger.error("❌ Config service not initialized")
            return False
        
        if hasattr(service, 'calc_service'):
            logger.info("✅ Calculation service initialized")
        else:
            logger.error("❌ Calculation service not initialized")
            return False
        
        if hasattr(service, 'default_chronic_periods'):
            logger.info("✅ Default chronic periods defined")
        else:
            logger.error("❌ Default chronic periods not defined")
            return False
        
        if hasattr(service, 'default_decay_rates'):
            logger.info("✅ Default decay rates defined")
        else:
            logger.error("❌ Default decay rates not defined")
            return False
        
        if hasattr(service, 'risk_zones'):
            logger.info("✅ Risk zones defined")
        else:
            logger.error("❌ Risk zones not defined")
            return False
        
        logger.info("✅ Visualization service initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visualization service initialization failed: {str(e)}")
        return False

def test_parameter_matrix_generation():
    """Test parameter matrix generation"""
    logger.info("Testing parameter matrix generation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Test with default parameters
        combinations = service.generate_parameter_matrix()
        
        if combinations:
            logger.info(f"✅ Generated {len(combinations)} parameter combinations")
        else:
            logger.error("❌ No parameter combinations generated")
            return False
        
        # Test with custom parameters
        custom_combinations = service.generate_parameter_matrix(
            chronic_periods=[28, 42, 56],
            decay_rates=[0.05, 0.10]
        )
        
        if len(custom_combinations) == 6:  # 3 * 2 = 6 combinations
            logger.info("✅ Custom parameter combinations generated correctly")
        else:
            logger.error(f"❌ Expected 6 combinations, got {len(custom_combinations)}")
            return False
        
        # Test parameter combination structure
        if isinstance(custom_combinations[0], ParameterCombination):
            logger.info("✅ Parameter combinations have correct structure")
        else:
            logger.error("❌ Parameter combinations have incorrect structure")
            return False
        
        logger.info("✅ Parameter matrix generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Parameter matrix generation test failed: {str(e)}")
        return False

def test_chronic_load_surface_calculation():
    """Test chronic load surface calculation"""
    logger.info("Testing chronic load surface calculation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Create test parameter combinations
        combinations = [
            ParameterCombination(chronic_period_days=28, decay_rate=0.05),
            ParameterCombination(chronic_period_days=42, decay_rate=0.10)
        ]
        
        # Mock the calculation service
        with patch.object(service.calc_service, 'calculate_acwr_for_user') as mock_calc:
            mock_calc.return_value = {
                'chronic_load': 100.0,
                'acute_load': 80.0,
                'acwr_ratio': 0.8,
                'risk_level': 'low',
                'data_quality': 'good'
            }
            
            # Test chronic load surface calculation
            data_points = service.calculate_chronic_load_surface(1, combinations)
            
            if data_points:
                logger.info(f"✅ Generated {len(data_points)} data points")
            else:
                logger.error("❌ No data points generated")
                return False
            
            # Test data point structure
            if isinstance(data_points[0], VisualizationDataPoint):
                logger.info("✅ Data points have correct structure")
            else:
                logger.error("❌ Data points have incorrect structure")
                return False
            
            # Test data point content
            dp = data_points[0]
            if hasattr(dp, 'x') and hasattr(dp, 'y') and hasattr(dp, 'z'):
                logger.info("✅ Data points have required coordinates")
            else:
                logger.error("❌ Data points missing required coordinates")
                return False
        
        logger.info("✅ Chronic load surface calculation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Chronic load surface calculation test failed: {str(e)}")
        return False

def test_heatmap_data_generation():
    """Test heatmap data generation"""
    logger.info("Testing heatmap data generation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Create test parameter combinations
        combinations = [
            ParameterCombination(chronic_period_days=28, decay_rate=0.05),
            ParameterCombination(chronic_period_days=42, decay_rate=0.05),
            ParameterCombination(chronic_period_days=28, decay_rate=0.10),
            ParameterCombination(chronic_period_days=42, decay_rate=0.10)
        ]
        
        # Mock the calculation service
        with patch.object(service.calc_service, 'calculate_acwr_for_user') as mock_calc:
            mock_calc.return_value = {
                'chronic_load': 100.0,
                'acute_load': 80.0,
                'acwr_ratio': 0.8,
                'risk_level': 'low',
                'data_quality': 'good'
            }
            
            # Test heatmap data generation
            heatmap_data = service.generate_heatmap_data(1, combinations)
            
            if 'error' in heatmap_data:
                logger.error(f"❌ Heatmap generation failed: {heatmap_data['error']}")
                return False
            
            # Test heatmap structure
            required_keys = ['matrix', 'x_labels', 'y_labels', 'color_scale', 'data_points']
            for key in required_keys:
                if key in heatmap_data:
                    logger.info(f"✅ Heatmap data contains {key}")
                else:
                    logger.error(f"❌ Heatmap data missing {key}")
                    return False
            
            # Test matrix dimensions
            matrix = heatmap_data['matrix']
            x_labels = heatmap_data['x_labels']
            y_labels = heatmap_data['y_labels']
            
            if len(matrix) == len(y_labels) and len(matrix[0]) == len(x_labels):
                logger.info("✅ Heatmap matrix dimensions are correct")
            else:
                logger.error("❌ Heatmap matrix dimensions are incorrect")
                return False
        
        logger.info("✅ Heatmap data generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Heatmap data generation test failed: {str(e)}")
        return False

def test_time_series_data_generation():
    """Test time series data generation"""
    logger.info("Testing time series data generation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Mock the configuration service
        with patch.object(service.config_service, 'get_configuration_by_id') as mock_config:
            mock_config.return_value = {
                'id': 1,
                'name': 'Test Config',
                'chronic_period_days': 42,
                'decay_rate': 0.05
            }
            
            # Mock the calculation service
            with patch.object(service.calc_service, 'calculate_acwr_for_user') as mock_calc:
                mock_calc.return_value = {
                    'chronic_load': 100.0,
                    'acute_load': 80.0,
                    'acwr_ratio': 0.8,
                    'risk_level': 'low',
                    'data_quality': 'good'
                }
                
                # Mock database query
                with patch('db_utils.execute_query') as mock_db:
                    mock_db.return_value = [
                        {'start_date': '2024-01-01', 'trimp_score': 100, 'duration_seconds': 3600}
                    ]
                    
                    # Test time series data generation
                    time_series_data = service.generate_time_series_data(1, 1, 7)
                    
                    if time_series_data:
                        logger.info(f"✅ Generated {len(time_series_data)} time series points")
                    else:
                        logger.error("❌ No time series data generated")
                        return False
                    
                    # Test time series point structure
                    if isinstance(time_series_data[0], TimeSeriesPoint):
                        logger.info("✅ Time series points have correct structure")
                    else:
                        logger.error("❌ Time series points have incorrect structure")
                        return False
        
        logger.info("✅ Time series data generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Time series data generation test failed: {str(e)}")
        return False

def test_acwr_ratio_visualization():
    """Test ACWR ratio visualization generation"""
    logger.info("Testing ACWR ratio visualization generation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Mock the time series generation
        with patch.object(service, 'generate_time_series_data') as mock_time_series:
            from datetime import datetime
            mock_time_series.return_value = [
                TimeSeriesPoint(
                    date=datetime(2024, 1, 1),
                    value=0.8,
                    metadata={'risk_level': 'low'}
                ),
                TimeSeriesPoint(
                    date=datetime(2024, 1, 2),
                    value=1.2,
                    metadata={'risk_level': 'moderate'}
                ),
                TimeSeriesPoint(
                    date=datetime(2024, 1, 3),
                    value=1.6,
                    metadata={'risk_level': 'very_high'}
                )
            ]
            
            # Test ACWR ratio visualization
            viz_data = service.generate_acwr_ratio_visualization(1, 1, 7)
            
            if 'error' in viz_data:
                logger.error(f"❌ ACWR ratio visualization failed: {viz_data['error']}")
                return False
            
            # Test visualization structure
            required_keys = ['time_series', 'risk_zones', 'risk_summary', 'statistics', 'risk_zone_thresholds']
            for key in required_keys:
                if key in viz_data:
                    logger.info(f"✅ Visualization data contains {key}")
                else:
                    logger.error(f"❌ Visualization data missing {key}")
                    return False
            
            # Test risk zone categorization
            risk_zones = viz_data['risk_zones']
            if 'low' in risk_zones and 'moderate' in risk_zones and 'high' in risk_zones and 'very_high' in risk_zones:
                logger.info("✅ Risk zones are properly categorized")
            else:
                logger.error("❌ Risk zones are not properly categorized")
                return False
        
        logger.info("✅ ACWR ratio visualization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ ACWR ratio visualization test failed: {str(e)}")
        return False

def test_sensitivity_analysis():
    """Test sensitivity analysis functionality"""
    logger.info("Testing sensitivity analysis...")
    
    try:
        service = ACWRVisualizationService()
        
        # Mock the calculation service
        with patch.object(service.calc_service, 'calculate_acwr_for_user') as mock_calc:
            mock_calc.return_value = {
                'chronic_load': 100.0,
                'acute_load': 80.0,
                'acwr_ratio': 0.8,
                'risk_level': 'low',
                'data_quality': 'good'
            }
            
            # Test sensitivity analysis
            analysis_result = service.perform_sensitivity_analysis(1, 42, 0.05)
            
            if 'error' in analysis_result:
                logger.error(f"❌ Sensitivity analysis failed: {analysis_result['error']}")
                return False
            
            # Test analysis structure
            required_keys = ['base_parameters', 'base_result', 'sensitivity_results', 'sensitivity_metrics']
            for key in required_keys:
                if key in analysis_result:
                    logger.info(f"✅ Analysis result contains {key}")
                else:
                    logger.error(f"❌ Analysis result missing {key}")
                    return False
            
            # Test sensitivity results
            sensitivity_results = analysis_result['sensitivity_results']
            if sensitivity_results:
                logger.info(f"✅ Generated {len(sensitivity_results)} sensitivity results")
            else:
                logger.error("❌ No sensitivity results generated")
                return False
        
        logger.info("✅ Sensitivity analysis test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sensitivity analysis test failed: {str(e)}")
        return False

def test_data_quality_indicators():
    """Test data quality indicators generation"""
    logger.info("Testing data quality indicators generation...")
    
    try:
        service = ACWRVisualizationService()
        
        # Mock the configuration service
        with patch.object(service.config_service, 'get_configuration_by_id') as mock_config:
            mock_config.return_value = {
                'id': 1,
                'name': 'Test Config',
                'chronic_period_days': 42,
                'decay_rate': 0.05
            }
            
            # Mock database query
            with patch('db_utils.execute_query') as mock_db:
                mock_db.return_value = [
                    {
                        'start_date': '2024-01-01',
                        'trimp_score': 100,
                        'duration_seconds': 3600,
                        'distance_meters': 5000,
                        'average_heart_rate': 150,
                        'max_heart_rate': 180
                    }
                ]
                
                # Test data quality indicators
                quality_indicators = service.generate_data_quality_indicators(1, 1, 7)
                
                if 'error' in quality_indicators:
                    logger.error(f"❌ Data quality indicators failed: {quality_indicators['error']}")
                    return False
                
                # Test quality indicators structure
                required_keys = ['data_completeness', 'data_consistency', 'temporal_distribution', 'confidence_score']
                for key in required_keys:
                    if key in quality_indicators:
                        logger.info(f"✅ Quality indicators contain {key}")
                    else:
                        logger.error(f"❌ Quality indicators missing {key}")
                        return False
                
                # Test confidence score
                confidence_score = quality_indicators['confidence_score']
                if 0 <= confidence_score <= 100:
                    logger.info(f"✅ Confidence score is valid: {confidence_score}")
                else:
                    logger.error(f"❌ Confidence score is invalid: {confidence_score}")
                    return False
        
        logger.info("✅ Data quality indicators test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data quality indicators test failed: {str(e)}")
        return False

def test_helper_methods():
    """Test helper methods"""
    logger.info("Testing helper methods...")
    
    try:
        service = ACWRVisualizationService()
        
        # Test risk zone calculation
        risk_zones = ['low', 'moderate', 'high', 'very_high']
        test_values = [0.5, 1.0, 1.4, 2.0]
        
        for value in test_values:
            risk_zone = service._get_risk_zone(value)
            if risk_zone in risk_zones:
                logger.info(f"✅ Risk zone for {value}: {risk_zone}")
            else:
                logger.error(f"❌ Invalid risk zone for {value}: {risk_zone}")
                return False
        
        # Test data consistency calculation
        test_values = [100, 110, 90, 105, 95]
        consistency = service._calculate_data_consistency(test_values)
        
        if 'coefficient_of_variation' in consistency:
            logger.info("✅ Data consistency calculation works")
        else:
            logger.error("❌ Data consistency calculation failed")
            return False
        
        # Test confidence score calculation
        confidence_score = service._calculate_confidence_score(80, 70, {'coefficient_of_variation': 20}, {'coefficient_of_variation': 15})
        
        if 0 <= confidence_score <= 100:
            logger.info(f"✅ Confidence score calculation works: {confidence_score}")
        else:
            logger.error(f"❌ Confidence score calculation failed: {confidence_score}")
            return False
        
        logger.info("✅ Helper methods test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Helper methods test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all visualization service tests"""
    logger.info("=" * 60)
    logger.info("ACWR Visualization Service Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Service Initialization", test_visualization_service_initialization),
        ("Parameter Matrix Generation", test_parameter_matrix_generation),
        ("Chronic Load Surface Calculation", test_chronic_load_surface_calculation),
        ("Heatmap Data Generation", test_heatmap_data_generation),
        ("Time Series Data Generation", test_time_series_data_generation),
        ("ACWR Ratio Visualization", test_acwr_ratio_visualization),
        ("Sensitivity Analysis", test_sensitivity_analysis),
        ("Data Quality Indicators", test_data_quality_indicators),
        ("Helper Methods", test_helper_methods)
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
        logger.info("🎉 All tests passed! ACWR visualization service is working correctly.")
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
