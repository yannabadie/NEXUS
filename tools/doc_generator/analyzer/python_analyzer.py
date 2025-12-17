# NEXUS Documentation Generator - Python Analyzer
"""
Analyzes Python files using the ast module.
"""

import ast
from pathlib import Path
from typing import Optional

from ..config import (
    DocGeneratorConfig,
    ModuleInfo,
    ClassInfo,
    FunctionInfo,
    ImportInfo,
    CallInfo,
)


class PythonAnalyzer:
    """Analyzes Python files using AST."""

    def __init__(self, config: DocGeneratorConfig):
        self.config = config
        self.repo_root = config.repo_root

    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """
        Analyze a Python file and extract all information.

        Args:
            file_path: Path to the Python file

        Returns:
            ModuleInfo with all extracted information
        """
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = file_path.read_text(encoding="latin-1")

        tree = ast.parse(source, filename=str(file_path))

        # Get module docstring
        docstring = ast.get_docstring(tree)

        # Extract components
        classes = self._extract_classes(tree)
        functions = self._extract_functions(tree)
        imports = self._extract_imports(tree)
        calls = self._extract_calls(tree)  # V13.0: INTERACTION MATRIX

        # Count lines
        loc = len(source.splitlines())

        # Get relative path for display
        try:
            rel_path = file_path.relative_to(self.repo_root)
        except ValueError:
            rel_path = file_path

        return ModuleInfo(
            path=rel_path,
            name=file_path.stem,
            docstring=docstring,
            classes=classes,
            functions=functions,
            imports=imports,
            calls=calls,
            loc=loc,
        )

    def _extract_classes(self, tree: ast.AST) -> list[ClassInfo]:
        """Extract all class definitions."""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                classes.append(class_info)

        return classes

    def _analyze_class(self, node: ast.ClassDef) -> ClassInfo:
        """Analyze a class definition."""
        # Get docstring
        docstring = ast.get_docstring(node)

        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attribute_name(base)}")

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        # Get methods
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                method_info = self._analyze_function(item)
                methods.append(method_info)

        # Get class attributes
        attributes = self._extract_class_attributes(node)

        return ClassInfo(
            name=node.name,
            docstring=docstring,
            methods=methods,
            attributes=attributes,
            bases=bases,
            decorators=decorators,
            line=node.lineno,
        )

    def _extract_functions(self, tree: ast.AST) -> list[FunctionInfo]:
        """Extract top-level function definitions."""
        functions = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                func_info = self._analyze_function(node)
                functions.append(func_info)

        return functions

    def _analyze_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        """Analyze a function definition."""
        docstring = ast.get_docstring(node)

        # Build signature
        signature = self._build_signature(node)

        # Get decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        is_async = isinstance(node, ast.AsyncFunctionDef)

        return FunctionInfo(
            name=node.name,
            signature=signature,
            docstring=docstring,
            decorators=decorators,
            line=node.lineno,
            is_async=is_async,
        )

    def _build_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Build function signature string."""
        args = node.args

        # Collect all arguments
        params = []

        # Positional-only args (before /)
        for arg in args.posonlyargs:
            params.append(self._format_arg(arg))

        # Regular args
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        for i, arg in enumerate(args.args):
            default_index = i - (num_args - num_defaults)
            if default_index >= 0:
                default = args.defaults[default_index]
                params.append(f"{self._format_arg(arg)}=...")
            else:
                params.append(self._format_arg(arg))

        # *args
        if args.vararg:
            params.append(f"*{args.vararg.arg}")

        # Keyword-only args
        num_kw_defaults = len(args.kw_defaults)
        for i, arg in enumerate(args.kwonlyargs):
            if args.kw_defaults[i] is not None:
                params.append(f"{self._format_arg(arg)}=...")
            else:
                params.append(self._format_arg(arg))

        # **kwargs
        if args.kwarg:
            params.append(f"**{args.kwarg.arg}")

        # Return annotation
        return_type = ""
        if node.returns:
            return_type = f" -> {self._get_annotation_name(node.returns)}"

        return f"{node.name}({', '.join(params)}){return_type}"

    def _format_arg(self, arg: ast.arg) -> str:
        """Format a function argument."""
        if arg.annotation:
            return f"{arg.arg}: {self._get_annotation_name(arg.annotation)}"
        return arg.arg

    def _get_annotation_name(self, node: ast.expr) -> str:
        """Get string representation of a type annotation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation_name(node.value)
            slice_val = self._get_annotation_name(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation_name(e) for e in node.elts]
            return ", ".join(elements)
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.BinOp):
            # Union type with | operator
            left = self._get_annotation_name(node.left)
            right = self._get_annotation_name(node.right)
            return f"{left} | {right}"
        return "..."

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., 'module.Class')."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return self._get_attribute_name(node.func)
        return "unknown"

    def _extract_class_attributes(self, node: ast.ClassDef) -> list[dict]:
        """Extract class attributes from __init__ and class body."""
        attributes = []
        seen = set()

        # Class-level attributes
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                name = item.target.id
                if name not in seen:
                    seen.add(name)
                    annotation = self._get_annotation_name(item.annotation) if item.annotation else None
                    attributes.append({
                        "name": name,
                        "type": annotation,
                        "visibility": "+" if not name.startswith("_") else "-",
                    })
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if name not in seen:
                            seen.add(name)
                            attributes.append({
                                "name": name,
                                "type": None,
                                "visibility": "+" if not name.startswith("_") else "-",
                            })

        # Instance attributes from __init__
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                for stmt in ast.walk(item):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Attribute):
                                if isinstance(target.value, ast.Name) and target.value.id == "self":
                                    name = target.attr
                                    if name not in seen:
                                        seen.add(name)
                                        attributes.append({
                                            "name": name,
                                            "type": None,
                                            "visibility": "+" if not name.startswith("_") else "-",
                                        })

        return attributes

    def _extract_imports(self, tree: ast.AST) -> list[ImportInfo]:
        """Extract all import statements."""
        imports = []

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        names=[alias.asname or alias.name],
                        is_from=False,
                        line=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        module=node.module,
                        names=names,
                        is_from=True,
                        line=node.lineno,
                    ))

        return imports

    def _extract_calls(self, tree: ast.AST) -> list[CallInfo]:
        """
        Extract function/method calls for INTERACTION MATRIX (V13.0).

        Walks the AST to find all Call nodes and determines:
        - caller: The enclosing function/method
        - callee: The function/method being called
        - is_method: Whether it's a method call (obj.method())
        """
        calls = []

        # Build a map of function/method nodes to their names
        def get_caller_name(node: ast.AST) -> str:
            """Walk up to find enclosing function/class context."""
            for parent in ast.walk(tree):
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for child in ast.walk(parent):
                        if child is node:
                            return parent.name
                elif isinstance(parent, ast.ClassDef):
                    for child in ast.walk(parent):
                        if child is node:
                            return f"{parent.name}.<class>"
            return "<module>"

        # Visit all Call nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                callee_name = None
                is_method = False
                callee_module = None

                # Determine callee name
                if isinstance(node.func, ast.Name):
                    # Direct function call: foo()
                    callee_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # Method/attribute call: obj.method() or module.func()
                    callee_name = node.func.attr
                    is_method = True
                    # Try to get the object/module name
                    if isinstance(node.func.value, ast.Name):
                        callee_module = node.func.value.id
                    elif isinstance(node.func.value, ast.Attribute):
                        callee_module = self._get_attribute_name(node.func.value)

                if callee_name:
                    # Find the caller context
                    caller = self._find_caller_context(tree, node)

                    calls.append(CallInfo(
                        caller=caller,
                        callee=callee_name,
                        callee_module=callee_module,
                        line=node.lineno,
                        is_method=is_method,
                    ))

        return calls

    def _find_caller_context(self, tree: ast.AST, target_node: ast.AST) -> str:
        """Find the enclosing function/method/class for a node."""
        # This is a simplified approach - walk through function/class defs
        # and check if the target node is within their body

        class CallerFinder(ast.NodeVisitor):
            def __init__(self):
                self.context_stack = []
                self.found_context = "<module>"
                self.target_line = target_node.lineno

            def visit_ClassDef(self, node):
                self.context_stack.append(node.name)
                self.generic_visit(node)
                self.context_stack.pop()

            def visit_FunctionDef(self, node):
                self._visit_function(node)

            def visit_AsyncFunctionDef(self, node):
                self._visit_function(node)

            def _visit_function(self, node):
                if self.context_stack:
                    full_name = f"{'.'.join(self.context_stack)}.{node.name}"
                else:
                    full_name = node.name

                self.context_stack.append(node.name)

                # Check if target is in this function's range
                if hasattr(node, 'end_lineno'):
                    if node.lineno <= self.target_line <= node.end_lineno:
                        self.found_context = full_name
                else:
                    # Fallback: check if line is after function start
                    if node.lineno <= self.target_line:
                        self.found_context = full_name

                self.generic_visit(node)
                self.context_stack.pop()

        finder = CallerFinder()
        finder.visit(tree)
        return finder.found_context

    def get_public_api(self, module: ModuleInfo) -> dict:
        """
        Extract the public API of a module.

        Returns dict with 'classes' and 'functions' keys.
        """
        public_classes = [
            c for c in module.classes
            if not c.name.startswith("_")
        ]
        public_functions = [
            f for f in module.functions
            if not f.name.startswith("_")
        ]

        return {
            "classes": public_classes,
            "functions": public_functions,
        }

    def get_docstring_summary(self, docstring: Optional[str]) -> str:
        """Get first line of docstring as summary."""
        if not docstring:
            return ""

        lines = docstring.strip().split("\n")
        if lines:
            return lines[0].strip()
        return ""
