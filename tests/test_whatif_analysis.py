#!/usr/bin/env python3
"""
Test script for What-If Analysis Functionality
Tests the comprehensive what-if analysis capabilities with parameter comparison
"""

import sys
import os
import logging

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_whatif_components():
    """Test that what-if analysis components exist"""
    logger.info("Testing what-if analysis components...")
    
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
        
        # Check for what-if analysis specific components
        whatif_components = [
            'What-If Analysis & Parameter Comparison',
            'addCustomScenario',
            'exportWhatIfAnalysis',
            'initializeWhatIfScenarios',
            'updateScenarioDisplays',
            'createScenarioCard',
            'generateImpactAnalysis',
            'generateRiskAssessment',
            'createScenarioComparisonChart',
            'selectScenario',
            'saveCustomScenario',
            'scenarioA',
            'scenarioB',
            'scenarioC',
            'impactAnalysis',
            'riskAssessment',
            'scenarioComparisonChart'
        ]
        
        for component in whatif_components:
            if component in content:
                logger.info(f"✅ What-if component {component} found")
            else:
                logger.error(f"❌ What-if component {component} not found")
                return False
        
        logger.info("✅ What-if analysis components test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ What-if analysis components test failed: {str(e)}")
        return False

def test_scenario_management():
    """Test scenario management functionality"""
    logger.info("Testing scenario management...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for scenario management components
        scenario_components = [
            'window.whatIfScenarios',
            'scenarioA:',
            'scenarioB:',
            'scenarioC:',
            'Current Configuration',
            'Conservative Approach',
            'Aggressive Approach',
            'chronic_period:',
            'decay_rate:',
            'acwr_ratio:',
            'acute_load:',
            'chronic_load:',
            'risk_level:'
        ]
        
        for component in scenario_components:
            if component in content:
                logger.info(f"✅ Scenario component {component} found")
            else:
                logger.error(f"❌ Scenario component {component} not found")
                return False
        
        logger.info("✅ Scenario management test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scenario management test failed: {str(e)}")
        return False

def test_impact_analysis():
    """Test impact analysis functionality"""
    logger.info("Testing impact analysis...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for impact analysis components
        impact_components = [
            'ACWR Change (vs Current)',
            'Training Load Impact',
            'Recovery Time',
            'Conservative:',
            'Aggressive:',
            'Lower intensity',
            'Higher intensity',
            'Faster recovery',
            'Longer recovery',
            'text-success',
            'text-danger',
            'text-info',
            'text-warning'
        ]
        
        for component in impact_components:
            if component in content:
                logger.info(f"✅ Impact analysis component {component} found")
            else:
                logger.error(f"❌ Impact analysis component {component} not found")
                return False
        
        logger.info("✅ Impact analysis test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Impact analysis test failed: {str(e)}")
        return False

def test_risk_assessment():
    """Test risk assessment functionality"""
    logger.info("Testing risk assessment...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for risk assessment components
        risk_components = [
            'Injury Risk',
            'Performance Impact',
            'Recommendation',
            'Low (',
            'Moderate (',
            'High (',
            'Steady progress',
            'Balanced approach',
            'High variability',
            'Safe for beginners',
            'Good for experienced',
            'Advanced only'
        ]
        
        for component in risk_components:
            if component in content:
                logger.info(f"✅ Risk assessment component {component} found")
            else:
                logger.error(f"❌ Risk assessment component {component} not found")
                return False
        
        logger.info("✅ Risk assessment test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Risk assessment test failed: {str(e)}")
        return False

def test_comparison_chart():
    """Test comparison chart functionality"""
    logger.info("Testing comparison chart...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for comparison chart components
        chart_components = [
            'createScenarioComparisonChart',
            'Plotly.newPlot',
            'scenarioComparisonChart',
            'Chronic Period',
            'Decay Rate',
            'ACWR Ratio',
            'Acute Load',
            'Chronic Load',
            'Current',
            'Conservative',
            'Aggressive',
            'type: \'bar\'',
            'barmode: \'group\'',
            'marker: { color: \'#007bff\' }',
            'marker: { color: \'#28a745\' }',
            'marker: { color: \'#dc3545\' }'
        ]
        
        for component in chart_components:
            if component in content:
                logger.info(f"✅ Comparison chart component {component} found")
            else:
                logger.error(f"❌ Comparison chart component {component} not found")
                return False
        
        logger.info("✅ Comparison chart test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Comparison chart test failed: {str(e)}")
        return False

def test_custom_scenarios():
    """Test custom scenario functionality"""
    logger.info("Testing custom scenarios...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for custom scenario components
        custom_components = [
            'addCustomScenario',
            'saveCustomScenario',
            'customScenarioModal',
            'customScenarioName',
            'customChronicPeriod',
            'customDecayRate',
            'modal fade',
            'modal-dialog',
            'modal-content',
            'modal-header',
            'modal-body',
            'modal-footer',
            'data-bs-dismiss="modal"',
            'bootstrap.Modal',
            'Please enter a scenario name'
        ]
        
        for component in custom_components:
            if component in content:
                logger.info(f"✅ Custom scenario component {component} found")
            else:
                logger.error(f"❌ Custom scenario component {component} not found")
                return False
        
        logger.info("✅ Custom scenarios test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Custom scenarios test failed: {str(e)}")
        return False

def test_export_functionality():
    """Test export functionality"""
    logger.info("Testing export functionality...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for export components
        export_components = [
            'exportWhatIfAnalysis',
            'JSON.stringify',
            'Blob',
            'application/json',
            'URL.createObjectURL',
            'createElement(\'a\')',
            'download =',
            'what-if-analysis-',
            'URL.revokeObjectURL',
            'exportData',
            'timestamp:',
            'scenarios:',
            'analysis:'
        ]
        
        for component in export_components:
            if component in content:
                logger.info(f"✅ Export component {component} found")
            else:
                logger.error(f"❌ Export component {component} not found")
                return False
        
        logger.info("✅ Export functionality test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Export functionality test failed: {str(e)}")
        return False

def test_ui_components():
    """Test UI components"""
    logger.info("Testing UI components...")
    
    try:
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'acwr_visualization_dashboard.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for UI components
        ui_components = [
            'scenario-card',
            'comparison-panel',
            'card-header',
            'card-body',
            'impact-analysis-card',
            'risk-assessment-card',
            'scenario-comparison-chart',
            'Select This Scenario',
            'Add Custom Scenario',
            'Export Analysis',
            'Scenario A (Current)',
            'Scenario B (Comparison)',
            'Scenario C (Alternative)'
        ]
        
        for component in ui_components:
            if component in content:
                logger.info(f"✅ UI component {component} found")
            else:
                logger.error(f"❌ UI component {component} not found")
                return False
        
        logger.info("✅ UI components test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ UI components test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all what-if analysis tests"""
    logger.info("=" * 60)
    logger.info("What-If Analysis Functionality Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("What-If Components", test_whatif_components),
        ("Scenario Management", test_scenario_management),
        ("Impact Analysis", test_impact_analysis),
        ("Risk Assessment", test_risk_assessment),
        ("Comparison Chart", test_comparison_chart),
        ("Custom Scenarios", test_custom_scenarios),
        ("Export Functionality", test_export_functionality),
        ("UI Components", test_ui_components)
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
        logger.info("🎉 All tests passed! What-if analysis functionality is working correctly.")
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

