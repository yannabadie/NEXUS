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
    - Dead import removal
    - Simple docstring additions
    - Dead code removal (with caution)

    Does NOT handle:
    - Complex refactoring
    - Security fixes
    - Multi-file changes
    """

    def __init__(self):
        self.logger = get_logger()

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
