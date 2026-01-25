from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import pytest


def _parse_oracle(lines: Iterable[str]) -> Dict[str, object]:
    fsm: Dict[Tuple[str, str], Optional[str]] = {}
    active_states: List[str] = []
    swarm: Dict[str, Optional[str]] = {}
    hive_states: List[str] = []
    hive_phases: List[str] = []
    hive_breakpoints: List[str] = []
    evolution_phases: List[str] = []

    for line in lines:
        parts = line.split("|")
        if len(parts) < 2:
            continue
        tag = parts[0]
        if tag == "FSM" and len(parts) == 4:
            from_state, event, next_state = parts[1], parts[2], parts[3]
            fsm[(from_state, event)] = None if next_state == "none" else next_state
        elif tag == "ACTIVE" and len(parts) == 2:
            active_states.append(parts[1])
        elif tag == "SWARM" and len(parts) == 3:
            mode, next_mode = parts[1], parts[2]
            swarm[mode] = None if next_mode == "none" else next_mode
        elif tag == "HIVE_STATE" and len(parts) == 2:
            hive_states.append(parts[1])
        elif tag == "HIVE_PHASE" and len(parts) == 2:
            hive_phases.append(parts[1])
        elif tag == "HIVE_BREAKPOINT" and len(parts) == 2:
            hive_breakpoints.append(parts[1])
        elif tag == "EVOLUTION_PHASE" and len(parts) == 2:
            evolution_phases.append(parts[1])

    return {
        "fsm": fsm,
        "active_states": active_states,
        "swarm": swarm,
        "hive_states": hive_states,
        "hive_phases": hive_phases,
        "hive_breakpoints": hive_breakpoints,
        "evolution_phases": evolution_phases,
    }


@pytest.mark.lean_oracle
def test_fsm_transitions_match_oracle(lean_oracle_lines):
    from core.fsm.states import TRANSITION_MATRIX

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_fsm: Dict[Tuple[str, str], Optional[str]] = parsed["fsm"]  # type: ignore[assignment]

    expected: Dict[Tuple[str, str], Optional[str]] = {}
    for from_state, transitions in TRANSITION_MATRIX.items():
        from_name = from_state.name
        for event, to_state in transitions.items():
            expected[(from_name, event)] = None if to_state is None else to_state.name

    assert expected == oracle_fsm


@pytest.mark.lean_oracle
def test_active_states_match_oracle(lean_oracle_lines):
    from core.fsm.states import ACTIVE_STATES

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_active = set(parsed["active_states"])  # type: ignore[arg-type]
    expected = {state.name for state in ACTIVE_STATES}
    assert expected == oracle_active


@pytest.mark.lean_oracle
def test_swarm_fallbacks_match_oracle(lean_oracle_lines):
    from core.swarm.collaboration_modes import CollaborationMode

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_swarm: Dict[str, Optional[str]] = parsed["swarm"]  # type: ignore[assignment]

    expected: Dict[str, Optional[str]] = {}
    for mode in CollaborationMode:
        fallback = mode.fallback_mode
        expected[mode.name] = fallback.name if fallback else None

    assert expected == oracle_swarm


@pytest.mark.lean_oracle
def test_hivemind_states_match_oracle(lean_oracle_lines):
    from core.hive_mind.types import HiveMindState

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_states = set(parsed["hive_states"])  # type: ignore[arg-type]
    expected = {state.value for state in HiveMindState}
    assert expected == oracle_states


@pytest.mark.lean_oracle
def test_hivemind_phases_match_oracle(lean_oracle_lines):
    from core.hive_mind.saga_manager import PHASE_ORDER

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_phases = parsed["hive_phases"]  # type: ignore[assignment]
    assert list(PHASE_ORDER) == oracle_phases


@pytest.mark.lean_oracle
def test_hivemind_breakpoints_match_oracle(lean_oracle_lines):
    from core.hive_mind.types import UserBreakpoint

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_breakpoints = set(parsed["hive_breakpoints"])  # type: ignore[arg-type]
    expected = {bp.value for bp in UserBreakpoint}
    assert expected == oracle_breakpoints


@pytest.mark.lean_oracle
def test_evolution_phases_match_oracle(lean_oracle_lines):
    from core.evolution.models import EvolutionPhaseStatus

    parsed = _parse_oracle(lean_oracle_lines)
    oracle_phases = set(parsed["evolution_phases"])  # type: ignore[arg-type]
    expected = {phase.value for phase in EvolutionPhaseStatus}
    assert expected == oracle_phases
