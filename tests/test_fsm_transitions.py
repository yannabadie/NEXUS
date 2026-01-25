"""FSM transition coverage tests."""

from core.fsm.states import OrchestratorState, TRANSITION_MATRIX, ACTIVE_STATES


def test_fsm_state_count() -> None:
    assert len(OrchestratorState) == 12


def test_transition_matrix_state_keys() -> None:
    for state in TRANSITION_MATRIX:
        assert state in OrchestratorState


def test_transition_targets_are_valid() -> None:
    for transitions in TRANSITION_MATRIX.values():
        for next_state in transitions.values():
            if next_state is None:
                continue
            assert next_state in OrchestratorState


def test_error_and_panic_recovery_paths() -> None:
    assert TRANSITION_MATRIX[OrchestratorState.ERROR]["reset"] == OrchestratorState.IDLE
    assert TRANSITION_MATRIX[OrchestratorState.PANIC]["recovery"] == OrchestratorState.IDLE


def test_hibernate_reconnect_is_dynamic() -> None:
    assert TRANSITION_MATRIX[OrchestratorState.HIBERNATE]["ws_reconnect"] is None


def test_swarm_transitions_exist() -> None:
    assert TRANSITION_MATRIX[OrchestratorState.SWARM_ANALYZING]["analysis_complete"] == OrchestratorState.SWARM_NEGOTIATING
    assert TRANSITION_MATRIX[OrchestratorState.SWARM_ANALYZING]["skip_negotiation"] == OrchestratorState.SWARM_EXECUTING
    assert TRANSITION_MATRIX[OrchestratorState.SWARM_NEGOTIATING]["consensus"] == OrchestratorState.SWARM_EXECUTING
    assert TRANSITION_MATRIX[OrchestratorState.SWARM_EXECUTING]["execution_complete"] == OrchestratorState.VALIDATING_CFL


def test_active_states_can_hibernate() -> None:
    for state in ACTIVE_STATES:
        assert TRANSITION_MATRIX[state]["ws_disconnect"] == OrchestratorState.HIBERNATE
