#!/usr/bin/env python3
"""
Comprehensive Test Runner for TrainingMonkey Transition Optimization

This script runs all test suites for the transition optimization project,
including unit tests, integration tests, and quality assurance tests.
"""

import unittest
import sys
import os
import time
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

def run_test_suite(test_module, test_class=None):
    """Run a specific test suite"""
    try:
        # Import the test module
        module = __import__(test_module)
        
        # Create test suite
        if test_class:
            test_suite = unittest.makeSuite(getattr(module, test_class))
        else:
            test_suite = unittest.TestLoader().loadTestsFromModule(module)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(test_suite)
        
        return {
            'module': test_module,
            'class': test_class,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
        }
    except Exception as e:
        return {
            'module': test_module,
            'class': test_class,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'success_rate': 0,
            'error': str(e)
        }

def main():
    """Main test runner function"""
    print("=" * 80)
    print("TrainingMonkey Transition Optimization - Comprehensive Test Suite")
    print("=" * 80)
    print(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Define test suites to run
    test_suites = [
        {
            'name': 'Getting Started Route Tests',
            'module': 'test_getting_started',
            'description': 'Unit tests for getting started route functionality'
        },
        {
            'name': 'Context Detection Tests',
            'module': 'test_context_detection',
            'description': 'Unit tests for context detection and user authentication'
        },
        {
            'name': 'Analytics Tracking Tests',
            'module': 'test_analytics_tracking',
            'description': 'Unit tests for analytics tracking functionality'
        },
        {
            'name': 'Transition Integration Tests',
            'module': 'test_transition_integration',
            'description': 'Integration tests for complete user journey flows'
        }
    ]
    
    # Run all test suites
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    successful_suites = 0
    
    for suite in test_suites:
        print(f"Running {suite['name']}...")
        print(f"Description: {suite['description']}")
        print("-" * 60)
        
        start_time = time.time()
        result = run_test_suite(suite['module'])
        end_time = time.time()
        
        result['name'] = suite['name']
        result['description'] = suite['description']
        result['duration'] = end_time - start_time
        results.append(result)
        
        # Update totals
        total_tests += result['tests_run']
        total_failures += result['failures']
        total_errors += result['errors']
        if result['success']:
            successful_suites += 1
        
        # Print suite summary
        print(f"\n{suite['name']} Summary:")
        print(f"  Tests run: {result['tests_run']}")
        print(f"  Failures: {result['failures']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Success rate: {result['success_rate']:.1f}%")
        print(f"  Duration: {result['duration']:.2f} seconds")
        print(f"  Status: {'PASSED' if result['success'] else 'FAILED'}")
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
        
        print()
        print("=" * 80)
        print()
    
    # Print overall summary
    print("OVERALL TEST SUMMARY")
    print("=" * 80)
    print(f"Total test suites: {len(test_suites)}")
    print(f"Successful suites: {successful_suites}")
    print(f"Failed suites: {len(test_suites) - successful_suites}")
    print(f"Total tests run: {total_tests}")
    print(f"Total failures: {total_failures}")
    print(f"Total errors: {total_errors}")
    print(f"Overall success rate: {((total_tests - total_failures - total_errors) / total_tests * 100) if total_tests > 0 else 0:.1f}%")
    print()
    
    # Print detailed results
    print("DETAILED RESULTS")
    print("=" * 80)
    for result in results:
        print(f"{result['name']}:")
        print(f"  Tests: {result['tests_run']}, Failures: {result['failures']}, Errors: {result['errors']}")
        print(f"  Success Rate: {result['success_rate']:.1f}%, Duration: {result['duration']:.2f}s")
        print(f"  Status: {'PASSED' if result['success'] else 'FAILED'}")
        if 'error' in result:
            print(f"  Error: {result['error']}")
        print()
    
    # Print recommendations
    print("RECOMMENDATIONS")
    print("=" * 80)
    if total_failures > 0 or total_errors > 0:
        print("❌ Some tests failed. Please review the following:")
        print("   1. Check the test output above for specific failure details")
        print("   2. Ensure all dependencies are properly installed")
        print("   3. Verify database connections and mock configurations")
        print("   4. Review test data and expected outcomes")
        print("   5. Check for any recent changes that might have broken tests")
    else:
        print("✅ All tests passed successfully!")
        print("   The transition optimization implementation is working correctly.")
        print("   All integration points, analytics tracking, and user flows are functional.")
    
    print()
    print("=" * 80)
    print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Exit with appropriate code
    overall_success = (total_failures == 0 and total_errors == 0)
    sys.exit(0 if overall_success else 1)

if __name__ == '__main__':
    main()
