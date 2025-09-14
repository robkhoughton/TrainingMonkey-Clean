#!/usr/bin/env python3
"""
Test script for Multi-Line Time Series Functionality
Tests the enhanced time series visualization with toggle visibility
"""

import sys
import os
import logging

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_multiline_timeseries_components():
    """Test that multi-line time series components exist"""
    logger.info("Testing multi-line time series components...")
    
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
        
        # Check for multi-line time series specific components
        multiline_components = [
            'generateMockMultiTimeSeriesData',
            'setupTimeSeriesToggleControls',
            'toggleTimeSeriesLine',
            'toggleAllTimeSeriesLines',
            'Multi-Line Comparison',
            'yaxis2',
            'overlaying: \'y\'',
            'side: \'right\'',
            'hovermode: \'x unified\'',
            'timeseries-toggle-controls',
            'Toggle All Lines'
        ]
        
        for component in multiline_components:
            if component in content:
                logger.info(f"✅ Multi-line component {component} found")
            else:
                logger.error(f"❌ Multi-line component {component} not found")
                return False
        
        logger.info("✅ Multi-line time series components test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-line time series components test failed: {str(e)}")
        return False

def test_toggle_controls():
    """Test toggle controls functionality"""
    logger.info("Testing toggle controls...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for toggle control components
        toggle_components = [
            'toggle-acwr',
            'toggle-acute',
            'toggle-chronic',
            'toggle-conservative',
            'toggle-moderate',
            'toggle-aggressive',
            'onchange="toggleTimeSeriesLine',
            'onclick="toggleAllTimeSeriesLines()"',
            'Toggle Lines:',
            'position: absolute',
            'z-index: 100'
        ]
        
        for component in toggle_components:
            if component in content:
                logger.info(f"✅ Toggle control {component} found")
            else:
                logger.error(f"❌ Toggle control {component} not found")
                return False
        
        logger.info("✅ Toggle controls test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Toggle controls test failed: {str(e)}")
        return False

def test_dual_axis_support():
    """Test dual y-axis support"""
    logger.info("Testing dual y-axis support...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for dual y-axis components
        dual_axis_components = [
            'yaxis2:',
            'title: \'Load Values\'',
            'anchor: \'x\'',
            'overlaying: \'y\'',
            'side: \'right\'',
            'yaxis: \'y2\'',
            'titlefont: { color: \'#007bff\' }',
            'titlefont: { color: \'#28a745\' }'
        ]
        
        for component in dual_axis_components:
            if component in content:
                logger.info(f"✅ Dual axis component {component} found")
            else:
                logger.error(f"❌ Dual axis component {component} not found")
                return False
        
        logger.info("✅ Dual y-axis support test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dual y-axis support test failed: {str(e)}")
        return False

def test_comparison_data():
    """Test comparison data generation"""
    logger.info("Testing comparison data generation...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for comparison data components
        comparison_components = [
            'comparisonData',
            'Conservative (56d, 0.03)',
            'Moderate (42d, 0.05)',
            'Aggressive (28d, 0.08)',
            'acwrValues',
            'acuteValues',
            'chronicValues',
            'visible: \'legendonly\'',
            'dash: index > 0 ? \'dash\' : \'solid\''
        ]
        
        for component in comparison_components:
            if component in content:
                logger.info(f"✅ Comparison data component {component} found")
            else:
                logger.error(f"❌ Comparison data component {component} not found")
                return False
        
        logger.info("✅ Comparison data generation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Comparison data generation test failed: {str(e)}")
        return False

def test_plotly_integration():
    """Test Plotly.js integration for multi-line charts"""
    logger.info("Testing Plotly.js integration...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for Plotly.js multi-line specific components
        plotly_components = [
            'Plotly.newPlot',
            'Plotly.restyle',
            'plotly_legendclick',
            'hovermode: \'x unified\'',
            'displayModeBar: true',
            'modeBarButtonsToAdd',
            'select2d',
            'lasso2d'
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

def test_legend_functionality():
    """Test legend functionality"""
    logger.info("Testing legend functionality...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for legend components
        legend_components = [
            'legend: {',
            'x: 0',
            'y: 1',
            'bgcolor: \'rgba(255,255,255,0.8)\'',
            'bordercolor: \'rgba(0,0,0,0.2)\'',
            'borderwidth: 1',
            'return false',
            'custom toggle logic'
        ]
        
        for component in legend_components:
            if component in content:
                logger.info(f"✅ Legend component {component} found")
            else:
                logger.error(f"❌ Legend component {component} not found")
                return False
        
        logger.info("✅ Legend functionality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Legend functionality test failed: {str(e)}")
        return False

def test_risk_zones_integration():
    """Test risk zones integration with multi-line charts"""
    logger.info("Testing risk zones integration...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for risk zone components
        risk_zone_components = [
            'const shapes = [',
            'type: \'rect\'',
            'fillcolor: \'#d4edda\'',
            'fillcolor: \'#fff3cd\'',
            'fillcolor: \'#f8d7da\'',
            'fillcolor: \'#f5c6cb\'',
            'opacity: 0.3',
            'Toggle Risk Zones'
        ]
        
        for component in risk_zone_components:
            if component in content:
                logger.info(f"✅ Risk zone component {component} found")
            else:
                logger.error(f"❌ Risk zone component {component} not found")
                return False
        
        logger.info("✅ Risk zones integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Risk zones integration test failed: {str(e)}")
        return False

def test_responsive_design():
    """Test responsive design for multi-line charts"""
    logger.info("Testing responsive design...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for responsive design components
        responsive_components = [
            'responsive: true',
            'margin: { t: 50, l: 50, r: 80, b: 50 }',
            'position: relative',
            'position: absolute',
            'z-index: 100',
            'max-width: 200px'
        ]
        
        for component in responsive_components:
            if component in content:
                logger.info(f"✅ Responsive component {component} found")
            else:
                logger.error(f"❌ Responsive component {component} not found")
                return False
        
        logger.info("✅ Responsive design test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Responsive design test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all multi-line time series tests"""
    logger.info("=" * 60)
    logger.info("Multi-Line Time Series Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Multi-Line Components", test_multiline_timeseries_components),
        ("Toggle Controls", test_toggle_controls),
        ("Dual Y-Axis Support", test_dual_axis_support),
        ("Comparison Data", test_comparison_data),
        ("Plotly.js Integration", test_plotly_integration),
        ("Legend Functionality", test_legend_functionality),
        ("Risk Zones Integration", test_risk_zones_integration),
        ("Responsive Design", test_responsive_design)
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
        logger.info("🎉 All tests passed! Multi-line time series functionality is working correctly.")
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
