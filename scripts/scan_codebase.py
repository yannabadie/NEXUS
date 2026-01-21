"""
Comprehensive codebase scan for Phase 2B queue generation.
Scans for: missing docstrings, type hints, security issues, deprecations.
"""

import json
import re
import ast
from pathlib import Path
from datetime import datetime
from collections import defaultdict

workspace_path = Path.cwd()
stories = []
story_id = 0

def next_id():
    global story_id
    story_id += 1
    return f'P2B-{story_id:03d}'

print('=' * 60)
print('COMPREHENSIVE CODEBASE SCAN')
print('=' * 60)

# 1. MISSING DOCSTRINGS - Full scan
print('\n[1/5] Scanning for missing docstrings...')
missing_doc_by_file = defaultdict(list)

for py_file in workspace_path.glob('core/**/*.py'):
    if '__pycache__' in str(py_file) or 'test' in str(py_file).lower():
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        tree = ast.parse(content)
        rel_path = str(py_file.relative_to(workspace_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # Skip private/dunder methods
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                # Check for docstring
                if not (node.body and isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                    missing_doc_by_file[rel_path].append({
                        'name': node.name,
                        'type': 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class',
                        'line': node.lineno
                    })
    except Exception as e:
        pass

# Create stories for files with multiple missing docstrings
for file_path, missing in missing_doc_by_file.items():
    if len(missing) >= 2:  # Only if 2+ missing docstrings
        stories.append({
            'story_id': next_id(),
            'category': 'missing_doc',
            'priority': 'P2',
            'description': f'Add docstrings to {len(missing)} functions/classes in {file_path}',
            'target_file': file_path,
            'target_files': [file_path],
            'domains': ['documentation'],
            'details': [f'{m["type"]} {m["name"]} (line {m["line"]})' for m in missing[:5]]
        })

print(f'  Found {sum(len(v) for v in missing_doc_by_file.values())} missing docstrings in {len(missing_doc_by_file)} files')
print(f'  Created {len([s for s in stories if s["category"] == "missing_doc"])} stories')

# 2. TYPE HINTS - Check functions without return type hints
print('\n[2/5] Scanning for missing type hints...')
type_issues_by_file = defaultdict(list)

for py_file in workspace_path.glob('core/**/*.py'):
    if '__pycache__' in str(py_file) or 'test' in str(py_file).lower():
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        tree = ast.parse(content)
        rel_path = str(py_file.relative_to(workspace_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip private methods and __init__
                if node.name.startswith('_') and node.name != '__init__':
                    continue
                # Check for return type annotation
                if node.returns is None and node.name != '__init__':
                    type_issues_by_file[rel_path].append({
                        'name': node.name,
                        'line': node.lineno,
                        'issue': 'missing_return_type'
                    })
                # Check for parameter type annotations
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                        type_issues_by_file[rel_path].append({
                            'name': f'{node.name}.{arg.arg}',
                            'line': node.lineno,
                            'issue': 'missing_param_type'
                        })
    except:
        pass

# Create stories for files with type issues
for file_path, issues in type_issues_by_file.items():
    if len(issues) >= 3:  # Only if 3+ type issues
        stories.append({
            'story_id': next_id(),
            'category': 'type_error',
            'priority': 'P1',
            'description': f'Add type hints to {len(issues)} items in {file_path}',
            'target_file': file_path,
            'target_files': [file_path],
            'domains': ['typing'],
            'details': [f'{i["issue"]}: {i["name"]}' for i in issues[:5]]
        })

print(f'  Found {sum(len(v) for v in type_issues_by_file.values())} type issues in {len(type_issues_by_file)} files')
print(f'  Created {len([s for s in stories if s["category"] == "type_error"])} stories')

# 3. SECURITY - Check for common security issues
print('\n[3/5] Scanning for security issues...')
security_patterns = [
    (r'eval\s*\(', 'eval_usage', 'Potential code injection via eval()'),
    (r'exec\s*\(', 'exec_usage', 'Potential code injection via exec()'),
    (r'subprocess\..*shell\s*=\s*True', 'shell_injection', 'Shell injection risk'),
    (r'pickle\.load', 'pickle_load', 'Insecure deserialization'),
    (r'yaml\.load\s*\([^,]+\)', 'yaml_unsafe', 'Unsafe YAML loading'),
    (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password', 'Hardcoded password'),
    (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret', 'Hardcoded secret'),
]

security_issues = []
for py_file in workspace_path.glob('core/**/*.py'):
    if '__pycache__' in str(py_file):
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        rel_path = str(py_file.relative_to(workspace_path))

        for pattern, issue_type, description in security_patterns:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                security_issues.append({
                    'file': rel_path,
                    'line': line_num,
                    'type': issue_type,
                    'description': description
                })
    except:
        pass

# Group security issues by file
security_by_file = defaultdict(list)
for issue in security_issues:
    security_by_file[issue['file']].append(issue)

for file_path, issues in security_by_file.items():
    stories.append({
        'story_id': next_id(),
        'category': 'security',
        'priority': 'P0',
        'description': f'Fix {len(issues)} security issue(s) in {file_path}',
        'target_file': file_path,
        'target_files': [file_path],
        'domains': ['security'],
        'details': [f'Line {i["line"]}: {i["description"]}' for i in issues]
    })

print(f'  Found {len(security_issues)} security issues in {len(security_by_file)} files')
print(f'  Created {len([s for s in stories if s["category"] == "security"])} stories')

# 4. DEPRECATION - Check for deprecated patterns
print('\n[4/5] Scanning for deprecation warnings...')
deprecation_patterns = [
    (r'datetime\.utcnow\(\)', 'datetime_utcnow', 'Use datetime.now(timezone.utc) instead'),
    (r'datetime\.utcfromtimestamp', 'datetime_utcfromtimestamp', 'Use datetime.fromtimestamp(ts, tz=timezone.utc)'),
    (r'asyncio\.get_event_loop\(\)', 'asyncio_get_event_loop', 'Use asyncio.get_running_loop() in async context'),
]

deprecation_issues = []
for py_file in workspace_path.glob('core/**/*.py'):
    if '__pycache__' in str(py_file):
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        rel_path = str(py_file.relative_to(workspace_path))

        for pattern, issue_type, description in deprecation_patterns:
            matches = list(re.finditer(pattern, content))
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                deprecation_issues.append({
                    'file': rel_path,
                    'line': line_num,
                    'type': issue_type,
                    'description': description
                })
    except:
        pass

# Group by file
deprecation_by_file = defaultdict(list)
for issue in deprecation_issues:
    deprecation_by_file[issue['file']].append(issue)

for file_path, issues in deprecation_by_file.items():
    stories.append({
        'story_id': next_id(),
        'category': 'deprecation',
        'priority': 'P2',
        'description': f'Fix {len(issues)} deprecation(s) in {file_path}',
        'target_file': file_path,
        'target_files': [file_path],
        'domains': ['modernization'],
        'details': [f'Line {i["line"]}: {i["description"]}' for i in issues]
    })

print(f'  Found {len(deprecation_issues)} deprecation issues in {len(deprecation_by_file)} files')
print(f'  Created {len([s for s in stories if s["category"] == "deprecation"])} stories')

# 5. COMPLEXITY - Check for large functions
print('\n[5/5] Scanning for complex functions...')
complex_functions = []

for py_file in workspace_path.glob('core/**/*.py'):
    if '__pycache__' in str(py_file):
        continue
    try:
        content = py_file.read_text(encoding='utf-8')
        tree = ast.parse(content)
        rel_path = str(py_file.relative_to(workspace_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count lines
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    lines = node.end_lineno - node.lineno
                    if lines > 50:  # Functions over 50 lines
                        complex_functions.append({
                            'file': rel_path,
                            'name': node.name,
                            'line': node.lineno,
                            'length': lines
                        })
    except:
        pass

# Group by file
complex_by_file = defaultdict(list)
for func in complex_functions:
    complex_by_file[func['file']].append(func)

for file_path, funcs in complex_by_file.items():
    stories.append({
        'story_id': next_id(),
        'category': 'refactoring',
        'priority': 'P2',
        'description': f'Refactor {len(funcs)} complex function(s) in {file_path}',
        'target_file': file_path,
        'target_files': [file_path],
        'domains': ['refactoring'],
        'details': [f'{f["name"]} ({f["length"]} lines)' for f in funcs]
    })

print(f'  Found {len(complex_functions)} complex functions in {len(complex_by_file)} files')
print(f'  Created {len([s for s in stories if s["category"] == "refactoring"])} stories')

# SUMMARY
print('\n' + '=' * 60)
print('SCAN COMPLETE')
print('=' * 60)

by_category = defaultdict(int)
for s in stories:
    by_category[s['category']] += 1

print(f'\nTotal stories: {len(stories)}')
print('By category:')
for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {count}')

# Save
output_path = workspace_path / 'workspace/ncm/phase2b_stories.json'
output_data = {
    'generated_at': datetime.now().isoformat(),
    'total_stories': len(stories),
    'by_category': dict(by_category),
    'stories': stories
}
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2)

print(f'\nSaved to: {output_path}')
