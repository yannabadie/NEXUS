"""
Simple smoke tests for NEXUS V7

Run with: python -m pytest tests/
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """Test that all modules can be imported"""
    from core.config import load_config
    from core.meta.cli_inspector import CLIInspector
    from core.fsm.states import OrchestratorState
    from core.fsm.stagnation_detector import StagnationDetector
    from core.synapse.protocol_v7 import LightMessageV7
    from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
    from core.orchestration_v7 import OrchestratorV7

    assert True  # If we got here, imports worked


def test_config():
    """Test config loads"""
    from core.config import load_config

    config = load_config()
    assert config.gemini_cli_path
    assert config.claude_cli_path
    assert config.max_stalemate_count > 0


def test_stagnation_detector():
    """Test stagnation detection"""
    from core.fsm.stagnation_detector import StagnationDetector

    detector = StagnationDetector(similarity_threshold=0.8, window_size=3)

    # Add highly similar messages (same with minor variation)
    detector.add_message("I will read auth.py to find the bug")
    detector.add_message("I will read auth.py to find the bug")
    detector.add_message("I will read auth.py to find the bug")

    # Should detect stagnation (identical messages)
    assert detector.is_stagnant()


def test_claude_parser():
    """Test Claude hybrid parser"""
    from core.drivers.claude_driver_hybrid import ClaudeDriverHybrid
    from pathlib import Path
    from core.config import Config

    config = Config()
    driver = ClaudeDriverHybrid(config, Path("workspace"))

    # Test parsing natural language + XML
    raw_text = """
Je vais lire le fichier.

<tool_use name="read">
{"file_path": "auth.py"}
</tool_use>

Puis je chercherai le bug.
"""

    result = driver._parse_hybrid_response(raw_text)

    assert result["sender"] == "Claude"
    assert result["action_type"] == "TOOL_USE"
    assert "lire le fichier" in result["content"].lower()
    assert result["tool_use"]["tool_name"] == "read"
    assert result["tool_use"]["arguments"]["file_path"] == "auth.py"


if __name__ == "__main__":
    # Run tests manually
    test_imports()
    print("✓ Imports OK")

    test_config()
    print("✓ Config OK")

    test_stagnation_detector()
    print("✓ Stagnation Detector OK")

    test_claude_parser()
    print("✓ Claude Parser OK")

    print("\n✅ All tests passed!")
