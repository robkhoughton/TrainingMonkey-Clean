#!/usr/bin/env python3
"""
Pre-commit Hooks
Automated validation before code commits
"""

import subprocess
import sys
import os

def run_sql_validation():
    """Run SQL syntax validation"""
    print("🔍 Running SQL syntax validation...")
    result = subprocess.run([sys.executable, 'scripts/validate_sql_syntax.py'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ SQL validation failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("✅ SQL validation passed!")
    return True

def run_database_rules_check():
    """Check for database rule violations"""
    print("🔍 Checking database rules compliance...")
    
    # Check for forbidden SQLite imports
    forbidden_patterns = [
        'import sqlite3',
        'from sqlite3 import',
        'sqlite3.connect',
        'sqlite3.Cursor'
    ]
    
    app_dir = 'app'
    violations = []
    
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in forbidden_patterns:
                            if pattern in content:
                                violations.append(f"{file_path}: {pattern}")
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}")
    
    if violations:
        print("❌ Database rule violations found:")
        for violation in violations:
            print(f"   {violation}")
        return False
    
    print("✅ Database rules compliance passed!")
    return True

def main():
    """Run all pre-commit checks"""
    print("🚀 Running pre-commit validation...")
    
    checks = [
        run_sql_validation,
        run_database_rules_check
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        print("✅ All pre-commit checks passed!")
        return 0
    else:
        print("❌ Pre-commit checks failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
