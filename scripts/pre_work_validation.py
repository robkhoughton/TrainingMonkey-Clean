#!/usr/bin/env python3
"""
Pre-Work Validation Script for TrainingMonkey
Run this before starting any development work to ensure standards compliance
"""

import os
import subprocess
import sys

def check_cursorrules():
    """Check if .cursorrules file exists and contains key standards"""
    if not os.path.exists('.cursorrules'):
        print("❌ .cursorrules file missing - project standards not configured")
        return False
    
    with open('.cursorrules', 'r', encoding='utf-8') as f:
        content = f.read()
        
    required_standards = [
        'PostgreSQL ONLY',
        '`%s` placeholders',
        'SERIAL PRIMARY KEY',
        'NOW()',
        'SQL Editor ONLY'
    ]
    
    missing = [std for std in required_standards if std not in content]
    if missing:
        print(f"❌ .cursorrules missing standards: {missing}")
        return False
    
    print("✅ .cursorrules file configured with project standards")
    return True

def check_guiding_principles():
    """Check if guiding principles document exists"""
    if not os.path.exists('guiding_principles_summary.md'):
        print("❌ guiding_principles_summary.md missing")
        return False
    
    print("✅ Guiding principles document available")
    return True

def check_validation_script():
    """Check if SQL validation script exists"""
    if not os.path.exists('scripts/validate_sql_syntax.py'):
        print("❌ SQL validation script missing")
        return False
    
    print("✅ SQL validation script available")
    return True

def run_sql_validation():
    """Run SQL syntax validation"""
    try:
        result = subprocess.run([
            sys.executable, 'scripts/validate_sql_syntax.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SQL syntax validation passed")
            return True
        else:
            print(f"❌ SQL syntax validation failed: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Could not run SQL validation: {e}")
        return False

def main():
    """Run all pre-work validations"""
    print("🔍 TrainingMonkey Pre-Work Validation")
    print("=" * 40)
    
    checks = [
        check_cursorrules(),
        check_guiding_principles(),
        check_validation_script(),
        run_sql_validation()
    ]
    
    if all(checks):
        print("\n🎉 All validations passed - ready for development!")
        return True
    else:
        print("\n❌ Some validations failed - please address issues before continuing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
