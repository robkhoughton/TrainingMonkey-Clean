#!/usr/bin/env python3
"""
SQL Syntax Validator
Validates that all SQL queries use PostgreSQL syntax (not SQLite)
"""

import os
import re
import sys
from pathlib import Path

def validate_sql_syntax(file_path: str) -> list:
    """Validate SQL syntax in a Python file"""
    issues = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find SQL queries more precisely - look for execute_query patterns or triple-quoted SQL
        # This reduces false positives from email templates, URLs, etc.
        sql_patterns = [
            # Triple-quoted strings with SQL keywords (common for queries)
            r'"""([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)[^"]*)"""',
            r"'''([^']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)[^']*)'''",
            # execute_query calls with string arguments
            r'execute_query\s*\(\s*["\']([^"\']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)[^"\']*)["\']',
        ]

        sql_queries = []
        for pattern in sql_patterns:
            sql_queries.extend(re.findall(pattern, content, re.IGNORECASE | re.DOTALL))

        for i, query in enumerate(sql_queries):
            # Filter out obvious false positives
            query_lower = query.lower()

            # Skip if this looks like a regex pattern (contains regex metacharacters in brackets)
            if re.search(r'\[[^\]]*[\?\*\+\^\\$]+[^\]]*\]', query):
                continue

            # Skip if this looks like a URL (contains ?token=, ?id=, etc.)
            if re.search(r'\?[a-z_]+=', query):
                continue

            # Skip if this is just text with SQL keywords but no SQL structure
            # Real SQL queries have structural keywords like FROM, WHERE, VALUES, SET
            has_structure = any(kw in query_lower for kw in ['from ', 'where ', 'values', ' set ', 'join '])
            has_sql_keyword = any(kw in query_lower for kw in ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter'])

            if has_sql_keyword and not has_structure and len(query) < 100:
                # Likely just text mentioning SQL keywords, not actual SQL
                continue

            # Check for SQLite placeholders in actual SQL context
            # Look for ? that appears to be a placeholder (followed by comma, closing paren, or end of string)
            if re.search(r'\?\s*[,\)]|\?$', query):
                issues.append({
                    'file': file_path,
                    'line': content[:content.find(query)].count('\n') + 1,
                    'query': query.strip(),
                    'issue': 'SQLite placeholder (?) found - use PostgreSQL placeholder (%s)',
                    'severity': 'ERROR'
                })
            
            # Check for SQLite-specific syntax
            sqlite_patterns = [
                (r'AUTOINCREMENT', 'SQLite AUTOINCREMENT - use PostgreSQL SERIAL'),
                (r'INTEGER PRIMARY KEY', 'SQLite INTEGER PRIMARY KEY - use PostgreSQL SERIAL PRIMARY KEY'),
                (r'REAL', 'SQLite REAL - use PostgreSQL DECIMAL or NUMERIC'),
                (r'TEXT', 'SQLite TEXT - use PostgreSQL VARCHAR or TEXT'),
                (r'BLOB', 'SQLite BLOB - use PostgreSQL BYTEA'),
            ]
            
            for pattern, message in sqlite_patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    issues.append({
                        'file': file_path,
                        'line': content[:content.find(query)].count('\n') + 1,
                        'query': query.strip(),
                        'issue': message,
                        'severity': 'WARNING'
                    })
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line': 0,
            'query': '',
            'issue': f'Error reading file: {str(e)}',
            'severity': 'ERROR'
        })
    
    return issues

def main():
    """Main validation function"""
    print("Validating SQL syntax for PostgreSQL compliance...")
    
    # Find all Python files in the app directory
    app_dir = Path('app')
    python_files = list(app_dir.rglob('*.py'))
    
    all_issues = []
    
    for file_path in python_files:
        issues = validate_sql_syntax(str(file_path))
        all_issues.extend(issues)
    
    # Report results
    if all_issues:
        print(f"\nFound {len(all_issues)} SQL syntax issues:")
        print("=" * 80)
        
        for issue in all_issues:
            severity_icon = "ERROR" if issue['severity'] == 'ERROR' else "WARNING"
            print(f"{severity_icon} {issue['file']}:{issue['line']}")
            print(f"   {issue['issue']}")
            if issue['query']:
                print(f"   Query: {issue['query'][:100]}...")
            print()
        
        # Exit with error code if critical issues found
        error_count = sum(1 for issue in all_issues if issue['severity'] == 'ERROR')
        if error_count > 0:
            print(f"ERROR: {error_count} critical errors found. Fix before deployment!")
            sys.exit(1)
    else:
        print("All SQL syntax is PostgreSQL compliant!")
    
    return len(all_issues)

if __name__ == '__main__':
    main()
