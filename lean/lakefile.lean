import Lake
open Lake DSL

package nexus where

lean_lib Nexus

@[default_target]
lean_exe nexus_oracle where
  root := `Main
