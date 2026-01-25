import Nexus.FSM
import Nexus.HiveMind
import Nexus.Swarm
import Nexus.Evolution

open Nexus

def exportLines : List String :=
  fsmLines ++ activeLines ++ swarmLines ++ hiveStateLines ++ hivePhaseLines ++ hiveBreakpointLines ++ evolutionPhaseLines

def main : IO Unit := do
  for line in exportLines do
    IO.println line
