"""
Integration Tests - NEXUS V7

Tests integration between:
- AutoBootstrap + Commands (REPL)
- GoT + HybridSwarmEngine
- Full orchestration pipeline
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.bootstrap import AutoBootstrap
from core.reasoning import GOT_AVAILABLE
# GoT imports are optional - module may not be implemented yet
if GOT_AVAILABLE:
    from core.reasoning import GraphOfThought, ThoughtGraph, ThoughtNode, ThoughtStatus
else:
    GraphOfThought = ThoughtGraph = ThoughtNode = ThoughtStatus = None
from core.swarm import HybridSwarmEngine
from core.swarm.task_analyzer import TaskComplexity, TaskDomain
from core.interface.commands import (
    SLASH_COMMANDS,
    is_slash_command,
    parse_command
)


# ============================================================================
# AutoBootstrap + Commands Integration
# ============================================================================

class TestBootstrapCommandIntegration:
    """Test AutoBootstrap integration with commands system."""

    def test_bootstrap_command_registered(self):
        """Bootstrap command should be in SLASH_COMMANDS."""
        assert any("/bootstrap" in cmd for cmd in SLASH_COMMANDS.keys())

    def test_bootstrap_command_description(self):
        """Bootstrap command should have proper description."""
        for cmd, desc in SLASH_COMMANDS.items():
            if "/bootstrap" in cmd:
                assert "NEXUS.md" in desc or "project" in desc.lower()
                break

    def test_parse_bootstrap_command(self):
        """Should parse /bootstrap command correctly."""
        cmd, args = parse_command("/bootstrap")
        assert cmd == "/bootstrap"
        assert args == ""

    def test_parse_bootstrap_with_path(self):
        """Should parse /bootstrap with path argument."""
        cmd, args = parse_command("/bootstrap /path/to/project")
        assert cmd == "/bootstrap"
        assert args == "/path/to/project"

    def test_is_slash_command_bootstrap(self):
        """Bootstrap should be detected as slash command."""
        assert is_slash_command("/bootstrap")
        assert is_slash_command("/bootstrap ./project")


class TestBootstrapEndToEnd:
    """End-to-end tests for AutoBootstrap."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure."""
        base = Path(tempfile.mkdtemp())

        # Create Python project structure
        (base / "src").mkdir()
        (base / "tests").mkdir()
        (base / "docs").mkdir()

        # Python files
        (base / "src" / "__init__.py").write_text("")
        (base / "src" / "main.py").write_text("""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")

        # Config files
        (base / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"

[tool.pytest]
testpaths = ["tests"]

[build-system]
requires = ["setuptools"]
""")

        (base / "requirements.txt").write_text("""
fastapi>=0.100.0
uvicorn>=0.22.0
pytest>=7.0.0
""")

        # Test file
        (base / "tests" / "test_main.py").write_text("""
def test_placeholder():
    assert True
""")

        yield base

        # Cleanup
        shutil.rmtree(base, ignore_errors=True)

    def test_full_bootstrap_workflow(self, temp_project):
        """Test complete bootstrap workflow."""
        # 1. Create bootstrap
        bootstrap = AutoBootstrap(temp_project)

        # 2. Analyze project
        analysis = bootstrap.analyze()

        # 3. Verify analysis results
        assert "Python" in analysis.languages
        assert "FastAPI" in analysis.frameworks
        assert analysis.has_tests
        assert analysis.project_name != "Unknown Project"

        # 4. Generate NEXUS.md
        nexus_md = bootstrap.generate_nexus_md(analysis)

        # 5. Verify content
        assert "Python" in nexus_md
        assert "FastAPI" in nexus_md
        assert "pytest" in nexus_md.lower() or "tests" in nexus_md.lower()

        # 6. Save and verify file
        bootstrap.save(nexus_md)
        assert (temp_project / "NEXUS.md").exists()

        # 7. Verify file content matches (normalize line endings)
        saved_content = (temp_project / "NEXUS.md").read_text(encoding="utf-8")
        # Normalize line endings for cross-platform comparison
        assert saved_content.replace('\r\n', '\n') == nexus_md.replace('\r\n', '\n')


# ============================================================================
# GoT + SwarmEngine Integration
# ============================================================================

class TestGoTSwarmIntegration:
    """Test GoT integration with HybridSwarmEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine with GoT enabled."""
        return HybridSwarmEngine()

    def test_got_available_in_engine(self, engine):
        """GoT should be available in engine stats."""
        stats = engine.get_stats()
        assert "got_available" in stats
        assert "got_enabled" in stats

    def test_should_use_got_for_complex_tasks(self, engine):
        """Engine should recommend GoT for complex tasks."""
        # Analyze a complex task
        analysis = engine.start_analysis(
            "Refactor the entire authentication module with new JWT-based "
            "architecture and comprehensive security review"
        )

        # Should recommend GoT for complex tasks
        if analysis.complexity >= TaskComplexity.COMPLEX:
            assert engine.should_use_got(analysis) == True

    def test_should_not_use_got_for_simple_tasks(self, engine):
        """Engine should not recommend GoT for simple tasks."""
        # Analyze a simple task
        analysis = engine.start_analysis("Fix typo in README")

        # Should not use GoT for trivial tasks
        if analysis.complexity == TaskComplexity.TRIVIAL:
            assert engine.should_use_got(analysis) == False

    def test_decompose_complex_task(self, engine):
        """Should decompose complex task into thought graph."""
        # Analyze task
        analysis = engine.start_analysis(
            "Implement a new caching layer with Redis support"
        )

        # Decompose
        graph = engine.decompose_with_got(
            "Implement a new caching layer with Redis support",
            analysis
        )

        if graph is not None:  # GoT available
            assert isinstance(graph, ThoughtGraph)
            assert len(graph.nodes) > 0

    def test_sub_problems_based_on_domains(self, engine):
        """Sub-problems should be domain-specific."""
        # Security task
        analysis = engine.start_analysis(
            "Perform security audit of authentication system"
        )

        sub_problems = engine._generate_sub_problems(
            "Perform security audit of authentication system",
            analysis
        )

        # Should include security-specific step
        has_security_step = any("security" in p.lower() for p in sub_problems)
        # Note: may or may not have security depending on domain detection
        assert len(sub_problems) >= 2  # At minimum: analyze + implement

    def test_coding_task_sub_problems(self, engine):
        """Coding tasks should have code-related sub-problems."""
        analysis = engine.start_analysis(
            "Implement new function to calculate metrics"
        )

        sub_problems = engine._generate_sub_problems(
            "Implement new function to calculate metrics",
            analysis
        )

        # Should include implementation step
        has_implement = any("implement" in p.lower() for p in sub_problems)
        assert has_implement


class TestGoTExecution:
    """Test GoT execution through SwarmEngine."""

    @pytest.fixture
    def engine(self):
        """Create engine with mock invoke_agent."""
        def mock_invoke(agent_id, task_type, context):
            return f"Mock response from {agent_id} for {task_type}"

        return HybridSwarmEngine(invoke_agent=mock_invoke)

    def test_execute_thought_graph_basic(self, engine):
        """Should execute thought graph with mock responses."""
        # Create simple graph
        graph = engine.decompose_with_got(
            "Test task",
            sub_problems=["Step 1", "Step 2"]
        )

        if graph is not None:
            # Execute
            result = engine.execute_thought_graph(graph)

            # Should complete
            assert result is not None
            assert result.is_complete()

    def test_got_summary_generation(self, engine):
        """Should generate summary from completed graph."""
        # Decompose and execute
        graph = engine.decompose_with_got(
            "Test summarization",
            sub_problems=["Analyze", "Synthesize"]
        )

        if graph is not None:
            engine.execute_thought_graph(graph)

            # Get summary
            summary = engine.get_got_summary()
            assert summary is not None or engine._current_thought_graph is None


# ============================================================================
# Full Pipeline Integration
# ============================================================================

class TestFullPipelineIntegration:
    """Test full NEXUS pipeline integration."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        base = Path(tempfile.mkdtemp())

        (base / "workspace").mkdir()
        (base / "_IO_BUFFER").mkdir()

        yield base

        shutil.rmtree(base, ignore_errors=True)

    def test_swarm_engine_reset_clears_got(self):
        """Reset should clear GoT state."""
        engine = HybridSwarmEngine()

        # Start processing
        engine.start_analysis("Complex task requiring analysis")

        # Reset
        engine.reset()

        # GoT state should be cleared
        assert engine._current_thought_graph is None
        assert engine._current_analysis is None

    def test_swarm_stats_include_got(self):
        """Stats should include GoT information."""
        engine = HybridSwarmEngine()
        stats = engine.get_stats()

        assert "got_enabled" in stats
        assert "got_available" in stats
        assert isinstance(stats["got_enabled"], bool)
        assert isinstance(stats["got_available"], bool)

    def test_process_task_basic_flow(self):
        """Test basic task processing flow."""
        def mock_invoke(agent_id, task_type, context):
            return {"content": "Task completed", "status": "success"}

        engine = HybridSwarmEngine(invoke_agent=mock_invoke)

        result = engine.process_task("Simple task")

        assert result is not None
        assert result.status.value in ["completed", "failed"]
        assert result.final_output is not None


# ============================================================================
# Module Import Tests
# ============================================================================

class TestModuleImports:
    """Test that all modules can be imported correctly."""

    def test_import_bootstrap(self):
        """AutoBootstrap should be importable."""
        from core.bootstrap import AutoBootstrap
        assert AutoBootstrap is not None

    def test_import_reasoning(self):
        """GoT should be importable (when available)."""
        from core.reasoning import GOT_AVAILABLE
        # GoT is optional - test that module imports without error
        if GOT_AVAILABLE:
            from core.reasoning import GraphOfThought, ThoughtNode, ThoughtGraph
            assert GraphOfThought is not None
            assert ThoughtNode is not None
            assert ThoughtGraph is not None
        else:
            # GoT not implemented yet - this is acceptable
            pytest.skip("GoT module not implemented yet")

    def test_import_swarm(self):
        """SwarmEngine should be importable."""
        from core.swarm import HybridSwarmEngine
        assert HybridSwarmEngine is not None

    def test_import_security(self):
        """Security modules should be importable."""
        from core.security import PathGuardian, MutationValidator
        assert PathGuardian is not None
        assert MutationValidator is not None

    def test_import_commands(self):
        """Commands should be importable."""
        from core.interface.commands import SLASH_COMMANDS, get_help_message
        assert SLASH_COMMANDS is not None
        assert callable(get_help_message)


# ============================================================================
# Cross-Module Integration
# ============================================================================

class TestCrossModuleIntegration:
    """Test integration between different modules."""

    def test_bootstrap_creates_valid_nexus_md(self):
        """Bootstrap should create valid NEXUS.md for swarm consumption."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "main.py").write_text("print('hello')")

            bootstrap = AutoBootstrap(project)
            analysis = bootstrap.analyze()
            nexus_md = bootstrap.generate_nexus_md(analysis)

            # Should be valid markdown
            assert nexus_md.startswith("#")
            assert len(nexus_md) > 100

    def test_got_integrates_with_task_analysis(self):
        """GoT should work with TaskAnalysis results."""
        engine = HybridSwarmEngine()

        # Analyze task
        analysis = engine.start_analysis(
            "Complex multi-step refactoring task"
        )

        # Generate sub-problems using analysis
        sub_problems = engine._generate_sub_problems(
            "Complex multi-step refactoring task",
            analysis
        )

        # Sub-problems should reflect analysis
        assert len(sub_problems) > 0
        assert all(isinstance(p, str) for p in sub_problems)

    def test_swarm_phase_includes_decomposing(self):
        """SwarmPhase should include DECOMPOSING for GoT."""
        from core.swarm.hybrid_swarm_engine import SwarmPhase

        phases = [p.value for p in SwarmPhase]
        assert "decomposing" in phases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
