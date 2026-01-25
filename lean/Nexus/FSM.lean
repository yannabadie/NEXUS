namespace Nexus

inductive OrchestratorState
  | idle
  | brainstorming
  | executing_tool
  | validating_cfl
  | evolution_brainstorm
  | waiting_user
  | error
  | panic
  | swarm_analyzing
  | swarm_negotiating
  | swarm_executing
  | hibernate
  deriving Repr, DecidableEq

inductive Event
  | user_input
  | tool_use
  | finished
  | stagnation
  | ws_disconnect
  | tool_completed
  | success
  | failure
  | stalemate
  | reset
  | timeout
  | recovery
  | analysis_complete
  | skip_negotiation
  | error
  | consensus
  | execution_complete
  | continue
  | ws_reconnect
  | user_cancel
  deriving Repr, DecidableEq

def stateToString : OrchestratorState -> String
  | .idle => "IDLE"
  | .brainstorming => "BRAINSTORMING"
  | .executing_tool => "EXECUTING_TOOL"
  | .validating_cfl => "VALIDATING_CFL"
  | .evolution_brainstorm => "EVOLUTION_BRAINSTORM"
  | .waiting_user => "WAITING_USER"
  | .error => "ERROR"
  | .panic => "PANIC"
  | .swarm_analyzing => "SWARM_ANALYZING"
  | .swarm_negotiating => "SWARM_NEGOTIATING"
  | .swarm_executing => "SWARM_EXECUTING"
  | .hibernate => "HIBERNATE"

def eventToString : Event -> String
  | .user_input => "user_input"
  | .tool_use => "tool_use"
  | .finished => "finished"
  | .stagnation => "stagnation"
  | .ws_disconnect => "ws_disconnect"
  | .tool_completed => "tool_completed"
  | .success => "success"
  | .failure => "failure"
  | .stalemate => "stalemate"
  | .reset => "reset"
  | .timeout => "timeout"
  | .recovery => "recovery"
  | .analysis_complete => "analysis_complete"
  | .skip_negotiation => "skip_negotiation"
  | .error => "error"
  | .consensus => "consensus"
  | .execution_complete => "execution_complete"
  | .continue => "continue"
  | .ws_reconnect => "ws_reconnect"
  | .user_cancel => "user_cancel"

abbrev Transition := Prod OrchestratorState (Prod Event (Option OrchestratorState))

def transitionTable : List Transition :=
  [
    (.idle, .user_input, some .brainstorming),
    (.brainstorming, .tool_use, some .executing_tool),
    (.brainstorming, .finished, some .waiting_user),
    (.brainstorming, .stagnation, some .error),
    (.brainstorming, .ws_disconnect, some .hibernate),
    (.executing_tool, .tool_completed, some .validating_cfl),
    (.executing_tool, .ws_disconnect, some .hibernate),
    (.validating_cfl, .success, some .idle),
    (.validating_cfl, .failure, some .brainstorming),
    (.validating_cfl, .stalemate, some .error),
    (.validating_cfl, .ws_disconnect, some .hibernate),
    (.waiting_user, .user_input, some .brainstorming),
    (.waiting_user, .ws_disconnect, some .hibernate),
    (.error, .reset, some .idle),
    (.error, .timeout, some .panic),
    (.panic, .recovery, some .idle),
    (.swarm_analyzing, .analysis_complete, some .swarm_negotiating),
    (.swarm_analyzing, .skip_negotiation, some .swarm_executing),
    (.swarm_analyzing, .error, some .error),
    (.swarm_analyzing, .ws_disconnect, some .hibernate),
    (.swarm_negotiating, .consensus, some .swarm_executing),
    (.swarm_negotiating, .timeout, some .swarm_executing),
    (.swarm_negotiating, .error, some .error),
    (.swarm_negotiating, .ws_disconnect, some .hibernate),
    (.swarm_executing, .execution_complete, some .validating_cfl),
    (.swarm_executing, .continue, some .swarm_executing),
    (.swarm_executing, .error, some .error),
    (.swarm_executing, .ws_disconnect, some .hibernate),
    (.hibernate, .ws_reconnect, none),
    (.hibernate, .timeout, some .idle),
    (.hibernate, .user_cancel, some .idle)
  ]

def activeStates : List OrchestratorState :=
  [
    .brainstorming,
    .executing_tool,
    .validating_cfl,
    .waiting_user,
    .swarm_analyzing,
    .swarm_negotiating,
    .swarm_executing
  ]

def formatFSM (fromState : OrchestratorState) (event : Event)
    (nextState : Option OrchestratorState) : String :=
  let nextStr := match nextState with
    | some state => stateToString state
    | none => "none"
  "FSM|" ++ stateToString fromState ++ "|" ++ eventToString event ++ "|" ++ nextStr

def fsmLines : List String :=
  transitionTable.map fun (entry : Transition) =>
    formatFSM entry.1 entry.2.1 entry.2.2

def activeLines : List String :=
  activeStates.map fun state => "ACTIVE|" ++ stateToString state

end Nexus
