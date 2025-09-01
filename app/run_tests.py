#!/usr/bin/env python3
"""
Test Runner for Training Monkey™ Dashboard
Run this script to execute all Phase 1 tests locally
"""

import os
import sys
import unittest
import subprocess
from pathlib import Path

def run_tests():
    """Run all tests in the tests directory"""
    
    # Add the current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = current_dir / 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1

def run_specific_test(test_file):
    """Run a specific test file"""
    test_path = Path(__file__).parent / 'tests' / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return 1
    
    # Run the specific test
    result = subprocess.run([sys.executable, str(test_path)], 
                          cwd=Path(__file__).parent)
    return result.returncode

def list_tests():
    """List all available tests"""
    tests_dir = Path(__file__).parent / 'tests'
    
    if not tests_dir.exists():
        print("❌ Tests directory not found")
        return
    
    print("📋 Available Tests:")
    print("=" * 50)
    
    for test_file in sorted(tests_dir.glob('test_*.py')):
        print(f"  • {test_file.name}")
    
    print("\n💡 Usage:")
    print("  python run_tests.py                    # Run all tests")
    print("  python run_tests.py test_file.py       # Run specific test")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            list_tests()
        else:
            # Run specific test file
            exit_code = run_specific_test(sys.argv[1])
            sys.exit(exit_code)
    else:
        # Run all tests
        print("🧪 Running Phase 1 Tests...")
        print("=" * 50)
        exit_code = run_tests()
        sys.exit(exit_code)



