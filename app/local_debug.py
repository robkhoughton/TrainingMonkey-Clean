#!/usr/bin/env python3
"""
Test script to identify import issues before deployment
Run this in your strava_sync_service directory to catch import problems
"""

import sys
import traceback


def test_import(module_name):
    """Test importing a specific module and report any errors"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - Import successful")
        return True
    except Exception as e:
        print(f"❌ {module_name} - Import failed: {str(e)}")
        print(f"   Error details: {traceback.format_exc()}")
        return False


def main():
    """Test all critical imports"""
    print("Testing imports for Training Monkey deployment...")
    print("=" * 50)

    # Test core modules
    modules_to_test = [
        'db_utils',
        'timezone_utils',
        'auth',
        'enhanced_token_management',
        'unified_metrics_service',
        'strava_training_load',
        'llm_recommendations_module',
        'strava_app'  # Test this last as it imports others
    ]

    success_count = 0
    total_count = len(modules_to_test)

    for module in modules_to_test:
        if test_import(module):
            success_count += 1
        print()

    print("=" * 50)
    print(f"Import Test Results: {success_count}/{total_count} successful")

    if success_count == total_count:
        print("🎉 All imports successful! Deployment should work.")
        return 0
    else:
        print("🚨 Import errors detected! Fix these before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())