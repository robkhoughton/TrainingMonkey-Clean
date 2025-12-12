#!/usr/bin/env python3
"""
Find unused functions in the codebase.
This script identifies functions that are defined but never called.
"""

import ast
import os
import re
from pathlib import Path
from collections import defaultdict

def get_all_python_files(directory):
    """Get all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directories
        if any(skip in root for skip in ['node_modules', '__pycache__', '.git', 'venv', 'env']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def extract_function_definitions(file_path):
    """Extract all function definitions from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if it's a method or standalone function
                parent = None
                for parent_node in ast.walk(tree):
                    if isinstance(parent_node, (ast.ClassDef, ast.FunctionDef)):
                        for child in ast.walk(parent_node):
                            if child == node and parent_node != node:
                                parent = parent_node.name if isinstance(parent_node, ast.ClassDef) else None
                                break
                        if parent:
                            break
                
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'file': file_path,
                    'parent_class': parent,
                    'is_private': node.name.startswith('_'),
                    'is_dunder': node.name.startswith('__') and node.name.endswith('__')
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'file': file_path
                })
        
        return functions, classes
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], []

def extract_function_calls(file_path):
    """Extract all function calls from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        calls = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # Method calls like obj.method()
                    calls.add(node.func.attr)
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    # Calls like module.function()
                    calls.add(f"{node.func.value.id}.{node.func.attr}")
        
        return calls
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return set()

def find_imports(file_path):
    """Find all imports to understand what functions might be called from other modules"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        imports = defaultdict(set)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports[alias.asname or alias.name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports[alias.asname or alias.name].add(f"{module}.{alias.name}")
        
        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return defaultdict(set)

def main():
    app_dir = Path('app')
    if not app_dir.exists():
        print("Error: 'app' directory not found")
        return
    
    print("Scanning codebase for unused functions...")
    print("=" * 80)
    
    # Get all Python files
    python_files = get_all_python_files('app')
    print(f"Found {len(python_files)} Python files\n")
    
    # Extract all function definitions
    all_functions = []
    all_classes = []
    for file_path in python_files:
        funcs, classes = extract_function_definitions(file_path)
        all_functions.extend(funcs)
        all_classes.extend(classes)
    
    print(f"Found {len(all_functions)} function definitions")
    print(f"Found {len(all_classes)} class definitions\n")
    
    # Extract all function calls
    all_calls = set()
    for file_path in python_files:
        calls = extract_function_calls(file_path)
        all_calls.update(calls)
    
    # Build function lookup
    function_lookup = {}
    for func in all_functions:
        key = func['name']
        if func['parent_class']:
            key = f"{func['parent_class']}.{func['name']}"
        function_lookup[key] = func
    
    # Find unused functions
    unused_functions = []
    potentially_unused = []
    
    for func in all_functions:
        func_name = func['name']
        
        # Skip special methods (dunder methods)
        if func['is_dunder']:
            continue
        
        # Skip if it's a Flask route decorator (these are called by Flask)
        if func_name.startswith('@') or 'route' in func_name.lower():
            continue
        
        # Check if function is called
        is_called = False
        
        # Check direct calls
        if func_name in all_calls:
            is_called = True
        
        # Check if it's imported and used
        for file_path in python_files:
            imports = find_imports(file_path)
            if func_name in imports.values() or any(func_name in imp for imp in imports.values()):
                # Check if it's actually used in the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple check - function name appears after import
                    if func_name in content:
                        is_called = True
                        break
        
        # Check if it's a route handler (Flask)
        if 'route' in func.get('file', '') or 'app.route' in open(func['file'], 'r', encoding='utf-8').read():
            # Check if it has @app.route decorator
            with open(func['file'], 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if i + 1 == func['line']:
                        # Check previous lines for route decorator
                        for j in range(max(0, i-5), i):
                            if '@app.route' in lines[j] or '@login_required' in lines[j] or '@csrf_protected' in lines[j]:
                                is_called = True
                                break
                        break
        
        if not is_called:
            if func['is_private']:
                potentially_unused.append(func)
            else:
                unused_functions.append(func)
    
    # Print results
    print("=" * 80)
    print("UNUSED PUBLIC FUNCTIONS (likely safe to remove):")
    print("=" * 80)
    if unused_functions:
        for func in sorted(unused_functions, key=lambda x: x['file']):
            print(f"{func['file']}:{func['line']} - {func['name']}")
            if func['parent_class']:
                print(f"  (Method of class: {func['parent_class']})")
    else:
        print("None found!")
    
    print("\n" + "=" * 80)
    print("POTENTIALLY UNUSED PRIVATE FUNCTIONS (review carefully):")
    print("=" * 80)
    if potentially_unused:
        for func in sorted(potentially_unused, key=lambda x: x['file']):
            print(f"{func['file']}:{func['line']} - {func['name']}")
            if func['parent_class']:
                print(f"  (Method of class: {func['parent_class']})")
    else:
        print("None found!")
    
    print("\n" + "=" * 80)
    print("DEPRECATED FUNCTIONS (marked for removal):")
    print("=" * 80)
    
    # Check for deprecated functions
    deprecated = []
    for file_path in python_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'deprecated' in line.lower() or 'legacy' in line.lower() or 'replaced' in line.lower():
                    # Find the function definition
                    for func in all_functions:
                        if func['file'] == file_path and abs(func['line'] - (i + 1)) < 10:
                            deprecated.append((func, line.strip()))
                            break
    
    if deprecated:
        for func, comment in deprecated:
            print(f"{func['file']}:{func['line']} - {func['name']}")
            print(f"  Comment: {comment}")
    else:
        print("None found!")

if __name__ == '__main__':
    main()

