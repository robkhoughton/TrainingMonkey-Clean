#!/usr/bin/env python3
"""
Comprehensive test suite runner for TRIMP enhancement system
Runs all tests related to the enhanced TRIMP calculation functionality
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all test modules
from test_enhanced_trimp_calculation import TestEnhancedTrimpCalculation, TestTrimpCalculationIntegration
from test_feature_flags_system import TestFeatureFlagsSystem, TestFeatureFlagsIntegration
from test_historical_recalculation_system import TestHistoricalTrimpRecalculator, TestRecalculationDataStructures
from test_database_utilities import TestDatabaseUtilities, TestDatabaseUtilitiesIntegration


class TrimpEnhancementTestSuite:
    """Test suite runner for TRIMP enhancement system"""
    
    def __init__(self):
        self.test_suites = []
        self.results = {}
        self.total_tests = 0
        self.total_failures = 0
        self.total_errors = 0
        self.total_skipped = 0
    
    def add_test_suite(self, test_class, suite_name):
        """Add a test suite to the runner"""
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        self.test_suites.append((suite, suite_name))
        self.total_tests += suite.countTestCases()
    
    def run_all_tests(self, verbosity=2):
        """Run all test suites and return results"""
        print("=" * 80)
        print("🧪 TRIMP ENHANCEMENT COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print(f"Total test suites: {len(self.test_suites)}")
        print(f"Total test cases: {self.total_tests}")
        print("=" * 80)
        
        start_time = time.time()
        
        for suite, suite_name in self.test_suites:
            print(f"\n📋 Running {suite_name}...")
            print("-" * 60)
            
            # Capture output
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=verbosity)
            result = runner.run(suite)
            
            # Store results
            self.results[suite_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'success': result.wasSuccessful(),
                'output': stream.getvalue()
            }
            
            # Update totals
            self.total_failures += len(result.failures)
            self.total_errors += len(result.errors)
            self.total_skipped += len(result.skipped) if hasattr(result, 'skipped') else 0
            
            # Print results
            if result.wasSuccessful():
                print(f"✅ {suite_name}: PASSED ({result.testsRun} tests)")
            else:
                print(f"❌ {suite_name}: FAILED ({result.testsRun} tests)")
                if result.failures:
                    print(f"   Failures: {len(result.failures)}")
                if result.errors:
                    print(f"   Errors: {len(result.errors)}")
                if hasattr(result, 'skipped') and result.skipped:
                    print(f"   Skipped: {len(result.skipped)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        self.print_summary(duration)
        
        return self.results
    
    def print_summary(self, duration):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_passed = self.total_tests - self.total_failures - self.total_errors - self.total_skipped
        
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {total_passed}")
        print(f"❌ Failed: {self.total_failures}")
        print(f"💥 Errors: {self.total_errors}")
        print(f"⏭️  Skipped: {self.total_skipped}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        success_rate = (total_passed / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.total_failures > 0 or self.total_errors > 0:
            print("\n❌ SOME TESTS FAILED!")
            self.print_failure_details()
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print("=" * 80)
    
    def print_failure_details(self):
        """Print details of failed tests"""
        print("\n🔍 FAILURE DETAILS:")
        print("-" * 40)
        
        for suite_name, result in self.results.items():
            if not result['success']:
                print(f"\n📋 {suite_name}:")
                if result['failures'] > 0:
                    print(f"   Failures: {result['failures']}")
                if result['errors'] > 0:
                    print(f"   Errors: {result['errors']}")
                
                # Print first few lines of output for debugging
                output_lines = result['output'].split('\n')
                relevant_lines = [line for line in output_lines if 'FAIL' in line or 'ERROR' in line][:3]
                for line in relevant_lines:
                    if line.strip():
                        print(f"   {line.strip()}")
    
    def run_specific_suite(self, suite_name, verbosity=2):
        """Run a specific test suite"""
        for suite, name in self.test_suites:
            if name == suite_name:
                print(f"📋 Running {suite_name}...")
                print("-" * 60)
                
                runner = unittest.TextTestRunner(verbosity=verbosity)
                result = runner.run(suite)
                
                return result.wasSuccessful()
        
        print(f"❌ Test suite '{suite_name}' not found!")
        return False
    
    def list_test_suites(self):
        """List all available test suites"""
        print("📋 Available Test Suites:")
        print("-" * 30)
        for i, (suite, name) in enumerate(self.test_suites, 1):
            test_count = suite.countTestCases()
            print(f"{i}. {name} ({test_count} tests)")


def create_test_suite():
    """Create and configure the test suite"""
    suite_runner = TrimpEnhancementTestSuite()
    
    # Add all test suites
    suite_runner.add_test_suite(TestEnhancedTrimpCalculation, "Enhanced TRIMP Calculation - Unit Tests")
    suite_runner.add_test_suite(TestTrimpCalculationIntegration, "Enhanced TRIMP Calculation - Integration Tests")
    suite_runner.add_test_suite(TestFeatureFlagsSystem, "Feature Flags System - Unit Tests")
    suite_runner.add_test_suite(TestFeatureFlagsIntegration, "Feature Flags System - Integration Tests")
    suite_runner.add_test_suite(TestHistoricalTrimpRecalculator, "Historical Recalculation System - Unit Tests")
    suite_runner.add_test_suite(TestRecalculationDataStructures, "Historical Recalculation System - Data Structures")
    suite_runner.add_test_suite(TestDatabaseUtilities, "Database Utilities - Unit Tests")
    suite_runner.add_test_suite(TestDatabaseUtilitiesIntegration, "Database Utilities - Integration Tests")
    
    return suite_runner


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run TRIMP Enhancement Test Suite')
    parser.add_argument('--suite', help='Run specific test suite')
    parser.add_argument('--list', action='store_true', help='List available test suites')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    
    args = parser.parse_args()
    
    suite_runner = create_test_suite()
    
    if args.list:
        suite_runner.list_test_suites()
        return
    
    verbosity = 2
    if args.verbose:
        verbosity = 3
    elif args.quiet:
        verbosity = 1
    
    if args.suite:
        success = suite_runner.run_specific_suite(args.suite, verbosity)
        sys.exit(0 if success else 1)
    else:
        results = suite_runner.run_all_tests(verbosity)
        total_failures = sum(r['failures'] for r in results.values())
        total_errors = sum(r['errors'] for r in results.values())
        sys.exit(0 if (total_failures == 0 and total_errors == 0) else 1)


if __name__ == '__main__':
    main()
