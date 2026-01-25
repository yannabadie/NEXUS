namespace Nexus

inductive HiveMindState
  | hive_gating
  | hive_analyzing_gemini
  | hive_analyzing_claude
  | hive_comparing_analyses
  | hive_debating
  | hive_checking_consensus
  | hive_breakpoint_debate
  | hive_architecting
  | hive_checking_registry
  | hive_breakpoint_spawn
  | hive_spawning
  | hive_executing
  | hive_monitoring
  | hive_diagnosing
  | hive_breakpoint_diagnosis
  | hive_deciding_retry
  | hive_applying_changes
  | hive_reflecting
  | hive_deciding_retention
  | hive_breakpoint_consolidation
  | hive_consolidating
  | hive_success
  | hive_failed
  | hive_escalate
  deriving Repr, DecidableEq

def hiveStateToString : HiveMindState -> String
  | .hive_gating => "hive_gating"
  | .hive_analyzing_gemini => "hive_analyzing_gemini"
  | .hive_analyzing_claude => "hive_analyzing_claude"
  | .hive_comparing_analyses => "hive_comparing_analyses"
  | .hive_debating => "hive_debating"
  | .hive_checking_consensus => "hive_checking_consensus"
  | .hive_breakpoint_debate => "hive_breakpoint_debate"
  | .hive_architecting => "hive_architecting"
  | .hive_checking_registry => "hive_checking_registry"
  | .hive_breakpoint_spawn => "hive_breakpoint_spawn"
  | .hive_spawning => "hive_spawning"
  | .hive_executing => "hive_executing"
  | .hive_monitoring => "hive_monitoring"
  | .hive_diagnosing => "hive_diagnosing"
  | .hive_breakpoint_diagnosis => "hive_breakpoint_diagnosis"
  | .hive_deciding_retry => "hive_deciding_retry"
  | .hive_applying_changes => "hive_applying_changes"
  | .hive_reflecting => "hive_reflecting"
  | .hive_deciding_retention => "hive_deciding_retention"
  | .hive_breakpoint_consolidation => "hive_breakpoint_consolidation"
  | .hive_consolidating => "hive_consolidating"
  | .hive_success => "hive_success"
  | .hive_failed => "hive_failed"
  | .hive_escalate => "hive_escalate"

def hiveStates : List HiveMindState :=
  [
    .hive_gating,
    .hive_analyzing_gemini,
    .hive_analyzing_claude,
    .hive_comparing_analyses,
    .hive_debating,
    .hive_checking_consensus,
    .hive_breakpoint_debate,
    .hive_architecting,
    .hive_checking_registry,
    .hive_breakpoint_spawn,
    .hive_spawning,
    .hive_executing,
    .hive_monitoring,
    .hive_diagnosing,
    .hive_breakpoint_diagnosis,
    .hive_deciding_retry,
    .hive_applying_changes,
    .hive_reflecting,
    .hive_deciding_retention,
    .hive_breakpoint_consolidation,
    .hive_consolidating,
    .hive_success,
    .hive_failed,
    .hive_escalate
  ]

def hiveStateLines : List String :=
  hiveStates.map fun state => "HIVE_STATE|" ++ hiveStateToString state

def hivePhases : List String :=
  [
    "analysis",
    "debate",
    "architecture",
    "execution",
    "diagnosis",
    "retry",
    "consolidation"
  ]

def hivePhaseLines : List String :=
  hivePhases.map fun phase => "HIVE_PHASE|" ++ phase

def hiveBreakpoints : List String :=
  [
    "after_debate",
    "before_spawn",
    "after_diagnosis",
    "knowledge_consolidation"
  ]

def hiveBreakpointLines : List String :=
  hiveBreakpoints.map fun bp => "HIVE_BREAKPOINT|" ++ bp

end Nexus
