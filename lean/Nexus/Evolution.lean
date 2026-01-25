import Std

namespace Nexus

inductive EvolutionPhaseStatus
  | pending
  | in_progress
  | completed
  | failed
  | skipped
  deriving Repr, DecidableEq

def evolutionPhaseToString : EvolutionPhaseStatus -> String
  | .pending => "pending"
  | .in_progress => "in_progress"
  | .completed => "completed"
  | .failed => "failed"
  | .skipped => "skipped"

def evolutionPhaseLines : List String :=
  [
    .pending,
    .in_progress,
    .completed,
    .failed,
    .skipped
  ].map fun phase => "EVOLUTION_PHASE|" ++ evolutionPhaseToString phase

end Nexus
