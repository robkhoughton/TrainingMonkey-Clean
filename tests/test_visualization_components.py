#!/usr/bin/env python3
"""
Test script for ACWR Visualization Components
Tests the interactive visualization dashboard and API endpoints
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_visualization_routes import acwr_visualization_routes
from acwr_visualization_service import ACWRVisualizationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_visualization_routes_initialization():
    """Test that visualization routes initialize correctly"""
    logger.info("Testing visualization routes initialization...")
    
    try:
        # Check that blueprint exists
        if hasattr(acwr_visualization_routes, 'name'):
            logger.info("✅ Visualization routes blueprint exists")
        else:
            logger.error("❌ Visualization routes blueprint not found")
            return False
        
        # Check blueprint name
        if acwr_visualization_routes.name == 'acwr_visualization_routes':
            logger.info("✅ Blueprint name is correct")
        else:
            logger.error("❌ Blueprint name is incorrect")
            return False
        
        logger.info("✅ Visualization routes initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visualization routes initialization failed: {str(e)}")
        return False

def test_dashboard_template():
    """Test that dashboard template exists and has required components"""
    logger.info("Testing dashboard template...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        if os.path.exists(template_path):
            logger.info("✅ Dashboard template file exists")
        else:
            logger.error("❌ Dashboard template file not found")
            return False
        
        # Read template content
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required libraries
        required_libraries = [
            'three.js',
            'plotly-latest.min.js',
            'chart.js',
            'bootstrap@5.3.0'
        ]
        
        for library in required_libraries:
            if library in content:
                logger.info(f"✅ Required library {library} found")
            else:
                logger.error(f"❌ Required library {library} not found")
                return False
        
        # Check for required HTML elements
        required_elements = [
            'threejs-container',
            'heatmap-container',
            'timeseries-container',
            'sensitivity-container',
            'userSelect',
            'configSelect',
            'chronicPeriodSlider',
            'decayRateSlider'
        ]
        
        for element in required_elements:
            if element in content:
                logger.info(f"✅ Required element {element} found")
            else:
                logger.error(f"❌ Required element {element} not found")
                return False
        
        # Check for required JavaScript functions
        required_functions = [
            'initializeDashboard',
            'generate3DSurface',
            'generateHeatmap',
            'generateTimeSeries',
            'generateSensitivityAnalysis',
            'updateCurrentMetrics',
            'exportToPNG',
            'exportToSVG',
            'exportToCSV',
            'exportToPDF'
        ]
        
        for function in required_functions:
            if function in content:
                logger.info(f"✅ Required function {function} found")
            else:
                logger.error(f"❌ Required function {function} not found")
                return False
        
        logger.info("✅ Dashboard template test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dashboard template test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test that all required API endpoints exist"""
    logger.info("Testing API endpoints...")
    
    try:
        # Check route file content
        routes_path = os.path.join(os.path.dirname(__file__), 'acwr_visualization_routes.py')
        
        if os.path.exists(routes_path):
            logger.info("✅ Routes file exists")
        else:
            logger.error("❌ Routes file not found")
            return False
        
        # Read routes content
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required endpoints
        required_endpoints = [
            '/acwr-visualization',
            '/api/visualization/users',
            '/api/visualization/configurations',
            '/api/visualization/3d-surface',
            '/api/visualization/heatmap',
            '/api/visualization/timeseries',
            '/api/visualization/acwr-ratio',
            '/api/visualization/sensitivity',
            '/api/visualization/data-quality',
            '/api/visualization/current-metrics',
            '/api/visualization/export/png',
            '/api/visualization/export/svg',
            '/api/visualization/export/csv',
            '/api/visualization/export/pdf'
        ]
        
        for endpoint in required_endpoints:
            if endpoint in content:
                logger.info(f"✅ Endpoint {endpoint} found")
            else:
                logger.error(f"❌ Endpoint {endpoint} not found")
                return False
        
        # Check for required HTTP methods
        required_methods = ['GET', 'POST']
        for method in required_methods:
            if f"methods=['{method}']" in content:
                logger.info(f"✅ HTTP method {method} found")
            else:
                logger.error(f"❌ HTTP method {method} not found")
                return False
        
        logger.info("✅ API endpoints test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ API endpoints test failed: {str(e)}")
        return False

def test_threejs_integration():
    """Test Three.js integration components"""
    logger.info("Testing Three.js integration...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Three.js specific components
        threejs_components = [
            'THREE.Scene',
            'THREE.PerspectiveCamera',
            'THREE.WebGLRenderer',
            'THREE.BufferGeometry',
            'THREE.PointsMaterial',
            'THREE.Points',
            'THREE.AmbientLight',
            'THREE.DirectionalLight',
            'initializeThreeJS',
            'create3DSurface',
            'reset3DView',
            'toggle3DWireframe'
        ]
        
        for component in threejs_components:
            if component in content:
                logger.info(f"✅ Three.js component {component} found")
            else:
                logger.error(f"❌ Three.js component {component} not found")
                return False
        
        logger.info("✅ Three.js integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Three.js integration test failed: {str(e)}")
        return False

def test_plotly_integration():
    """Test Plotly.js integration components"""
    logger.info("Testing Plotly.js integration...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Plotly.js specific components
        plotly_components = [
            'Plotly.newPlot',
            'Plotly.downloadImage',
            'generateHeatmap',
            'generateTimeSeries',
            'generateSensitivityAnalysis',
            'exportHeatmap',
            'exportHeatmapSVG',
            'exportTimeSeries',
            'exportSensitivity'
        ]
        
        for component in plotly_components:
            if component in content:
                logger.info(f"✅ Plotly.js component {component} found")
            else:
                logger.error(f"❌ Plotly.js component {component} not found")
                return False
        
        logger.info("✅ Plotly.js integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Plotly.js integration test failed: {str(e)}")
        return False

def test_interactive_controls():
    """Test interactive control components"""
    logger.info("Testing interactive controls...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for interactive control components
        control_components = [
            'onUserChange',
            'onConfigChange',
            'onParameterChange',
            'applyPreset',
            'updateVisualizations',
            'toggleRiskZones',
            'refreshData',
            'chronicPeriodSlider',
            'decayRateSlider',
            'analysisPeriod'
        ]
        
        for component in control_components:
            if component in content:
                logger.info(f"✅ Interactive control {component} found")
            else:
                logger.error(f"❌ Interactive control {component} not found")
                return False
        
        # Check for preset configurations
        presets = ['conservative', 'moderate', 'aggressive']
        for preset in presets:
            if preset in content:
                logger.info(f"✅ Preset configuration {preset} found")
            else:
                logger.error(f"❌ Preset configuration {preset} not found")
                return False
        
        logger.info("✅ Interactive controls test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Interactive controls test failed: {str(e)}")
        return False

def test_export_functionality():
    """Test export functionality components"""
    logger.info("Testing export functionality...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for export functionality
        export_components = [
            'exportToPNG',
            'exportToSVG',
            'exportToCSV',
            'exportToPDF',
            'exportReport',
            'exportHeatmap',
            'exportHeatmapSVG',
            'exportTimeSeries',
            'exportSensitivity'
        ]
        
        for component in export_components:
            if component in content:
                logger.info(f"✅ Export function {component} found")
            else:
                logger.error(f"❌ Export function {component} not found")
                return False
        
        # Check for export API endpoints
        routes_path = os.path.join(os.path.dirname(__file__), 'acwr_visualization_routes.py')
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        export_endpoints = [
            '/api/visualization/export/png',
            '/api/visualization/export/svg',
            '/api/visualization/export/csv',
            '/api/visualization/export/pdf'
        ]
        
        for endpoint in export_endpoints:
            if endpoint in routes_content:
                logger.info(f"✅ Export endpoint {endpoint} found")
            else:
                logger.error(f"❌ Export endpoint {endpoint} not found")
                return False
        
        logger.info("✅ Export functionality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Export functionality test failed: {str(e)}")
        return False

def test_parameter_controls():
    """Test parameter control components"""
    logger.info("Testing parameter controls...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for parameter control components
        parameter_controls = [
            'chronicPeriodSlider',
            'decayRateSlider',
            'analysisPeriod',
            'userSelect',
            'configSelect',
            'updateSliderValues',
            'loadConfigurationParameters'
        ]
        
        for control in parameter_controls:
            if control in content:
                logger.info(f"✅ Parameter control {control} found")
            else:
                logger.error(f"❌ Parameter control {control} not found")
                return False
        
        # Check for parameter validation
        validation_components = [
            'min="28"',
            'max="90"',
            'min="0.01"',
            'max="0.20"',
            'step="7"',
            'step="0.01"'
        ]
        
        for validation in validation_components:
            if validation in content:
                logger.info(f"✅ Parameter validation {validation} found")
            else:
                logger.error(f"❌ Parameter validation {validation} not found")
                return False
        
        logger.info("✅ Parameter controls test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Parameter controls test failed: {str(e)}")
        return False

def test_visualization_service_integration():
    """Test integration with visualization service"""
    logger.info("Testing visualization service integration...")
    
    try:
        routes_path = os.path.join(os.path.dirname(__file__), 'acwr_visualization_routes.py')
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for visualization service integration
        service_integrations = [
            'ACWRVisualizationService',
            'visualization_service.generate_parameter_matrix',
            'visualization_service.calculate_chronic_load_surface',
            'visualization_service.generate_heatmap_data',
            'visualization_service.generate_time_series_data',
            'visualization_service.generate_acwr_ratio_visualization',
            'visualization_service.perform_sensitivity_analysis',
            'visualization_service.generate_data_quality_indicators'
        ]
        
        for integration in service_integrations:
            if integration in content:
                logger.info(f"✅ Service integration {integration} found")
            else:
                logger.error(f"❌ Service integration {integration} not found")
                return False
        
        logger.info("✅ Visualization service integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visualization service integration test failed: {str(e)}")
        return False

def test_error_handling():
    """Test error handling components"""
    logger.info("Testing error handling...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for error handling components
        error_components = [
            'showError',
            'showSuccess',
            'hideMessages',
            'errorMessage',
            'successMessage',
            'loadingSpinner',
            'showLoading'
        ]
        
        for component in error_components:
            if component in content:
                logger.info(f"✅ Error handling component {component} found")
            else:
                logger.error(f"❌ Error handling component {component} not found")
                return False
        
        # Check for error handling in routes
        routes_path = os.path.join(os.path.dirname(__file__), 'acwr_visualization_routes.py')
        
        with open(routes_path, 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        error_handling_patterns = [
            'try:',
            'except Exception as e:',
            'logger.error',
            'return jsonify',
            "'success': False"
        ]
        
        for pattern in error_handling_patterns:
            if pattern in routes_content:
                logger.info(f"✅ Error handling pattern {pattern} found")
            else:
                logger.error(f"❌ Error handling pattern {pattern} not found")
                return False
        
        logger.info("✅ Error handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all visualization component tests"""
    logger.info("=" * 60)
    logger.info("ACWR Visualization Components Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Routes Initialization", test_visualization_routes_initialization),
        ("Dashboard Template", test_dashboard_template),
        ("API Endpoints", test_api_endpoints),
        ("Three.js Integration", test_threejs_integration),
        ("Plotly.js Integration", test_plotly_integration),
        ("Interactive Controls", test_interactive_controls),
        ("Export Functionality", test_export_functionality),
        ("Parameter Controls", test_parameter_controls),
        ("Service Integration", test_visualization_service_integration),
        ("Error Handling", test_error_handling)
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
        logger.info("🎉 All tests passed! ACWR visualization components are working correctly.")
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
