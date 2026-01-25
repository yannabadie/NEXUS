"""
NCM Simple Executor - Direct Execution for P2 Stories

For simple P2 stories (dead imports, docstrings, etc.), bypass the full
OrchestratorV7 pipeline and execute directly using tools.

This avoids Hive Mind routing, timeouts, and unnecessary complexity analysis
for straightforward file operations.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import ast
import re
import subprocess
from core.logging import get_logger


class SimpleExecutor:
    """
    Direct executor for simple NCM stories.

    Handles:
    - Dead import removal (execute_dead_import_removal)
    - Docstring additions (execute_docstring_addition)
    - Type hint additions (execute_type_hint_addition)
    - Deprecation fixes (execute_deprecation_fix)

    Does NOT handle:
    - Complex refactoring (use process_turn)
    - Security fixes (use process_turn)
    - Multi-file changes (use process_turn)
    - God class refactoring (use process_turn)
    """

    def __init__(self):
        self.logger = get_logger()
        if self.logger is None:
            from core.config import Config
            from core.logging import init_logger
            config = Config()
            self.logger = init_logger(config.workspace_path, config.log_level)

    async def execute_dead_import_removal(
        self,
        file_path: Path,
        imports_to_remove: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove dead imports from a file.

        Args:
            file_path: File to modify
            imports_to_remove: List of import names to remove (e.g., ['Set', 'Dict'])

        Returns:
            (success: bool, error_message: Optional[str])

        Process:
            1. Read file content
            2. Parse AST to find import statements
            3. Remove matching imports
            4. Verify syntax is still valid
            5. Write back to file
        """
        self.logger.info("simple_executor_dead_import_start", {
            "file": str(file_path),
            "imports": imports_to_remove
        })

        try:
            # 1. Read file
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # 2. Remove imports line by line
            lines = content.split('\n')
            new_lines = []
            removed_count = 0

            for line in lines:
                should_remove = False

                # Check if this line imports any of the target names
                for import_name in imports_to_remove:
                    # Pattern: "from typing import Set, Dict, List"
                    if re.search(rf'\bimport\s+.*\b{re.escape(import_name)}\b', line):
                        # Check if this is the ONLY import on the line
                        if f"import {import_name}" in line and line.count('import') == 1:
                            # Single import, remove entire line
                            should_remove = True
                            removed_count += 1
                            self.logger.debug("removed_import_line", {
                                "line": line.strip(),
                                "import": import_name
                            })
                            break
                        else:
                            # Multiple imports on same line, just remove this one
                            # Example: "from typing import Set, Dict" -> "from typing import Dict"
                            modified_line = self._remove_import_from_line(line, import_name)
                            if modified_line != line:
                                new_lines.append(modified_line)
                                removed_count += 1
                                self.logger.debug("modified_import_line", {
                                    "before": line.strip(),
                                    "after": modified_line.strip(),
                                    "import": import_name
                                })
                                should_remove = True
                                break

                if not should_remove:
                    new_lines.append(line)

            if removed_count == 0:
                self.logger.warning("no_imports_removed", {
                    "file": str(file_path),
                    "imports": imports_to_remove
                })
                missing = [
                    name for name in imports_to_remove
                    if not re.search(rf"\\b{re.escape(name)}\\b", content)
                ]
                if missing and len(missing) == len(imports_to_remove):
                    return True, "No-op: imports already absent"
                return False, f"No imports removed (imports not found: {imports_to_remove})"

            # 3. Validate syntax
            new_content = '\n'.join(new_lines)
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                self.logger.error("syntax_error_after_removal", {
                    "file": str(file_path),
                    "error": str(e)
                })
                return False, f"Syntax error after removal: {e}"

            # 4. Write back
            file_path.write_text(new_content, encoding="utf-8")

            self.logger.info("simple_executor_dead_import_success", {
                "file": str(file_path),
                "removed_count": removed_count
            })

            return True, None

        except Exception as e:
            self.logger.error("simple_executor_dead_import_failed", {
                "file": str(file_path),
                "error": str(e)
            })
            return False, str(e)

    def _remove_import_from_line(self, line: str, import_name: str) -> str:
        """
        Remove a single import name from a line with multiple imports.

        Examples:
            "from typing import Set, Dict, List" + "Set" -> "from typing import Dict, List"
            "from typing import Set" + "Set" -> "" (will be handled by parent)
        """
        # Pattern 1: "import_name, " (not last)
        line = re.sub(rf'\b{re.escape(import_name)},\s*', '', line)

        # Pattern 2: ", import_name" (last in list)
        line = re.sub(rf',\s*\b{re.escape(import_name)}\b', '', line)

        # Pattern 3: "import_name" (only one)
        if f"import {import_name}" in line and line.count(',') == 0:
            return ""  # Remove entire line (will be caught by parent)

        return line

    async def execute_docstring_addition(
        self,
        file_path: Path,
        target_name: str,
        target_type: str = "function"
    ) -> Tuple[bool, Optional[str]]:
        """
        Add missing docstring to a function or class.

        Args:
            file_path: File to modify
            target_name: Name of function/class to add docstring to
            target_type: "function" or "class"

        Returns:
            (success: bool, error_message: Optional[str])

        Process:
            1. Read file content
            2. Parse AST to find target function/class
            3. Check if docstring already exists
            4. Add basic docstring template
            5. Write back to file
        """
        self.logger.info("simple_executor_docstring_start", {
            "file": str(file_path),
            "target": target_name,
            "type": target_type
        })

        try:
            # 1. Read file
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            content = file_path.read_text(encoding="utf-8")
            lines = content.split('\n')

            # 2. Find target definition
            target_line_idx = None
            indent_level = 0

            if target_type == "function":
                pattern = rf'^\s*def {re.escape(target_name)}\('
            else:  # class
                pattern = rf'^\s*class {re.escape(target_name)}[:\(]'

            for idx, line in enumerate(lines):
                if re.match(pattern, line):
                    target_line_idx = idx
                    # Calculate indentation
                    indent_level = len(line) - len(line.lstrip())
                    break

            if target_line_idx is None:
                return False, f"{target_type.capitalize()} '{target_name}' not found"

            # 3. Check if docstring already exists
            next_line_idx = target_line_idx + 1
            if next_line_idx < len(lines):
                next_line = lines[next_line_idx].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    return False, f"Docstring already exists for {target_name}"

            # 4. Generate docstring template
            indent = ' ' * (indent_level + 4)  # +4 for inside function/class
            if target_type == "function":
                docstring = f'{indent}"""TODO: Add function description."""'
            else:
                docstring = f'{indent}"""TODO: Add class description."""'

            # 5. Insert docstring
            lines.insert(next_line_idx, docstring)
            new_content = '\n'.join(lines)

            # 6. Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return False, f"Syntax error after adding docstring: {e}"

            # 7. Write back
            file_path.write_text(new_content, encoding="utf-8")

            self.logger.info("simple_executor_docstring_success", {
                "file": str(file_path),
                "target": target_name
            })

            return True, None

        except Exception as e:
            self.logger.error("simple_executor_docstring_failed", {
                "file": str(file_path),
                "error": str(e)
            })
            return False, str(e)

    async def execute_type_hint_addition(
        self,
        file_path: Path,
        target_name: str,
        param_name: str,
        type_hint: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Add type hint to a function parameter.

        Args:
            file_path: File to modify
            target_name: Name of function
            param_name: Parameter name to add type hint to
            type_hint: Type hint to add (e.g., "str", "int", "Optional[str]")

        Returns:
            (success: bool, error_message: Optional[str])

        Process:
            1. Read file content
            2. Find target function signature
            3. Add type hint to parameter
            4. Validate syntax
            5. Write back to file
        """
        self.logger.info("simple_executor_type_hint_start", {
            "file": str(file_path),
            "target": target_name,
            "param": param_name,
            "hint": type_hint
        })

        try:
            # 1. Read file
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            content = file_path.read_text(encoding="utf-8")

            # 2. Find and modify function signature
            # Pattern: def function_name(...param_name...)
            pattern = rf'(def {re.escape(target_name)}\([^)]*\b{re.escape(param_name)}\b)'

            # Check if type hint already exists
            existing_pattern = rf'{re.escape(param_name)}:\s*\w+'
            if re.search(existing_pattern, content):
                return False, f"Type hint already exists for parameter '{param_name}'"

            # Add type hint
            replacement = rf'\1: {type_hint}'
            new_content = re.sub(
                rf'(\bdef {re.escape(target_name)}\([^)]*)\b({re.escape(param_name)})\b',
                rf'\1\2: {type_hint}',
                content,
                count=1
            )

            if new_content == content:
                return False, f"Could not find parameter '{param_name}' in function '{target_name}'"

            # 3. Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return False, f"Syntax error after adding type hint: {e}"

            # 4. Write back
            file_path.write_text(new_content, encoding="utf-8")

            self.logger.info("simple_executor_type_hint_success", {
                "file": str(file_path),
                "target": target_name,
                "param": param_name
            })

            return True, None

        except Exception as e:
            self.logger.error("simple_executor_type_hint_failed", {
                "file": str(file_path),
                "error": str(e)
            })
            return False, str(e)

    async def execute_missing_return_type_hints(
        self,
        file_path: Path,
        targets: List[Tuple[Optional[str], str]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Add missing return type hints for functions/methods.

        Args:
            file_path: File to modify.
            targets: List of (class_name, function_name) tuples. class_name can be None.

        Returns:
            (success: bool, error_message: Optional[str])
        """
        self.logger.info("simple_executor_return_hint_start", {
            "file": str(file_path),
            "targets": targets
        })

        try:
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
            lines = content.splitlines()

            needed_typing: set[str] = set()
            updates: List[Tuple[int, str]] = []
            matched = 0
            already_annotated = 0

            target_map = {(cls, name) for cls, name in targets}
            target_names = {name for _, name in targets}

            def infer_return_type(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
                has_value = False
                has_none = False
                types: set[str] = set()
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        if child.value is None:
                            has_none = True
                            continue
                        if isinstance(child.value, ast.Constant):
                            val = child.value.value
                            if val is None:
                                has_none = True
                                continue
                            has_value = True
                            if isinstance(val, bool):
                                types.add("bool")
                            elif isinstance(val, int):
                                types.add("int")
                            elif isinstance(val, float):
                                types.add("float")
                            elif isinstance(val, str):
                                types.add("str")
                            else:
                                types.add("Any")
                        elif isinstance(child.value, (ast.List, ast.ListComp)):
                            has_value = True
                            types.add("list")
                        elif isinstance(child.value, (ast.Dict, ast.DictComp)):
                            has_value = True
                            types.add("dict")
                        elif isinstance(child.value, (ast.Set, ast.SetComp)):
                            has_value = True
                            types.add("set")
                        elif isinstance(child.value, ast.Tuple):
                            has_value = True
                            types.add("tuple")
                        else:
                            has_value = True
                            types.add("Any")
                if not has_value:
                    return "None"
                if len(types) == 1:
                    inferred = next(iter(types))
                else:
                    inferred = "Any"
                if has_none and inferred != "Any":
                    needed_typing.add("Optional")
                    return f"Optional[{inferred}]"
                return inferred

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_name = node.name
                    for child in node.body:
                        if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            continue
                        fn_name = child.name
                        if (class_name, fn_name) not in target_map:
                            continue
                        matched += 1
                        if child.returns is not None:
                            already_annotated += 1
                            continue
                        return_type = infer_return_type(child)
                        if return_type == "Any":
                            needed_typing.add("Any")
                        if return_type.startswith("Optional"):
                            needed_typing.add("Optional")
                        if child.body and child.body[0].lineno > child.lineno:
                            sig_end = child.body[0].lineno - 2
                        else:
                            sig_end = child.lineno - 1
                        line = lines[sig_end]
                        if "->" in line:
                            continue
                        if ":" not in line:
                            return False, f"Signature not found for {fn_name}"
                        before, after = line.rsplit(":", 1)
                        updates.append((sig_end, f"{before} -> {return_type}:{after}"))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if (None, node.name) not in target_map:
                        continue
                    matched += 1
                    if node.returns is not None:
                        already_annotated += 1
                        continue
                    return_type = infer_return_type(node)
                    if return_type == "Any":
                        needed_typing.add("Any")
                    if return_type.startswith("Optional"):
                        needed_typing.add("Optional")
                    if node.body and node.body[0].lineno > node.lineno:
                        sig_end = node.body[0].lineno - 2
                    else:
                        sig_end = node.lineno - 1
                    line = lines[sig_end]
                    if "->" in line:
                        continue
                    if ":" not in line:
                        return False, f"Signature not found for {node.name}"
                    before, after = line.rsplit(":", 1)
                    updates.append((sig_end, f"{before} -> {return_type}:{after}"))

            if not updates:
                if matched > 0 and matched == already_annotated:
                    return True, "No-op: return hints already present"
                if matched == 0:
                    return False, "No matching functions found for return hints"
                return False, "No return hints applied"

            for idx, updated in sorted(updates, key=lambda item: item[0]):
                lines[idx] = updated

            new_content = "\n".join(lines)
            new_content = self._ensure_typing_imports(new_content, needed_typing)

            ast.parse(new_content, filename=str(file_path))
            file_path.write_text(new_content, encoding="utf-8")

            self.logger.info("simple_executor_return_hint_success", {
                "file": str(file_path),
                "updated": len(updates)
            })
            return True, None

        except Exception as e:
            self.logger.error("simple_executor_return_hint_failed", {
                "file": str(file_path),
                "error": str(e)
            })
            return False, str(e)

    def _ensure_typing_imports(self, content: str, needed: set[str]) -> str:
        if not needed:
            return content

        lines = content.splitlines()
        import_idx = None
        existing = set()

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from typing import"):
                import_idx = idx
                parts = stripped.split("import", 1)[1]
                existing = {p.strip() for p in parts.split(",") if p.strip()}
                break

        missing = sorted(needed - existing)
        if not missing:
            return content

        if import_idx is not None:
            merged = sorted(existing | needed)
            lines[import_idx] = f"from typing import {', '.join(merged)}"
        else:
            insert_at = 0
            if lines and lines[0].startswith('"""'):
                for idx, line in enumerate(lines[1:], start=1):
                    if line.startswith('"""'):
                        insert_at = idx + 1
                        break
            for idx, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    insert_at = idx + 1
            lines.insert(insert_at, f"from typing import {', '.join(sorted(needed))}")

        return "\n".join(lines)

    async def execute_deprecation_fix(
        self,
        file_path: Path,
        deprecated_pattern: str,
        replacement: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Fix deprecation warnings by replacing old patterns with new ones.

        Args:
            file_path: File to modify
            deprecated_pattern: Deprecated code pattern (regex)
            replacement: Replacement code

        Returns:
            (success: bool, error_message: Optional[str])

        Common fixes:
            - datetime.utcnow() -> datetime.now(timezone.utc)
            - LanceDB v0.13 -> v0.16 API changes
            - Enum _generate_next_value_ signature changes

        Process:
            1. Read file content
            2. Search for deprecated pattern
            3. Replace with new pattern
            4. Validate syntax
            5. Write back to file
        """
        self.logger.info("simple_executor_deprecation_start", {
            "file": str(file_path),
            "pattern": deprecated_pattern
        })

        try:
            # 1. Read file
            if not file_path.exists():
                return False, f"File not found: {file_path}"

            content = file_path.read_text(encoding="utf-8")

            # 2. Check if pattern exists
            if not re.search(deprecated_pattern, content):
                return False, f"Deprecated pattern not found: {deprecated_pattern}"

            # 3. Replace pattern
            new_content = re.sub(deprecated_pattern, replacement, content)

            if new_content == content:
                return False, "No changes made (pattern not matched)"

            # 4. Validate syntax
            try:
                ast.parse(new_content)
            except SyntaxError as e:
                return False, f"Syntax error after deprecation fix: {e}"

            # 5. Write back
            file_path.write_text(new_content, encoding="utf-8")

            self.logger.info("simple_executor_deprecation_success", {
                "file": str(file_path),
                "replacements": new_content.count(replacement)
            })

            return True, None

        except Exception as e:
            self.logger.error("simple_executor_deprecation_failed", {
                "file": str(file_path),
                "error": str(e)
            })
            return False, str(e)

    async def run_tests(self, test_files: List[Path]) -> Tuple[bool, Optional[str]]:
        """
        Run pytest on test files.

        Args:
            test_files: List of test files to run

        Returns:
            (all_passed: bool, error_message: Optional[str])
        """
        if not test_files:
            return True, None  # No tests = pass

        for test_file in test_files:
            if not test_file.exists():
                self.logger.warning("test_file_not_found", {"file": str(test_file)})
                continue

            try:
                self.logger.debug("running_tests", {"file": str(test_file)})

                result = subprocess.run(
                    ["pytest", str(test_file), "-v", "--tb=short", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 min timeout
                )

                if result.returncode != 0:
                    error_msg = f"Tests failed in {test_file.name}"
                    self.logger.error("tests_failed", {
                        "file": str(test_file),
                        "output": result.stdout[:500]
                    })
                    return False, error_msg

                self.logger.debug("tests_passed", {"file": str(test_file)})

            except subprocess.TimeoutExpired:
                return False, f"Tests timed out: {test_file.name}"
            except Exception as e:
                return False, f"Test error: {e}"

        return True, None
