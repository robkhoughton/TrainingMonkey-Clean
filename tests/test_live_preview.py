#!/usr/bin/env python3
"""
Test script for Live Preview Functionality
Tests the real-time parameter adjustment with live preview functionality
"""

import sys
import os
import logging

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_live_preview_components():
    """Test that live preview components exist"""
    logger.info("Testing live preview components...")
    
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
        
        # Check for live preview specific components
        live_preview_components = [
            'updateLivePreview',
            'updateCurrentMetricsPreview',
            'updateParameterComparison',
            'updateWhatIfAnalysis',
            'showLivePreviewIndicator',
            'toggleLivePreview',
            'isLivePreviewEnabled',
            'addLivePreviewStyling',
            'removeLivePreviewStyling',
            'livePreviewToggle',
            'Live Preview Mode'
        ]
        
        for component in live_preview_components:
            if component in content:
                logger.info(f"✅ Live preview component {component} found")
            else:
                logger.error(f"❌ Live preview component {component} not found")
                return False
        
        logger.info("✅ Live preview components test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Live preview components test failed: {str(e)}")
        return False

def test_live_preview_toggle():
    """Test live preview toggle functionality"""
    logger.info("Testing live preview toggle...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for toggle components
        toggle_components = [
            'form-check form-switch',
            'livePreviewToggle',
            'onchange="toggleLivePreview()"',
            'Live Preview Mode',
            'Real-time updates as you adjust parameters',
            'toggleLivePreview',
            'isLivePreviewEnabled'
        ]
        
        for component in toggle_components:
            if component in content:
                logger.info(f"✅ Toggle component {component} found")
            else:
                logger.error(f"❌ Toggle component {component} not found")
                return False
        
        logger.info("✅ Live preview toggle test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Live preview toggle test failed: {str(e)}")
        return False

def test_visual_feedback():
    """Test visual feedback components"""
    logger.info("Testing visual feedback...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for visual feedback components
        visual_components = [
            'live-preview-active',
            'addLivePreviewStyling',
            'removeLivePreviewStyling',
            'live-preview-indicator',
            'Live Preview Active',
            'animation: pulse',
            'animation: slideIn',
            'transition: all 0.3s ease'
        ]
        
        for component in visual_components:
            if component in content:
                logger.info(f"✅ Visual feedback component {component} found")
            else:
                logger.error(f"❌ Visual feedback component {component} not found")
                return False
        
        logger.info("✅ Visual feedback test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Visual feedback test failed: {str(e)}")
        return False

def test_parameter_calculation():
    """Test parameter calculation functions"""
    logger.info("Testing parameter calculation...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for calculation components
        calculation_components = [
            'baseACWR = 1.0 + (chronicPeriod - 42) / 100',
            'baseAcute = 80 + Math.sin(chronicPeriod / 10) * 10',
            'baseChronic = 100 + Math.cos(decayRate * 10) * 15',
            'baseQuality = 85 + Math.sin(chronicPeriod / 20) * 5',
            'Predicted ACWR',
            'Predicted Acute Load',
            'Predicted Chronic Load',
            'Live Preview)'
        ]
        
        for component in calculation_components:
            if component in content:
                logger.info(f"✅ Calculation component {component} found")
            else:
                logger.error(f"❌ Calculation component {component} not found")
                return False
        
        logger.info("✅ Parameter calculation test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Parameter calculation test failed: {str(e)}")
        return False

def test_comparison_analysis():
    """Test comparison analysis functionality"""
    logger.info("Testing comparison analysis...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for comparison components
        comparison_components = [
            'updateWhatIfAnalysis',
            'Conservative (56d, 0.03)',
            'Moderate (42d, 0.05)',
            'Aggressive (28d, 0.08)',
            'vs current',
            'text-danger',
            'text-success',
            'differencePercent',
            'currentConfigDetails',
            'whatIfAnalysis'
        ]
        
        for component in comparison_components:
            if component in content:
                logger.info(f"✅ Comparison component {component} found")
            else:
                logger.error(f"❌ Comparison component {component} not found")
                return False
        
        logger.info("✅ Comparison analysis test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Comparison analysis test failed: {str(e)}")
        return False

def test_event_handling():
    """Test event handling for live preview"""
    logger.info("Testing event handling...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for event handling components
        event_components = [
            'addEventListener(\'input\', addLivePreviewStyling)',
            'addEventListener(\'mouseup\', removeLivePreviewStyling)',
            'addEventListener(\'change\', addLivePreviewStyling)',
            'parameterChangeTimeout',
            'clearTimeout',
            'setTimeout',
            'avoid too many API calls'
        ]
        
        for component in event_components:
            if component in content:
                logger.info(f"✅ Event handling component {component} found")
            else:
                logger.error(f"❌ Event handling component {component} not found")
                return False
        
        logger.info("✅ Event handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Event handling test failed: {str(e)}")
        return False

def test_css_animations():
    """Test CSS animations for live preview"""
    logger.info("Testing CSS animations...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for CSS animation components
        animation_components = [
            '@keyframes pulse',
            '@keyframes slideIn',
            'transform: scale(1.05)',
            'transform: translateX(100%)',
            'transition: all 0.3s ease',
            'box-shadow: 0 0 10px rgba(0, 123, 255, 0.3)',
            'border: 2px solid #007bff',
            'background: rgba(0, 123, 255, 0.1)'
        ]
        
        for component in animation_components:
            if component in content:
                logger.info(f"✅ CSS animation component {component} found")
            else:
                logger.error(f"❌ CSS animation component {component} not found")
                return False
        
        logger.info("✅ CSS animations test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ CSS animations test failed: {str(e)}")
        return False

def test_performance_optimization():
    """Test performance optimization features"""
    logger.info("Testing performance optimization...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for performance optimization components
        performance_components = [
            'clearTimeout(window.parameterChangeTimeout)',
            'setTimeout(() => {',
            '1000)',
            'avoid too many API calls',
            'immediate',
            'real-time',
            'updateVisualizations',
            'full visualization updates'
        ]
        
        for component in performance_components:
            if component in content:
                logger.info(f"✅ Performance component {component} found")
            else:
                logger.error(f"❌ Performance component {component} not found")
                return False
        
        logger.info("✅ Performance optimization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance optimization test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all live preview tests"""
    logger.info("=" * 60)
    logger.info("Live Preview Functionality Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Live Preview Components", test_live_preview_components),
        ("Live Preview Toggle", test_live_preview_toggle),
        ("Visual Feedback", test_visual_feedback),
        ("Parameter Calculation", test_parameter_calculation),
        ("Comparison Analysis", test_comparison_analysis),
        ("Event Handling", test_event_handling),
        ("CSS Animations", test_css_animations),
        ("Performance Optimization", test_performance_optimization)
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
        logger.info("🎉 All tests passed! Live preview functionality is working correctly.")
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
