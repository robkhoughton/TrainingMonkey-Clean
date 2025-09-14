#!/usr/bin/env python3
"""
Final Batch SQLite Fixer
Fixes remaining SQLite placeholders in all files
"""

import sys
import os
from pathlib import Path

# Import the fixer functions
sys.path.append(os.path.dirname(__file__))
from fix_sqlite_placeholders import fix_sqlite_placeholders
from enhanced_fix_sqlite import fix_complex_patterns

def main():
    """Fix remaining SQLite placeholders in all files"""
    
    # Get all Python files in app directory
    app_dir = Path("app")
    python_files = list(app_dir.rglob("*.py"))
    
    total_fixes = 0
    files_processed = 0
    
    print("🔧 Final batch fixing SQLite placeholders in all Python files...")
    print("=" * 70)
    
    for file_path in python_files:
        file_str = str(file_path)
        print(f"\n📁 Processing: {file_str}")
        
        # Apply basic fixes first
        basic_fixes = fix_sqlite_placeholders(file_str)
        
        # Apply enhanced fixes for complex patterns
        complex_fixes = fix_complex_patterns(file_str)
        
        total_fixes += basic_fixes + complex_fixes
        files_processed += 1
        
        if basic_fixes > 0 or complex_fixes > 0:
            print(f"✅ Total fixes applied: {basic_fixes + complex_fixes}")
        else:
            print("ℹ️  No fixes needed")
    
    print("\n" + "=" * 70)
    print(f"🎉 Final batch processing complete!")
    print(f"📊 Files processed: {files_processed}")
    print(f"🔧 Total fixes applied: {total_fixes}")
    print(f"📋 Run validation to check results: python scripts/validate_sql_syntax.py")
    
    return total_fixes

if __name__ == '__main__':
    main()
