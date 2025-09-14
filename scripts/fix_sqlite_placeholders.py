#!/usr/bin/env python3
"""
SQLite Placeholder Fixer
Converts SQLite placeholders (?) to PostgreSQL placeholders (%s)
"""

import re
import sys
from pathlib import Path

def fix_sqlite_placeholders(file_path: str) -> int:
    """Fix SQLite placeholders in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # Common SQLite placeholder patterns to fix
        patterns = [
            # WHERE clauses
            (r'WHERE id = \?', 'WHERE id = %s'),
            (r'WHERE user_id = \?', 'WHERE user_id = %s'),
            (r'WHERE activity_id = \?', 'WHERE activity_id = %s'),
            (r'WHERE date = \?', 'WHERE date = %s'),
            (r'WHERE user_id = \? AND', 'WHERE user_id = %s AND'),
            (r'WHERE id = \? AND', 'WHERE id = %s AND'),
            (r'WHERE activity_id = \? AND', 'WHERE activity_id = %s AND'),
            (r'WHERE date = \? AND', 'WHERE date = %s AND'),
            
            # AND clauses
            (r'AND user_id = \?', 'AND user_id = %s'),
            (r'AND id = \?', 'AND id = %s'),
            (r'AND activity_id = \?', 'AND activity_id = %s'),
            (r'AND date = \?', 'AND date = %s'),
            
            # VALUES clauses
            (r'VALUES \(\?', 'VALUES (%s'),
            (r'VALUES \(.*\?', 'VALUES (%s'),
            
            # SET clauses
            (r'SET .* = \?', 'SET %s = %s'),
            
            # ORDER BY and LIMIT
            (r'ORDER BY .* \?', 'ORDER BY %s'),
            (r'LIMIT \?', 'LIMIT %s'),
            
            # BETWEEN clauses
            (r'BETWEEN \? AND \?', 'BETWEEN %s AND %s'),
        ]
        
        # Apply replacements
        for pattern, replacement in patterns:
            old_content = content
            content = re.sub(pattern, replacement, content)
            if content != old_content:
                fixes_applied += 1
                print(f"✅ Fixed pattern: {pattern}")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🎉 Applied {fixes_applied} fixes to {file_path}")
        else:
            print(f"ℹ️  No fixes needed for {file_path}")
        
        return fixes_applied
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")
        return 0

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python fix_sqlite_placeholders.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print(f"🔧 Fixing SQLite placeholders in {file_path}...")
    fixes = fix_sqlite_placeholders(file_path)
    
    if fixes > 0:
        print(f"📋 Run validation to check results: python scripts/validate_sql_syntax.py")
    
    return fixes

if __name__ == '__main__':
    main()
