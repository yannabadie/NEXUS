import Nexus.FSM
import Nexus.HiveMind
import Nexus.Swarm
import Nexus.Evolution
import Nexus.Invariants

open Nexus

def exportLines : List String :=
  fsmLines ++ activeLines ++ swarmLines ++ hiveStateLines ++ hivePhaseLines ++ hiveBreakpointLines ++ evolutionPhaseLines ++ invariantLines

def main : IO Unit := do
  for line in exportLines do
    IO.println line
