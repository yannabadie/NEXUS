import ast
import os
from pathlib import Path
from typing import List, Dict

class ExceptionVisitor(ast.NodeVisitor):
    def __init__(self, filename: str):
        self.filename = filename
        self.silent_exceptions = []

    def visit_ExceptHandler(self, node):
        # Check if the body is empty or just 'pass'/'continue' without logging
        if not node.body:
            self.silent_exceptions.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "empty_body"
            })
            return

        is_silent = True
        for child in node.body:
            if isinstance(child, ast.Pass):
                continue
            if isinstance(child, ast.Continue):
                continue
            # If there's any other statement (logging, raising, assigning), it's arguably not "silent"
            # This is a heuristic; we might want to be stricter later.
            # For now, we look for blocks that effectively do NOTHING or just control flow without visibility.
            
            # Check for comments? AST doesn't preserve comments easily in this view.
            # We assume if there is code, it's doing something.
            
            # Simple check: if it has a function call (print, logger.error, etc) it's not silent
            if isinstance(child, ast.Expr) and isinstance(child.value, ast.Call):
                is_silent = False
                break
            
            # If it re-raises
            if isinstance(child, ast.Raise):
                is_silent = False
                break
                
            # If it assigns (maybe capturing error?) - arguably silent if not used, but let's assume it's handled
            if isinstance(child, ast.Assign) or isinstance(child, ast.AnnAssign):
                is_silent = False
                break
            
            # If it returns
            if isinstance(child, ast.Return):
                # Returns are tricky. "return None" on error is common but silent.
                # Let's flag it for review if it's just a return.
                pass 

        if is_silent:
             self.silent_exceptions.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "silent_pass_or_continue"
            })

def audit_directory(root_path: Path) -> List[Dict]:
    results = []
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(".py"):
                full_path = Path(root) / file
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=str(full_path))
                    visitor = ExceptionVisitor(str(full_path))
                    visitor.visit(tree)
                    results.extend(visitor.silent_exceptions)
                except Exception as e:
                    print(f"Error parsing {full_path}: {e}")
    return results

if __name__ == "__main__":
    root_dir = Path("core") # Focus on core for now
    print(f"Auditing {root_dir} for silent exceptions...")
    issues = audit_directory(root_dir)
    
    print(f"\nFound {len(issues)} potential silent exceptions:")
    for issue in issues:
        print(f"{issue['file']}:{issue['line']} - {issue['type']}")
    
    # Also check tests if needed, but core is priority
