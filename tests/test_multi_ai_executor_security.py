"""
Security tests for multi_ai_executor.py

Tests the three security fixes:
1. Path traversal prevention (CWE-22)
2. Validated file writes from AI output
3. Path validation before file reads
"""

import pytest
import tempfile
import json
from pathlib import Path
import sys
import asyncio

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ncm.multi_ai_executor import MultiAIExecutor, MultiAIExecutorConfig


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace."""
    workspace = Path(tempfile.mkdtemp()) / "workspace"
    workspace.mkdir(parents=True)
    
    # Create a test file
    test_file = workspace / "test.py"
    test_file.write_text("import os\nimport sys\n")
    
    yield workspace
    
    # Cleanup
    import shutil
    shutil.rmtree(workspace.parent, ignore_errors=True)


@pytest.fixture
def executor(temp_workspace):
    """Create a MultiAIExecutor instance."""
    config = MultiAIExecutorConfig(
        workspace_path=temp_workspace,
        stories_path=temp_workspace / "stories.json"
    )
    return MultiAIExecutor(config)


class TestPathTraversalSecurity:
    """Test CWE-22 path traversal vulnerability fixes."""
    
    def test_traversal_attack_blocked_in_simple_executor(self, executor, temp_workspace):
        """Path traversal in _execute_simple should be blocked."""
        # Create a file outside workspace
        outside_file = temp_workspace.parent / "secret.txt"
        outside_file.write_text("secret")
        
        # Try to access it via traversal
        story = {
            "story_id": "test-1",
            "category": "dead_import",
            "target_file": "../secret.txt",
            "import_text": "os",
            "description": "Remove unused import"
        }
        
        result = asyncio.run(executor._execute_simple(story))
        
        assert result.status == "FAILED"
        assert "SECURITY" in result.error
        assert "path validation failed" in result.error.lower()
    
    def test_absolute_path_blocked_in_simple_executor(self, executor, temp_workspace):
        """Absolute paths outside workspace should be blocked."""
        # Try to use absolute path
        outside_file = temp_workspace.parent / "secret.txt"
        outside_file.write_text("secret")
        
        story = {
            "story_id": "test-2",
            "category": "dead_import",
            "target_file": str(outside_file),
            "import_text": "os",
            "description": "Remove unused import"
        }
        
        result = asyncio.run(executor._execute_simple(story))
        
        assert result.status == "FAILED"
        assert "SECURITY" in result.error
    
    def test_valid_workspace_path_allowed(self, executor, temp_workspace):
        """Valid workspace paths should work."""
        story = {
            "story_id": "test-3",
            "category": "dead_import",
            "target_file": "test.py",
            "import_text": "os",
            "description": "Remove unused import os",
            "line_number": 1
        }
        
        result = asyncio.run(executor._execute_simple(story))
        
        # Should succeed (or skip if import not found, but not fail with SECURITY error)
        assert result.status in ["SUCCESS", "SKIPPED"]
        if result.status == "FAILED":
            assert "SECURITY" not in result.error


class TestAIOutputValidation:
    """Test validation of AI-generated code before writing."""
    
    def test_apply_changes_blocks_traversal(self, executor, temp_workspace):
        """_apply_changes should block path traversal."""
        # Create a file outside workspace
        outside_file = temp_workspace.parent / "target.txt"
        outside_file.write_text("original")
        
        story = {
            "target_file": "../target.txt"  # Attempt traversal
        }
        
        ai_output = """
Some analysis...
```python
# Malicious code
import os
os.system("rm -rf /")
```
"""
        
        # Should not write to outside file
        asyncio.run(executor._apply_changes(story, ai_output))
        
        # File should be unchanged
        assert outside_file.read_text() == "original"
    
    def test_apply_changes_valid_path_allowed(self, executor, temp_workspace):
        """_apply_changes should work with valid paths."""
        story = {
            "target_file": "new_file.py"
        }
        
        ai_output = """
Analysis complete.
```python
# New file content
def hello():
    return "world"
```
"""
        
        asyncio.run(executor._apply_changes(story, ai_output))
        
        # File should be created
        new_file = temp_workspace / "new_file.py"
        assert new_file.exists()
        assert "def hello" in new_file.read_text()


class TestBuildPromptSecurity:
    """Test path validation in _build_prompt."""
    
    def test_build_prompt_blocks_traversal(self, executor, temp_workspace):
        """_build_prompt should not read sacred files via traversal."""
        # Create a .env file outside workspace (sacred file that should be blocked)
        env_file = temp_workspace.parent / ".env"
        env_file.write_text("SECRET_KEY=leaked_value")
        
        # Try to include it via traversal
        story = {
            "category": "type_error",
            "description": "Fix types",
            "target_file": "../.env"
        }
        
        prompt = executor._build_prompt(story, include_context=True)
        
        # Should not include the secret content (PathGuardian blocks .env)
        assert "SECRET_KEY" not in prompt
        assert "leaked_value" not in prompt
        # Should still have the task description
        assert "Fix types" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
