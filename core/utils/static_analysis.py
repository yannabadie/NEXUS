
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass, field

@dataclass
class Issue:
    file: str
    line: int
    type: str
    message: str
    severity: str = "WARNING"

class StaticAnalyzer(ast.NodeVisitor):
    def __init__(self, filename: str, content: str):
        self.filename = filename
        self.content = content
        self.issues: List[Issue] = []
        self.imports: List[str] = []
        self.function_complexity: Dict[str, int] = {}
        
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Check argument count
        arg_count = len(node.args.args)
        if arg_count > 5:
            self.issues.append(Issue(
                file=self.filename,
                line=node.lineno,
                type="complexity",
                message=f"Function '{node.name}' has {arg_count} arguments (max 5)",
                severity="INFO"
            ))
            
        # Check function length (heuristic)
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        length = end_line - start_line
        if length > 50:
             self.issues.append(Issue(
                file=self.filename,
                line=node.lineno,
                type="complexity",
                message=f"Function '{node.name}' is {length} lines long (max 50)",
                severity="INFO"
            ))
            
        # Check for async blocking I/O (heuristic)
        if isinstance(node, ast.AsyncFunctionDef):
            self._check_async_blocking(node)
            
        self.generic_visit(node)
        
    def _check_async_blocking(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    # Check for time.sleep
                    if child.func.attr == 'sleep' and isinstance(child.func.value, ast.Name) and child.func.value.id == 'time':
                         self.issues.append(Issue(
                            file=self.filename,
                            line=child.lineno,
                            type="blocking_io",
                            message="Blocking time.sleep() called in async function",
                            severity="ERROR"
                        ))
                    # Check for subprocess.run/call without async
                    if child.func.attr in ('run', 'call', 'Popen') and isinstance(child.func.value, ast.Name) and child.func.value.id == 'subprocess':
                         self.issues.append(Issue(
                            file=self.filename,
                            line=child.lineno,
                            type="blocking_io",
                            message=f"Blocking subprocess.{child.func.attr}() called in async function",
                            severity="WARNING"
                        ))

def scan_file(filepath: Path) -> Tuple[List[Issue], List[str]]:
    issues = []
    imports = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 1. AST Analysis
        try:
            tree = ast.parse(content, filename=str(filepath))
            analyzer = StaticAnalyzer(str(filepath), content)
            analyzer.visit(tree)
            issues.extend(analyzer.issues)
            imports.extend(analyzer.imports)
        except SyntaxError as e:
            issues.append(Issue(str(filepath), e.lineno, "syntax_error", str(e), "ERROR"))
            
        # 2. Regex Analysis
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            # Check for TODOs/FIXMEs
            if "TODO" in line:
                issues.append(Issue(str(filepath), i, "todo", "TODO found", "INFO"))
            if "FIXME" in line:
                issues.append(Issue(str(filepath), i, "fixme", "FIXME found", "WARNING"))
                
            # Check for hardcoded secrets (Basic)
            if "API_KEY" in line and "=" in line and "os.getenv" not in line and "environ" not in line:
                 # Exclude tests and examples
                 if "test" not in str(filepath).lower() and "example" not in str(filepath).lower():
                    issues.append(Issue(str(filepath), i, "security", "Potential hardcoded API Key", "CRITICAL"))
                    
        # 3. File Level Checks
        if len(lines) > 500:
            issues.append(Issue(str(filepath), 1, "complexity", f"File is {len(lines)} lines long (max 500)", "INFO"))
            
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
        
    return issues, imports

def analyze_directory(root_path: Path):
    all_issues = []
    import_graph = {} # file -> list of imports
    
    print(f"Scanning {root_path}...")
    
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                rel_path = full_path.relative_to(root_path)
                
                file_issues, file_imports = scan_file(full_path)
                all_issues.extend(file_issues)
                
                # Normalize imports for graph (simplified)
                # We map "core.utils" -> "core/utils.py" or "core/utils/__init__.py" logic roughly
                # For now, just store the raw import string
                import_graph[str(rel_path)] = file_imports

    # Report
    print(f"\n=== Static Analysis Report ===")
    print(f"Total Files Scanned: {len(import_graph)}")
    print(f"Total Issues Found: {len(all_issues)}\n")
    
    # Group by severity
    by_severity = {}
    for issue in all_issues:
        by_severity.setdefault(issue.severity, []).append(issue)
        
    for sev in ["CRITICAL", "ERROR", "WARNING", "INFO"]:
        if sev in by_severity:
            print(f"--- {sev} ({len(by_severity[sev])}) ---")
            for issue in by_severity[sev][:10]: # Show top 10
                print(f"{issue.file}:{issue.line} - {issue.message}")
            if len(by_severity[sev]) > 10:
                print(f"... and {len(by_severity[sev]) - 10} more")
            print()

if __name__ == "__main__":
    root_dir = Path("core")
    analyze_directory(root_dir)
