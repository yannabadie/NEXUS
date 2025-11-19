# 📅 NEXT SESSION PLAN

**Objective:** Finalize MCP Integration & Activate Learning Loop.

## 1. Immediate Fixes (First 10 mins)
- [ ] **Fix SSE Route:** Apply the fix described in `05_LOGS/ISSUES.md` to `server_sse.py`.
- [ ] **Verify Fix:** Run `start_sse_server.bat` then `python test_client_sse.py`. Expect `✅ 42`.

## 2. Phase 1 Implementation
- [ ] **Port 'Planning' Agent:** Convert `15_POC_ACE_COMPASS/03_Scripts_POC/compass_agent_planning.py` into an MCP Tool (`20_NEXUS/03_AGENTS/compass_mcp/tools/planning.py`).
- [ ] **Connect ChromaDB:** Implement the vector DB connector in the new MCP environment.

## 3. Enable Learning Loop
- [ ] **Log Analysis:** Create a script to parse `CHAT_HISTORY_MASTER.md` and extract successful patterns.
- [ ] **Playbook Generation:** Automate the creation of new agent strategies based on logs.

## 4. Protocol Reminder
- Always use `swarm.py` for heavy tasks.
- Always verify code execution (don't trust "✅ SUCCESS" blindly).
- Use `uv` for all package management.
