#!/usr/bin/env python3
"""
Simple script to find potentially unused functions and deprecated code.
"""

import re
import os
from pathlib import Path

def find_function_definitions(file_path):
    """Find all function definitions in a file"""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines, 1):
            # Match function definitions
            match = re.match(r'^def\s+(\w+)\s*\(', line)
            if match:
                func_name = match.group(1)
                # Check for deprecated markers in nearby lines
                is_deprecated = False
                deprecated_reason = None
                
                # Check 5 lines before and after
                context_start = max(0, i - 6)
                context_end = min(len(lines), i + 6)
                context = ''.join(lines[context_start:context_end])
                
                if any(marker in context.lower() for marker in ['deprecated', 'legacy', 'replaced', 'superseded', 'old version', 'use instead']):
                    is_deprecated = True
                    # Try to extract reason
                    for j in range(context_start, context_end):
                        if any(marker in lines[j].lower() for marker in ['deprecated', 'legacy', 'replaced']):
                            deprecated_reason = lines[j].strip()
                            break
                
                functions.append({
                    'name': func_name,
                    'line': i,
                    'file': file_path,
                    'is_deprecated': is_deprecated,
                    'deprecated_reason': deprecated_reason
                })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return functions

def find_function_calls(file_path):
    """Find all function calls in a file"""
    calls = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple regex to find function calls (not perfect but good enough)
        # Match pattern: function_name( or module.function_name(
        pattern = r'(\w+)\s*\('
        matches = re.findall(pattern, content)
        calls.update(matches)
        
        # Also check for imports
        import_pattern = r'from\s+\S+\s+import\s+(\w+)'
        import_matches = re.findall(import_pattern, content)
        calls.update(import_matches)
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return calls

def main():
    app_dir = Path('app')
    if not app_dir.exists():
        print("Error: 'app' directory not found")
        return
    
    print("=" * 80)
    print("CODEBASE CLEANUP ANALYSIS")
    print("=" * 80)
    print()
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk('app'):
        if any(skip in root for skip in ['__pycache__', '.git']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Scanning {len(python_files)} Python files...")
    print()
    
    # Collect all functions and calls
    all_functions = {}
    all_calls = set()
    
    for file_path in python_files:
        funcs = find_function_definitions(file_path)
        for func in funcs:
            key = f"{file_path}:{func['name']}"
            all_functions[key] = func
        
        calls = find_function_calls(file_path)
        all_calls.update(calls)
    
    print(f"Found {len(all_functions)} function definitions")
    print(f"Found {len(all_calls)} unique function calls")
    print()
    
    # Find deprecated functions
    print("=" * 80)
    print("DEPRECATED FUNCTIONS (marked for removal):")
    print("=" * 80)
    deprecated = []
    for key, func in all_functions.items():
        if func['is_deprecated']:
            deprecated.append(func)
    
    if deprecated:
        for func in sorted(deprecated, key=lambda x: (x['file'], x['line'])):
            print(f"{func['file']}:{func['line']} - {func['name']}")
            if func['deprecated_reason']:
                print(f"  Reason: {func['deprecated_reason']}")
            # Check if it's called
            if func['name'] in all_calls:
                print(f"  WARNING: Still being called!")
            else:
                print(f"  Status: Not called - SAFE TO REMOVE")
            print()
    else:
        print("None found!")
    
    # Find potentially unused functions (not in calls, not deprecated, not dunder methods)
    print("=" * 80)
    print("POTENTIALLY UNUSED FUNCTIONS (review carefully):")
    print("=" * 80)
    unused = []
    for key, func in all_functions.items():
        func_name = func['name']
        # Skip dunder methods, Flask routes, and deprecated
        if (func_name.startswith('__') and func_name.endswith('__')):
            continue
        if func['is_deprecated']:
            continue
        
        # Check if it's called
        if func_name not in all_calls:
            # Check if it might be a Flask route (has @app.route decorator)
            try:
                with open(func['file'], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if func['line'] <= len(lines):
                        # Check a few lines before for decorators
                        for i in range(max(0, func['line'] - 5), func['line']):
                            if '@app.route' in lines[i] or '@login_required' in lines[i]:
                                break
                        else:
                            unused.append(func)
            except:
                unused.append(func)
    
    if unused:
        # Group by file
        by_file = {}
        for func in unused:
            if func['file'] not in by_file:
                by_file[func['file']] = []
            by_file[func['file']].append(func)
        
        for file_path in sorted(by_file.keys()):
            print(f"\n{file_path}:")
            for func in sorted(by_file[file_path], key=lambda x: x['line']):
                print(f"  Line {func['line']}: {func['name']}")
    else:
        print("None found!")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Deprecated functions: {len(deprecated)}")
    print(f"Potentially unused functions: {len(unused)}")
    print()
    print("NOTE: Review each function carefully before removing.")
    print("Some functions may be called dynamically or via imports.")

if __name__ == '__main__':
    main()

