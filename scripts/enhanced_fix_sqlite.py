#!/usr/bin/env python3
"""
Enhanced SQLite Placeholder Fixer
Handles complex patterns and edge cases
"""

import re
import sys
from pathlib import Path

def fix_complex_patterns(file_path: str) -> int:
    """Fix complex SQLite placeholder patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        # Complex patterns that need special handling
        complex_patterns = [
            # Mixed placeholder patterns
            (r'WHERE user_id = %s AND date >= \?', 'WHERE user_id = %s AND date >= %s'),
            (r'WHERE user_id = %s AND date = \?', 'WHERE user_id = %s AND date = %s'),
            (r'WHERE user_id = %s AND target_date = \?', 'WHERE user_id = %s AND target_date = %s'),
            (r'WHERE user_id = %s AND valid_until = \?', 'WHERE user_id = %s AND valid_until = %s'),
            (r'WHERE user_id = %s AND activity_id > \?', 'WHERE user_id = %s AND activity_id > %s'),
            (r'WHERE user_id = %s AND date = \? AND activity_id > \?', 'WHERE user_id = %s AND date = %s AND activity_id > %s'),
            
            # SET patterns with mixed placeholders
            (r'SET %s = %s,\s*trimp_calculation_method = \?', 'SET %s = %s, trimp_calculation_method = %s'),
            (r'SET %s = %s,\s*strava_refresh_token = \?', 'SET %s = %s, strava_refresh_token = %s'),
            (r'SET %s = %s,\s*strava_access_token = \?', 'SET %s = %s, strava_access_token = %s'),
            (r'SET %s = %s,\s*last_onboard', 'SET %s = %s, last_onboard'),
            (r'SET %s = %s\s*WHERE status = \?', 'SET %s = %s WHERE status = %s'),
            (r'SET %s = %s\s*WHERE session_id = \?', 'SET %s = %s WHERE session_id = %s'),
            (r'SET %s = %s\s*WHERE email = \?', 'SET %s = %s WHERE email = %s'),
            
            # Complex WHERE patterns
            (r'WHERE status = \? AND expires_at', 'WHERE status = %s AND expires_at'),
            (r'WHERE status = \? AND session_id', 'WHERE status = %s AND session_id'),
            (r'WHERE status = \? AND user_id', 'WHERE status = %s AND user_id'),
            (r'WHERE status = \? AND created_at', 'WHERE status = %s AND created_at'),
            (r'WHERE status = \? AND updated_at', 'WHERE status = %s AND updated_at'),
            
            # Date range patterns
            (r'WHERE date >= \? AND user_id = %s', 'WHERE date >= %s AND user_id = %s'),
            (r'WHERE date BETWEEN \? AND \? AND user_id = %s', 'WHERE date BETWEEN %s AND %s AND user_id = %s'),
            
            # Complex SELECT patterns
            (r'WHERE user_id = %s AND t\?', 'WHERE user_id = %s AND t%s'),
            (r'WHERE user_id = %s AND ta\?', 'WHERE user_id = %s AND ta%s'),
            
            # Timestamp patterns
            (r'WHERE timestamp < \?', 'WHERE timestamp < %s'),
            (r'WHERE trimp_processed_at >= \?', 'WHERE trimp_processed_at >= %s'),
            (r'WHERE trimp_processed_at < \?', 'WHERE trimp_processed_at < %s'),
            
            # Activity patterns
            (r'WHERE activity_id = \? AND user_id = %s', 'WHERE activity_id = %s AND user_id = %s'),
            (r'WHERE activity_id = \? AND date = \?', 'WHERE activity_id = %s AND date = %s'),
            
            # Configuration patterns
            (r'WHERE configuration_id = \?', 'WHERE configuration_id = %s'),
            (r'WHERE configuration_id = \? AND', 'WHERE configuration_id = %s AND'),
            
            # Email patterns
            (r'WHERE email = \?', 'WHERE email = %s'),
            (r'WHERE email = \? AND', 'WHERE email = %s AND'),
        ]
        
        # Apply complex replacements
        for pattern, replacement in complex_patterns:
            old_content = content
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE | re.MULTILINE)
            if content != old_content:
                fixes_applied += 1
                print(f"✅ Fixed complex pattern: {pattern}")
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"🎉 Applied {fixes_applied} complex fixes to {file_path}")
        else:
            print(f"ℹ️  No complex fixes needed for {file_path}")
        
        return fixes_applied
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")
        return 0

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python enhanced_fix_sqlite.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    print(f"🔧 Applying enhanced fixes to {file_path}...")
    fixes = fix_complex_patterns(file_path)
    
    if fixes > 0:
        print(f"📋 Run validation to check results: python scripts/validate_sql_syntax.py")
    
    return fixes

if __name__ == '__main__':
    main()
