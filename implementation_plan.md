# Implementation Plan - Cycle 003: Neural Upgrade

## Goal
Replace the legacy **Reactive** `StagnationDetector` (V8.0) with the new **Proactive** `StagnationPredictor` (V12.4) within the core `OrchestratorV7`.

## Why?
- **Current State**: System waits for ~3 loops of identical text to realize it's stuck. Wastes tokens and time. (SOTA behavior).
- **Target State**: System detects "hesitation patterns" (`let me think`, diminishing message length, no tool use) *before* the loop solidifies and nudges itself to act. (Better than SOTA).

## The Gap (Interface Mismatch)

| Feature | StagnationDetector (Old) | StagnationPredictor (New) |
|---------|--------------------------|---------------------------|
| **Input** | `add_message(content)` | `add_message(content, has_tool_use: bool)` |
| **Check** | `is_stagnant() -> bool` | `predict() -> PredictionResult` |
| **Output** | `get_stagnation_message()` | `result.recommendation`, `result.nudge_message` |
| **Levels** | Boolean (Yes/No) | Gradient (`CONTINUE`, `MONITOR`, `NUDGE`, `INTERVENE`) |

## Proposed Changes

### 1. Modify `core/orchestration_v7.py`

#### Imports
- Remove `StagnationDetector`
- Import `StagnationPredictor`, `PredictionLevel`

#### `__init__`
- Initialize `self.stagnation_predictor = StagnationPredictor()` instead of detector.

#### `process_turn` (The Loop)
- Identify if the current turn involved tool use (this data exists in `_make_result`).
- Feed `output` and `tool_use_status` into `predictor.add_message()`.
- Call `predictor.predict()` at the start of the turn (or end).

#### `_handle_stagnation` -> `_handle_prediction`
- Instead of binary check `if detector.is_stagnant()`, implement gradient logic:
    - **MONITOR**: Log generic debug.
    - **NUDGE**: Inject a "System Nudge" into the context (Gentle).
    - **INTERVENE**: Trigger the full Stagnation state (Force Gemini).

### 2. Adaptation Logic
We need to capture "Has Tool Use" which wasn't previously tracked explicitly for stagnation.
We will pull this from `self.blackboard.get("last_turn_had_tool", False)`.

## Verification Plan
1.  **Unit Test**: Create `tests/core/test_prediction_wiring.py` to simulate a hesitation loop and verify the NUDGE is fired.
2.  **Manual Check**: Run a controlled loop via REPL to see if it catches me "thinking" too much.
