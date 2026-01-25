import Std

namespace Nexus

inductive CollaborationMode
  | parallel
  | sequential
  | lead_support
  | ping_pong
  | specialist
  | red_blue
  deriving Repr, DecidableEq

def modeToString : CollaborationMode -> String
  | .parallel => "PARALLEL"
  | .sequential => "SEQUENTIAL"
  | .lead_support => "LEAD_SUPPORT"
  | .ping_pong => "PING_PONG"
  | .specialist => "SPECIALIST"
  | .red_blue => "RED_BLUE"

def fallbackMap : List (CollaborationMode × Option CollaborationMode) :=
  [
    (.parallel, some .sequential),
    (.red_blue, some .lead_support),
    (.lead_support, some .specialist),
    (.ping_pong, some .sequential),
    (.sequential, some .specialist),
    (.specialist, none)
  ]

def swarmLines : List String :=
  fallbackMap.map fun (entry : CollaborationMode × Option CollaborationMode) =>
    let nextStr := match entry.2 with
      | some mode => modeToString mode
      | none => "none"
    "SWARM|" ++ modeToString entry.1 ++ "|" ++ nextStr

end Nexus
