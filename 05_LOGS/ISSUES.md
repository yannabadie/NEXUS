# 🐛 NEXUS OPEN ISSUES

## 🔴 CRITICAL: MCP SSE Handshake Failure (405)

**Status:** OPEN
**Date:** 2025-11-19
**Component:** `20_NEXUS/03_AGENTS/mcp_skeleton/server_sse.py`

### Description
The MCP Client fails to connect to the SSE Server with `httpx.HTTPStatusError: 405 Method Not Allowed`.

### Root Cause Analysis
The Starlette route `/mcp/v1/sse` is configured to accept only `POST` methods.
Server-Sent Events (SSE) protocol initiates connection via a `GET` request.

**Faulty Code (Lines 123-126):**
```python
Route("/mcp/v1/sse",
      endpoint=mcp_server.handle_sse,
      methods=["POST"]),  # <--- ERROR: Missing GET
```

### Fix Plan
1. Update `server_sse.py`: Change `methods=["POST"]` to `methods=["GET", "POST"]`.
2. Restart Server.
3. Re-run `test_client_sse.py`.

---

## 🟡 WARNING: Auto-generated Code Quality
**Status:** OPEN
**Component:** `swarm.py`, `nexus_daemon.py`

The autonomous code generation by Claude (Worker) sometimes creates subtly broken code (wrong imports, missing methods).
**Action:** Always enforce a "Test & Verify" step (Driver side) before validating a task.
