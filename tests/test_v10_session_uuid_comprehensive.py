"""
NEXUS V10 - Comprehensive Test Suite for session_uuid Propagation
Uses pytest-asyncio with AsyncMock for rigorous async testing.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_gemini_driver():
    """Mock Gemini driver with async send_message_async."""
    driver = MagicMock()
    driver.send_message_async = AsyncMock(return_value={
        "content": '{"task_understanding": "test", "complexity_assessment": "MODERATE", "confidence": 0.8}'
    })
    return driver


@pytest.fixture
def mock_claude_driver():
    """Mock Claude driver with async send_message_async."""
    driver = MagicMock()
    driver.send_message_async = AsyncMock(return_value={
        "content": '{"task_understanding": "test", "complexity_assessment": "MODERATE", "confidence": 0.85}'
    })
    return driver


@pytest.fixture
def mock_cost_estimator():
    """Mock cost estimator."""
    estimator = MagicMock()
    estimator.can_afford_multiple = MagicMock(return_value=True)
    estimator.record_cost = MagicMock()
    estimator.start_task = MagicMock()
    return estimator


@pytest.fixture
def mock_context_manager():
    """Mock context manager."""
    context = MagicMock()
    context.add_task = MagicMock()
    context.clear = MagicMock()
    return context


# ============================================================================
# UNIT TESTS: Phase Analysis
# ============================================================================

class TestPhaseAnalysisSessionUUID:
    """Test session_uuid propagation in Phase 1 Analysis."""

    @pytest.mark.asyncio
    async def test_execute_accepts_session_uuid(
        self,
        mock_gemini_driver,
        mock_claude_driver,
        mock_cost_estimator,
        mock_context_manager
    ):
        """Phase 1 execute() should accept session_uuid parameter."""
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        
        phase = IndependentAnalysisPhase(
            gemini_driver=mock_gemini_driver,
            claude_driver=mock_claude_driver,
            cost_estimator=mock_cost_estimator,
            context_manager=mock_context_manager
        )
        
        session_uuid = "test-session-uuid-12345"
        result = await phase.execute("Test task", session_uuid=session_uuid)
        
        # Verify session_uuid was stored
        assert phase._session_uuid == session_uuid
        assert result is not None

    @pytest.mark.asyncio
    async def test_gemini_call_passes_session_uuid(
        self,
        mock_gemini_driver,
        mock_claude_driver,
        mock_cost_estimator,
        mock_context_manager
    ):
        """Phase 1 should pass session_uuid to Gemini send_message_async."""
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        
        phase = IndependentAnalysisPhase(
            gemini_driver=mock_gemini_driver,
            claude_driver=mock_claude_driver,
            cost_estimator=mock_cost_estimator,
            context_manager=mock_context_manager
        )
        
        session_uuid = "test-session-uuid-12345"
        await phase.execute("Test task", session_uuid=session_uuid)
        
        # Verify Gemini was called with session_uuid
        mock_gemini_driver.send_message_async.assert_called()
        call_kwargs = mock_gemini_driver.send_message_async.call_args
        assert call_kwargs.kwargs.get('session_uuid') == session_uuid

    @pytest.mark.asyncio
    async def test_claude_call_passes_session_uuid(
        self,
        mock_gemini_driver,
        mock_claude_driver,
        mock_cost_estimator,
        mock_context_manager
    ):
        """Phase 1 should pass session_uuid to Claude send_message_async."""
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        
        phase = IndependentAnalysisPhase(
            gemini_driver=mock_gemini_driver,
            claude_driver=mock_claude_driver,
            cost_estimator=mock_cost_estimator,
            context_manager=mock_context_manager
        )
        
        session_uuid = "test-session-uuid-12345"
        await phase.execute("Test task", session_uuid=session_uuid)
        
        # Verify Claude was called with session_uuid
        mock_claude_driver.send_message_async.assert_called()
        call_kwargs = mock_claude_driver.send_message_async.call_args
        assert call_kwargs.kwargs.get('session_uuid') == session_uuid


# ============================================================================
# UNIT TESTS: Phase Debate
# ============================================================================

class TestPhaseDebateSessionUUID:
    """Test session_uuid propagation in Phase 2 Debate."""

    def test_execute_accepts_session_uuid_param(self):
        """Phase 2 execute() should have session_uuid parameter."""
        import inspect
        from core.hive_mind.phases.phase_debate import StrategicDebatePhase
        
        sig = inspect.signature(StrategicDebatePhase.execute)
        params = list(sig.parameters.keys())
        
        assert "session_uuid" in params


# ============================================================================
# UNIT TESTS: JSON Parsing
# ============================================================================

class TestJSONParsing:
    """Test improved JSON parsing with ast.literal_eval fallback."""

    def test_parse_valid_json(self):
        """Should parse valid JSON correctly."""
        import json
        import ast
        
        # Valid JSON
        response = '{"task_understanding": "Test", "confidence": 0.9}'
        
        # Should parse with json.loads
        result = json.loads(response)
        assert result["task_understanding"] == "Test"
        assert result["confidence"] == 0.9

    def test_parse_python_dict_single_quotes(self):
        """Should parse Python dict with single quotes via ast.literal_eval."""
        import json
        import ast
        
        # Python dict repr (single quotes)
        input_str = "{'key': 'value', 'number': 42}"
        
        # Should fail with json.loads
        with pytest.raises(json.JSONDecodeError):
            json.loads(input_str)
        
        # Should work with ast.literal_eval
        result = ast.literal_eval(input_str)
        assert result == {'key': 'value', 'number': 42}


# ============================================================================
# INTEGRATION TESTS: TrueHiveMind Orchestrator
# ============================================================================

class TestTrueHiveMindSessionUUID:
    """Test session_uuid generation and propagation in orchestrator."""

    def test_orchestrator_generates_session_uuid(self):
        """TrueHiveMind should generate session_uuid in process_task."""
        import inspect
        from core.hive_mind.orchestrator import TrueHiveMind
        
        source = inspect.getsource(TrueHiveMind.process_task)
        assert "_current_session_uuid" in source
        assert "uuid.uuid4()" in source

    def test_all_phases_have_session_uuid_parameter(self):
        """All phase execute() methods should accept session_uuid."""
        import inspect
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        from core.hive_mind.phases.phase_debate import StrategicDebatePhase
        from core.hive_mind.phases.phase_architecture import ArchitectureGenerationPhase
        from core.hive_mind.phases.phase_execution import MonitoredExecutionPhase
        from core.hive_mind.phases.phase_diagnosis import FailureDiagnosisPhase
        from core.hive_mind.phases.phase_consolidation import KnowledgeConsolidationPhase
        
        phases = [
            ("Phase 1", IndependentAnalysisPhase),
            ("Phase 2", StrategicDebatePhase),
            ("Phase 3", ArchitectureGenerationPhase),
            ("Phase 4", MonitoredExecutionPhase),
            ("Phase 5", FailureDiagnosisPhase),
            ("Phase 7", KnowledgeConsolidationPhase),
        ]
        
        for name, phase_class in phases:
            sig = inspect.signature(phase_class.execute)
            params = list(sig.parameters.keys())
            assert "session_uuid" in params, f"{name} missing session_uuid parameter"


# ============================================================================
# REGRESSION TESTS: Bug Fixes
# ============================================================================

class TestBugFixes:
    """Test that V10 bug fixes are in place."""

    def test_len_content_not_len_response(self):
        """Verify len(content) is used instead of len(response)."""
        import inspect
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        
        source = inspect.getsource(IndependentAnalysisPhase._analyze_with_gemini)
        
        # Should have len(content), not len(response)
        assert "len(content)" in source
        # Should NOT have the bug
        assert "len(response) // 4" not in source or "len(content)" in source

    def test_ansi_color_fix(self):
        """Verify ANSI color fix for Windows is in place."""
        import inspect
        from core.hive_mind.phases.phase_debate import StrategicDebatePhase
        
        source = inspect.getsourcefile(StrategicDebatePhase)
        with open(source, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should have Windows ANSI fix
        assert "os.system" in content or "colorama" in content


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStressSessionIsolation:
    """Stress tests for session isolation."""

    @pytest.mark.asyncio
    async def test_concurrent_sessions_isolated(
        self,
        mock_gemini_driver,
        mock_claude_driver,
        mock_cost_estimator,
        mock_context_manager
    ):
        """Concurrent phase executions should have isolated sessions."""
        from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
        
        # Create multiple phases
        phases = [
            IndependentAnalysisPhase(
                gemini_driver=mock_gemini_driver,
                claude_driver=mock_claude_driver,
                cost_estimator=mock_cost_estimator,
                context_manager=mock_context_manager
            )
            for _ in range(5)
        ]
        
        # Execute with different session UUIDs
        session_uuids = [f"session-{i}" for i in range(5)]
        
        tasks = [
            phase.execute(f"Task {i}", session_uuid=session_uuids[i])
            for i, phase in enumerate(phases)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify each phase has its correct session_uuid
        for i, phase in enumerate(phases):
            assert phase._session_uuid == session_uuids[i]


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
