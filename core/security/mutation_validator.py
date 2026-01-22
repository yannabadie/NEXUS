"""
MutationValidator - Behavioral analysis of mutation code.

Mode: WARN + CONTINUE (never blocks, only logs warnings)

This validator uses AST analysis to detect potentially dangerous patterns
in mutation code, but follows the user's decision to WARN rather than BLOCK.

Special handling:
- open(): Allowed if workspace-relative path
- os/subprocess: Warning only (agents may have legitimate uses)
"""

import ast
import re
import signal
from pathlib import Path
from typing import List, Tuple, Optional


class MutationValidator:
    """Validates mutation code - warning mode (never blocks)."""

    # Security limits to prevent DoS attacks
    MAX_CODE_SIZE = 100_000  # Maximum code size in characters
    MAX_REGEX_TIME = 1.0  # Maximum time allowed for regex matching in seconds
    MAX_RECURSION_DEPTH = 50  # Maximum recursion depth for AST analysis

    # Imports potentiellement dangereux (WARNING seulement)
    SUSPICIOUS_IMPORTS = {
        'os', 'subprocess', 'shutil', 'sys',
        'socket', 'requests', 'urllib',
        'pickle', 'marshal',
        'ctypes', 'multiprocessing',
    }

    # Fonctions suspectes (WARNING seulement)
    SUSPICIOUS_CALLS = {
        'exec', 'eval', 'compile', '__import__',
        'system', 'popen', 'spawn',
        'remove', 'rmdir', 'unlink', 'rmtree',
        'chmod', 'chown',
    }

    # Patterns regex suspects dans le code
    SUSPICIOUS_PATTERNS = [
        (r'os\.system\s*\(', "os.system() - command execution"),
        (r'subprocess\.(run|call|Popen|check_output)', "subprocess execution"),
        (r'shutil\.(rmtree|move|copy)', "shutil file operation"),
        (r'__import__\s*\(', "dynamic import"),
        (r'\bexec\s*\(', "exec() - arbitrary code execution"),
        (r'\beval\s*\(', "eval() - arbitrary code execution"),
        (r'os\.(remove|unlink|rmdir)', "os file deletion"),
        (r'Path\([^)]{0,100}\)\.unlink', "pathlib file deletion"),  # Limit path length to prevent ReDoS
        (r'\.write\s*\([^)]{0,50}\.\.[^)]{0,50}\)', "write with parent path"),  # Limit path length to prevent ReDoS
    ]

    def __init__(self, workspace_path: Optional[Path] = None):
        """
        Initialize MutationValidator.

        Args:
            workspace_path: Optional workspace path for relative path analysis
        """
        self.workspace_path = workspace_path

    def _validate_code_size(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code size to prevent DoS attacks.

        Returns:
            (is_valid, error_message)
        """
        if len(code) > self.MAX_CODE_SIZE:
            return False, f"Code size exceeds maximum allowed limit ({self.MAX_CODE_SIZE} characters)"
        return True, None

    def _regex_search_with_timeout(self, pattern: str, text: str, timeout: float = MAX_REGEX_TIME) -> Optional[re.Match]:
        """
        Perform regex search with timeout protection to prevent ReDoS attacks.
        Uses signal-based timeout on Unix-like systems and length limits on all systems.

        Returns:
            Match object if pattern matches, None otherwise or on error/timeout
        """
        # Limit text length for regex matching to prevent catastrophic backtracking
        if len(text) > self.MAX_CODE_SIZE:
            return None

        # Use a reasonable recursion limit to prevent stack overflow
        import sys
        old_limit = sys.getrecursionlimit()

        try:
            # Only reduce if current limit is too high
            target_limit = max(1000, self.MAX_RECURSION_DEPTH * 10)
            if old_limit > target_limit:
                sys.setrecursionlimit(target_limit)

            # For platforms that support it (Unix-like), use signal-based timeout
            # Windows doesn't have signal.SIGALRM, so we only enable this on Unix
            use_signal_timeout = hasattr(signal, 'SIGALRM')
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Regex pattern took too long to execute")

            if use_signal_timeout:
                # Set up signal handler for timeout
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))  # Set alarm for timeout seconds

            try:
                result = re.search(pattern, text, re.IGNORECASE)
                
                if use_signal_timeout:
                    # Cancel the alarm if we completed successfully
                    signal.alarm(0)
                    # Restore old signal handler
                    signal.signal(signal.SIGALRM, old_handler)
                
                return result
                
            except TimeoutError:
                # Regex took too long, treat as no match for security
                return None
            except (MemoryError, RecursionError):
                # If regex fails due to recursion/stack limits, treat as no match
                return None
            except Exception:
                # Any other error, treat as no match
                return None
                
        finally:
            # Always restore recursion limit
            try:
                sys.setrecursionlimit(old_limit)
            except:
                pass

    def validate(
        self,
        code: str,
        target_file: str
    ) -> Tuple[List[str], List[str]]:
        """
        Validate mutation code for suspicious patterns.

        Args:
            code: The Python code to validate
            target_file: The target file path (for context)

        Returns:
            (warnings, info_messages)
            - warnings: List of warning messages for suspicious patterns
            - info: List of informational messages (e.g., open() allowed)

        NOTE: This method NEVER blocks. It returns warnings for human review,
        but the mutation is always applied (user's choice: "Avertir + continuer").
        """
        warnings: List[str] = []
        info: List[str] = []

        # 0. Validate code size
        size_valid, size_error = self._validate_code_size(code)
        if not size_valid:
            warnings.append(f"SECURITY: {size_error}")
            return warnings, info

        # 1. Analyse statique par regex (rapide, catch-all)
        for pattern, description in self.SUSPICIOUS_PATTERNS:
            if self._regex_search_with_timeout(pattern, code):
                warnings.append(f"Pattern suspect: {description}")

        # 2. Analyse AST (plus précise)
        try:
            tree = ast.parse(code)
            ast_warnings, ast_info = self._analyze_ast(tree)
            warnings.extend(ast_warnings)
            info.extend(ast_info)

        except SyntaxError as e:
            # Expected for indented code snippets (class methods, etc.)
            # The actual syntax validation happens in repl.py after block insertion
            # This is NOT an error - just info that AST analysis couldn't be performed
            info.append(f"AST analysis skipped (expected for indented code snippets): {e.msg}")

        # 3. Dédupliquer les warnings
        warnings = list(dict.fromkeys(warnings))
        info = list(dict.fromkeys(info))

        return warnings, info

    def _analyze_ast(self, tree: ast.AST) -> Tuple[List[str], List[str]]:
        """
        Analyze AST for suspicious patterns.

        Returns:
            (warnings, info)
        """
        warnings: List[str] = []
        info: List[str] = []

        for node in ast.walk(tree):
            # Vérifier imports suspects
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_root = alias.name.split('.')[0]
                    if module_root in self.SUSPICIOUS_IMPORTS:
                        warnings.append(f"Import suspect: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_root = node.module.split('.')[0]
                    if module_root in self.SUSPICIOUS_IMPORTS:
                        warnings.append(f"Import from suspect: {node.module}")

            # Vérifier appels de fonctions
            elif isinstance(node, ast.Call):
                func_name = self._get_func_name(node)

                if not func_name:
                    continue

                # Cas spécial: open() - autoriser si workspace-relative
                if func_name == 'open':
                    path_arg = self._extract_first_string_arg(node)
                    if path_arg:
                        if self._is_parent_or_absolute_path(path_arg):
                            warnings.append(
                                f"open() avec chemin parent/absolu: {path_arg}"
                            )
                        else:
                            info.append(
                                f"open() autorisé (workspace-relative): {path_arg}"
                            )
                    else:
                        info.append("open() avec chemin dynamique (non analysable)")

                # Autres fonctions suspectes
                elif func_name in self.SUSPICIOUS_CALLS:
                    warnings.append(f"Appel suspect: {func_name}()")

                # Méthodes suspectes sur objets
                elif isinstance(node.func, ast.Attribute):
                    method_name = node.func.attr
                    if method_name in self.SUSPICIOUS_CALLS:
                        warnings.append(f"Méthode suspecte: .{method_name}()")

        return warnings, info

    def _get_func_name(self, node: ast.Call) -> str:
        """Extract function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _extract_first_string_arg(self, node: ast.Call) -> str:
        """Extract the first string argument from a call (for open() analysis)."""
        if node.args:
            first_arg = node.args[0]
            # Python 3.8+ uses ast.Constant
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                return first_arg.value
            # Older Python uses ast.Str
            elif hasattr(ast, 'Str') and isinstance(first_arg, ast.Str):
                return first_arg.s
        return ""

    def _is_parent_or_absolute_path(self, path: str) -> bool:
        """Check if a path references parent directory or is absolute."""
        if not path:
            return False

        # Absolute paths (Unix and Windows)
        # Check Unix absolute paths
        if path.startswith('/'):
            return True
        
        # Check Windows absolute paths (C:, D:, etc.)
        # Use safer check to avoid IndexError on short strings
        if len(path) >= 2 and path[0].isalpha() and path[1] == ':':
            return True

        # Normalize path to handle various separators and encodings
        # Replace backslashes with forward slashes for consistent checking
        normalized_path = path.replace('\\', '/')
        
        # Check for parent directory references in normalized path
        # More robust check that handles various bypass attempts
        path_parts = normalized_path.split('/')
        for part in path_parts:
            # Check for .. and variations that could be used to bypass
            if part == '..' or part.startswith('..\\') or part.startswith('../'):
                return True
            # Check for encoded or obfuscated .. attempts
            if part.startswith('..') and len(part) > 2:
                # Pattern matches .. followed by anything (e.g., .../, ..foo/)
                return True

        # Additional check for parent references using both slash types
        if '/../' in normalized_path or '\\..\\' in path:
            return True
        if normalized_path.endswith('/..') or path.endswith('\\..\\'):
            return True

        return False

    def format_report(
        self,
        warnings: List[str],
        info: List[str],
        target_file: str
    ) -> str:
        """
        Format a human-readable report.

        Args:
            warnings: List of warnings
            info: List of info messages
            target_file: The target file for context

        Returns:
            Formatted string report
        """
        lines = []

        if warnings:
            lines.append(f"MUTATION WARNINGS for {target_file}:")
            for w in warnings:
                lines.append(f"  {w}")
            lines.append("  (Applying anyway - review the code)")

        if info:
            lines.append(f"Info for {target_file}:")
            for i in info:
                lines.append(f"  {i}")

        return "\n".join(lines) if lines else ""
