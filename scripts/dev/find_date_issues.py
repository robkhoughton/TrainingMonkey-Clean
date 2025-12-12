# Create this as find_date_issues.py to audit your codebase

import os
import re


def audit_date_patterns(directory="."):
    """Audit codebase for potential date format issues"""

    # Patterns that indicate potential date format issues
    patterns = {
        "date_text_casting": r"date::text\s*=",
        "mysql_date_casting": r"DATE\(date\)",
        "string_date_splitting": r"\.split\(['\"]T['\"]\)\[0\]",
        "date_strftime": r"\.strftime\(['\"][^'\"]*['\"]\)",
        "datetime_strptime": r"datetime\.strptime\([^)]+\)",
        "date_isoformat": r"\.isoformat\(\)",
        "date_comparison": r"date\s*[><=]+\s*['\"][0-9-]+['\"]",
    }

    issues_found = {}

    # Walk through Python files
    for root, dirs, files in os.walk(directory):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.env']]

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    file_issues = []
                    for pattern_name, pattern in patterns.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            line_content = content.split('\n')[line_num - 1].strip()
                            file_issues.append({
                                'pattern': pattern_name,
                                'line': line_num,
                                'content': line_content[:100] + '...' if len(line_content) > 100 else line_content
                            })

                    if file_issues:
                        issues_found[filepath] = file_issues

                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

    return issues_found


def print_audit_results(issues):
    """Print formatted audit results"""
    print("\n🔍 DATE FORMAT AUDIT RESULTS")
    print("=" * 50)

    if not issues:
        print("✅ No obvious date format issues found!")
        return

    total_issues = sum(len(file_issues) for file_issues in issues.values())
    print(f"⚠️  Found {total_issues} potential date format issues in {len(issues)} files\n")

    for filepath, file_issues in issues.items():
        print(f"\n📁 {filepath}")
        print("-" * 40)

        for issue in file_issues:
            print(f"  Line {issue['line']:3d} | {issue['pattern']:20s} | {issue['content']}")

    print(f"\n🚨 PRIORITY ACTIONS:")
    print("1. Fix all 'date_text_casting' issues immediately (HIGH)")
    print("2. Review 'string_date_splitting' for consistency (MEDIUM)")
    print("3. Standardize 'datetime_strptime' patterns (LOW)")


if __name__ == "__main__":
    issues = audit_date_patterns()
    print_audit_results(issues)