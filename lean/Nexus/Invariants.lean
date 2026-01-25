import Std

namespace Nexus

structure Invariant where
  name : String
  description : String

def invariants : List Invariant :=
  [
    { name := "tenant_isolation",
      description := "ServiceFactory returns distinct instances per tenant context." },
    { name := "workspace_isolation",
      description := "Workspace paths remain scoped to tenant/workspace identifiers." },
    { name := "cancellation_propagation",
      description := "Parent CancellationToken cancellation propagates to children." },
    { name := "event_delivery",
      description := "Published events reach in-memory subscribers or are rejected." }
  ]

def invariantLines : List String :=
  invariants.map fun inv => "INVARIANT|" ++ inv.name ++ "|" ++ inv.description

end Nexus
