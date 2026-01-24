"""
NCM Real Story Generator - Generate stories from actual codebase analysis.

Analyzes the NEXUS codebase to find real issues and generates NCM stories:
- Dead imports (autoflake)
- Missing docstrings (AST analysis)
- Missing type hints (AST analysis)
- Deprecation warnings (static analysis)
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple
import subprocess

from core.ncm.models import Story, StoryPriority, IssueDomain


class RealStoryGenerator:
    """Generate stories from real codebase issues."""

    def __init__(self, workspace_path: Path):
        # workspace_path from REPL context points to workspace/ subfolder
        # We need to analyze core/ which is at project root (parent of workspace/)
        if workspace_path.name == "workspace":
            self.project_root = workspace_path.parent
        else:
            self.project_root = workspace_path

        self.workspace_path = self.project_root
        self.core_path = self.project_root / "core"

    def generate_dead_import_stories(self, limit: int = 50) -> List[Story]:
        """
        Generate stories for dead imports using autoflake analysis.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for dead import removal
        """
        stories = []

        # Run autoflake to find dead imports
        try:
            result = subprocess.run(
                ["python", "-m", "autoflake", "--check", "--recursive", str(self.core_path)],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse autoflake output
            # Format: "file.py:10: Remove unused import: 'Dict'"
            for line in result.stdout.split('\n'):
                if "Remove unused import" in line or "would remove unused import" in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        file_path = parts[0].strip()
                        line_num = parts[1].strip()
                        import_match = re.search(r"['\"]([^'\"]+)['\"]", parts[2])

                        if import_match:
                            import_name = import_match.group(1)
                            rel_path = Path(file_path).relative_to(self.workspace_path)

                            story = Story(
                                story_id=f"REAL-IMPORT-{len(stories) + 1:03d}",
                                priority=StoryPriority.P2,
                                domains={IssueDomain.CLEANUP},
                                description=f"Remove dead import '{import_name}' from {rel_path}\n\nIssue:\nImport '{import_name}' may be unused on line {line_num}",
                                target_files=[Path(file_path)],
                                test_files=[],
                            )
                            stories.append(story)

                            if len(stories) >= limit:
                                break

        except subprocess.TimeoutExpired:
            print("Warning: autoflake analysis timed out")
        except FileNotFoundError:
            print("Warning: autoflake not installed, skipping dead import analysis")

        return stories

    def generate_missing_docstring_stories(self, limit: int = 50) -> List[Story]:
        """
        Generate stories for missing docstrings using AST analysis.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for docstring addition
        """
        stories = []

        # Walk through Python files
        for py_file in self.core_path.rglob("*.py"):
            if len(stories) >= limit:
                break

            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if len(stories) >= limit:
                        break

                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        # Skip private functions (start with _)
                        if node.name.startswith('_'):
                            continue

                        # Check if docstring exists
                        if not ast.get_docstring(node):
                            node_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                            rel_path = py_file.relative_to(self.workspace_path)

                            story = Story(
                                story_id=f"REAL-DOC-{len(stories) + 1:03d}",
                                priority=StoryPriority.P2,
                                domains={IssueDomain.DOCUMENTATION},
                                description=f"Add docstring to {node_type} '{node.name}' in {rel_path}\n\nIssue:\n{node_type.capitalize()} '{node.name}' is missing docstring (line {node.lineno})",
                                target_files=[py_file],
                                test_files=[],
                            )
                            stories.append(story)

            except Exception as e:
                # Skip files with parse errors
                continue

        return stories

    def generate_type_hint_stories(self, limit: int = 50) -> List[Story]:
        """
        Generate stories for missing type hints using AST analysis.

        Args:
            limit: Maximum number of stories to generate

        Returns:
            List of Story objects for type hint addition
        """
        stories = []

        # Walk through Python files
        for py_file in self.core_path.rglob("*.py"):
            if len(stories) >= limit:
                break

            try:
                content = py_file.read_text(encoding='utf-8')
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if len(stories) >= limit:
                        break

                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Skip private functions
                        if node.name.startswith('_'):
                            continue

                        # Check parameters for missing type hints
                        for arg in node.args.args:
                            if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                                rel_path = py_file.relative_to(self.workspace_path)

                                # Suggest type hint based on parameter name
                                suggested_type = self._suggest_type_hint(arg.arg)

                                story = Story(
                                    story_id=f"REAL-TYPE-{len(stories) + 1:03d}",
                                    priority=StoryPriority.P2,
                                    domains={IssueDomain.TYPING},
                                    description=f"Add type hint '{suggested_type}' to parameter '{arg.arg}' in function '{node.name}' in {rel_path}\n\nIssue:\nParameter '{arg.arg}' in function '{node.name}' is missing type hint (line {node.lineno})",
                                    target_files=[py_file],
                                    test_files=[],
                                )
                                stories.append(story)

                                if len(stories) >= limit:
                                    break

            except Exception as e:
                # Skip files with parse errors
                continue

        return stories

    def _suggest_type_hint(self, param_name: str) -> str:
        """
        Suggest type hint based on parameter name.

        Args:
            param_name: Parameter name to analyze

        Returns:
            Suggested type hint string
        """
        # Common patterns
        if 'path' in param_name.lower():
            return 'Path'
        elif 'file' in param_name.lower():
            return 'str'
        elif 'id' in param_name.lower():
            return 'str'
        elif 'count' in param_name.lower() or 'num' in param_name.lower():
            return 'int'
        elif 'name' in param_name.lower():
            return 'str'
        elif 'message' in param_name.lower() or 'text' in param_name.lower():
            return 'str'
        elif 'flag' in param_name.lower() or 'is_' in param_name.lower():
            return 'bool'
        elif 'data' in param_name.lower() or 'config' in param_name.lower():
            return 'Dict'
        elif 'items' in param_name.lower() or 'list' in param_name.lower():
            return 'List'
        else:
            return 'Any'  # Default

    def generate_mixed_stories(self, count: int = 100) -> List[Story]:
        """
        Generate mixed stories from real codebase analysis.

        Mix:
        - 50% dead imports
        - 30% missing docstrings
        - 20% type hints

        Args:
            count: Total number of stories to generate

        Returns:
            List of Story objects
        """
        stories = []

        # Calculate counts for each type
        dead_import_count = int(count * 0.5)
        docstring_count = int(count * 0.3)
        type_hint_count = count - dead_import_count - docstring_count

        print(f"[RealStoryGenerator] Workspace: {self.workspace_path}")
        print(f"[RealStoryGenerator] Core path: {self.core_path}")
        print(f"[RealStoryGenerator] Core path exists: {self.core_path.exists()}")

        # Generate each type
        print(f"Generating {dead_import_count} dead import stories...")
        dead_stories = self.generate_dead_import_stories(limit=dead_import_count)
        print(f"  Found {len(dead_stories)} dead import stories")
        stories.extend(dead_stories)

        print(f"Generating {docstring_count} docstring stories...")
        doc_stories = self.generate_missing_docstring_stories(limit=docstring_count)
        print(f"  Found {len(doc_stories)} docstring stories")
        stories.extend(doc_stories)

        print(f"Generating {type_hint_count} type hint stories...")
        type_stories = self.generate_type_hint_stories(limit=type_hint_count)
        print(f"  Found {len(type_stories)} type hint stories")
        stories.extend(type_stories)

        print(f"Total stories generated: {len(stories)}")
        return stories


if __name__ == "__main__":
    # Test the generator
    from pathlib import Path
    workspace = Path(__file__).parent.parent.parent
    generator = RealStoryGenerator(workspace)

    stories = generator.generate_mixed_stories(count=20)
    print(f"\nGenerated {len(stories)} stories:")
    for story in stories[:5]:
        print(f"  {story.story_id}: {story.description[:80]}...")
