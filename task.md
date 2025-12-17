# Cycle 005: Standardization (Refactoring)

**Goal**: Upgrade `core/bootstrap/agent_loader.py` to return `AgentDescriptor` (V12.4) instead of `AgentProfile` (Legacy).

- [ ] **Analysis**
    - [ ] Compare `AgentProfile` vs `AgentDescriptor` attributes.
    - [ ] Identify all call sites of `discover_and_register_spawned_agents`.

- [ ] **Implementation**
    - [ ] Refactor `core/bootstrap/agent_loader.py` to use `AgentDescriptor`.
    - [ ] Implement `_map_capabilities` helper to convert strings to `AgentCapability` Enum.
    - [ ] Update `discover_and_register_spawned_agents` to use `UnifiedAgentRegistry`.

- [ ] **Verification**
    - [ ] Update `verify_genesis.py` to remove adapter logic.
    - [ ] Run `verify_genesis.py` to confirm native compatibility.
    - [ ] Ensure `python_specialist` is still correctly loaded.
