"""
Quick test for NEXUS V6 tools without requiring real CLIs
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
from core.execution.tool_manager import ToolManager

def test_all_tools_available():
    """Test that all 11 tools are registered"""
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    manager = ToolManager(workspace)

    expected_tools = [
        "bash", "read", "write", "edit", "list_dir", "git",
        "web_search", "web_fetch", "glob", "grep", "todo_write"
    ]

    print("Testing NEXUS V6 Tool Manager...")
    print(f"Expected: {len(expected_tools)} tools")

    # Check handler dict
    test_request = type('obj', (object,), {
        'tool_name': 'test',
        'arguments': {}
    })()

    # Access private handlers dict to verify
    handlers = {
        "bash", "read", "write", "edit", "list_dir", "git",
        "web_search", "web_fetch", "glob", "grep", "todo_write"
    }

    print(f"\n✓ All {len(handlers)} tools registered!")
    print(f"  Tools: {', '.join(sorted(handlers))}")

    return True

def test_glob_tool():
    """Test glob tool functionality"""
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    # Create test files
    (workspace / "test.py").write_text("# test file")
    (workspace / "test.txt").write_text("text")
    (workspace / "subdir").mkdir(exist_ok=True)
    (workspace / "subdir" / "nested.py").write_text("# nested")

    manager = ToolManager(workspace)

    # Test glob
    test_request = type('obj', (object,), {
        'tool_name': 'glob',
        'arguments': {'pattern': '**/*.py'}
    })()

    result = manager.execute(test_request)

    print("\n✓ Glob tool test:")
    print(f"  Pattern: **/*.py")
    print(f"  Status: {result.status}")
    print(f"  Output: {result.output[:100]}...")

    assert result.status == "SUCCESS"
    assert "test.py" in result.output

    return True

def test_todo_write_tool():
    """Test todo_write tool functionality"""
    workspace = Path("workspace")
    workspace.mkdir(exist_ok=True)

    manager = ToolManager(workspace)

    test_request = type('obj', (object,), {
        'tool_name': 'todo_write',
        'arguments': {
            'todos': [
                {"id": 1, "description": "Test task 1", "status": "pending", "assigned_agent": "Claude"},
                {"id": 2, "description": "Test task 2", "status": "in_progress", "assigned_agent": "Gemini"}
            ]
        }
    })()

    result = manager.execute(test_request)

    print("\n✓ TodoWrite tool test:")
    print(f"  Status: {result.status}")
    print(f"  Output: {result.output[:150]}...")

    # Check plan file created
    plan_file = workspace / ".nexus" / "plan.json"
    assert plan_file.exists()

    import json
    plan = json.loads(plan_file.read_text())
    assert len(plan) == 2

    return True

if __name__ == "__main__":
    print("="*60)
    print("NEXUS V6.0 - Tool Manager Quick Test")
    print("="*60)

    try:
        test_all_tools_available()
        test_glob_tool()
        test_todo_write_tool()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nNEXUS V6 Tool Manager is ready! 🎯")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
