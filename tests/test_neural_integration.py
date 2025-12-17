import pytest
from unittest.mock import MagicMock
from core.fsm.stagnation_predictor import PredictionLevel, PredictionResult
from core.orchestration.fsm_handlers import FSMHandlers

class TestNeuralIntegration:
    def test_stagnation_wiring(self):
        """Verify that FSMHandlers calls stagnation_predictor.predict() and routes correctly."""
        
        # Mock Orchestrator
        orch_mock = MagicMock()
        orch_mock.stagnation_predictor = MagicMock()
        orch_mock.plan_health.check_health.return_value = {"status": "OK"}
        orch_mock.blackboard = {"strategic_plan": []}
        orch_mock.config = MagicMock()
        orch_mock.config.ui_verbose = False
        
        # Initialize Handlers
        handlers = FSMHandlers(orch_mock)
        
        # --- Case A: NUDGE ---
        orch_mock.stagnation_predictor.predict.return_value = PredictionResult(
            probability=0.3, 
            level=PredictionLevel.NUDGE, 
            factors={}, 
            recommendation="Nudge", 
            nudge_message="Wake up"
        )
        
        handlers.handle_brainstorming()
        
        # Verify handle_prediction called
        orch_mock._handle_prediction.assert_called_with(orch_mock.stagnation_predictor.predict.return_value)
        orch_mock._handle_prediction.reset_mock()
        
        # --- Case B: INTERVENE ---
        orch_mock.stagnation_predictor.predict.return_value = PredictionResult(
            probability=0.5, 
            level=PredictionLevel.INTERVENE, 
            factors={}, 
            recommendation="Stop", 
            nudge_message="Stop"
        )
        
        handlers.handle_brainstorming()
        
        orch_mock._handle_prediction.assert_called_with(orch_mock.stagnation_predictor.predict.return_value)
        orch_mock._handle_prediction.reset_mock()
        
        # --- Case C: CONTINUE ---
        result_continue = PredictionResult(
            probability=0.1, 
            level=PredictionLevel.CONTINUE, 
            factors={}, 
            recommendation="OK", 
            nudge_message=None
        )
        orch_mock.stagnation_predictor.predict.return_value = result_continue
        
        # Mock _invoke_agent to prevent crash downstream, or catch exception
        orch_mock._invoke_agent.side_effect = Exception("Stop here")
        
        try:
            handlers.handle_brainstorming()
        except Exception as e:
            if str(e) != "Stop here":
                raise e
        
        # Verify _handle_prediction NOT called
        orch_mock._handle_prediction.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
