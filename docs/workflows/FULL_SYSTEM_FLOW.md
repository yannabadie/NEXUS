# NEXUS Full System Flow

**Version**: 12.4 | **Last Updated**: 2025-12-16

End-to-end flow from user input to final result, showing how frontend and backend interact.

---

## Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NEXUS FULL SYSTEM FLOW                                  │
│                     From User Input to Result                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (CEREBRO)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  User types task in MissionControl                                          │
│  "Implement a login form with validation"                                   │
│        │                                                                    │
│        │ Select mode: LEAD_SUPPORT                                          │
│        │ Click ENGAGE                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ POST /api/workflow/start                                             │   │
│  │ Headers: Authorization: Bearer <jwt>                                 │   │
│  │ Body: { task: "...", mode: "LEAD_SUPPORT" }                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        │                                                                    │
│ ═══════╪════════════════════════════════════════════════════════════════   │
│        │              HTTP REQUEST                                          │
│ ═══════╪════════════════════════════════════════════════════════════════   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         BACKEND (CEREBRO API)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ JWT Validation  │──▶ Verify token, extract user                         │
│  │ (IRONCLAD)      │                                                       │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ Rate Limiter    │──▶ Check 100 req/min limit                            │
│  │ (V12.1)         │                                                       │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATOR V7 (FSM)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        │ process_turn(user_input)                                           │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ FSM Transition  │──▶ IDLE → BRAINSTORMING                               │
│  │                 │    Emit: fsm.state_changed                            │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      TASK ANALYZER                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        │ Analyze: complexity, domains, agent fit scores                     │
│        │                                                                    │
│        ├─────────────────────────────────────────────────────────────────  │
│        │ TRIVIAL?                                                           │
│        │    │                                                               │
│        │    └──▶ Direct execution (single agent)                           │
│        │                                                                    │
│        ├─────────────────────────────────────────────────────────────────  │
│        │ MODERATE+?                                                         │
│        │    │                                                               │
│        │    ▼                                                               │
│        │  ┌─────────────────────────────────────────────────────────────┐  │
│        │  │                 ROUTE DECISION                               │  │
│        │  │   Mode specified?  ────────────────▶ Use Swarm Engine        │  │
│        │  │   Auto-route?      ────────────────▶ HiveMind or Swarm       │  │
│        │  └─────────────────────────────────────────────────────────────┘  │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │            HYBRID SWARM ENGINE (Mode: LEAD_SUPPORT)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ Mode Selector   │──▶ Select Lead (Claude Opus) + Support (Gemini 3 Pro)│
│  │ (DyLAN scores)  │    Emit: swarm.mode_selected                          │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                 LEAD_SUPPORT EXECUTOR                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        │  ┌─────────────────────────────────────────────────────────────┐  │
│        │  │ LEAD (Claude Opus)                                          │  │
│        │  │ - Analyze requirements                                      │  │
│        │  │ - Design component structure                                │  │
│        │  │ - Implement login form                                      │  │
│        │  └─────────────────────────────────────────────────────────────┘  │
│        │        │                                                           │
│        │        │ Needs tool: write                                         │
│        │        ▼                                                           │
│        │  ┌─────────────────┐                                              │
│        │  │ Tool Execution  │                                              │
│        │  │                 │                                              │
│        │  │ ┌─────────────┐ │                                              │
│        │  │ │ InputGuard  │ │──▶ Sanitize inputs                           │
│        │  │ └─────────────┘ │                                              │
│        │  │ ┌─────────────┐ │                                              │
│        │  │ │ PathGuard   │ │──▶ Validate file path                        │
│        │  │ └─────────────┘ │                                              │
│        │  │ ┌─────────────┐ │                                              │
│        │  │ │ FileHandler │ │──▶ Write src/LoginForm.tsx                   │
│        │  │ └─────────────┘ │                                              │
│        │  │ ┌─────────────┐ │                                              │
│        │  │ │ OutputGuard │ │──▶ Check output safety                       │
│        │  │ └─────────────┘ │    Emit: tool.execution_completed            │
│        │  └─────────────────┘                                              │
│        │        │                                                           │
│        │        │ FSM: EXECUTING_TOOL → VALIDATING_CFL                      │
│        │        ▼                                                           │
│        │  ┌─────────────────────────────────────────────────────────────┐  │
│        │  │ SUPPORT (Gemini 3 Pro) - Review                             │  │
│        │  │ - Check code quality                                        │  │
│        │  │ - Suggest improvements                                      │  │
│        │  │ - Validate security                                         │  │
│        │  └─────────────────────────────────────────────────────────────┘  │
│        │        │                                                           │
│        │        │ Review passed                                             │
│        │        ▼                                                           │
│        │  ┌─────────────────┐                                              │
│        │  │ Continue or     │                                              │
│        │  │ Complete?       │                                              │
│        │  └─────────────────┘                                              │
│        │        │                                                           │
│        │        │ More work needed → Loop back to LEAD                      │
│        │        │ Complete → Consolidate                                    │
│        │        ▼                                                           │
│        │  ┌─────────────────────────────────────────────────────────────┐  │
│        │  │ CONSOLIDATION                                               │  │
│        │  │ - Merge all outputs                                         │  │
│        │  │ - Generate summary                                          │  │
│        │  │ - Record to SuccessMemory                                   │  │
│        │  └─────────────────────────────────────────────────────────────┘  │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ FSM Transition  │──▶ → WAITING_USER                                     │
│  │                 │    Emit: fsm.state_changed, workflow.completed        │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        │                                                                    │
│ ═══════╪════════════════════════════════════════════════════════════════   │
│        │              WEBSOCKET EVENTS                                      │
│ ═══════╪════════════════════════════════════════════════════════════════   │
│        │                                                                    │
│        │ (Throughout execution, events stream to frontend)                  │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (CEREBRO)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ EventStream     │──▶ Display all events in real-time                    │
│  │ component       │    User sees progress                                 │
│  └─────────────────┘                                                       │
│        │                                                                    │
│        ▼                                                                    │
│  ┌─────────────────┐                                                       │
│  │ Final Result    │──▶ "Login form created at src/LoginForm.tsx"          │
│  │ displayed       │    with validation and styling                        │
│  └─────────────────┘                                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Event Timeline Example

```
T+0ms     │ frontend  │ POST /api/workflow/start
T+50ms    │ backend   │ JWT validated, rate check passed
T+100ms   │ websocket │ { type: "fsm.state_changed", payload: { from: "IDLE", to: "BRAINSTORMING" } }
T+150ms   │ backend   │ TaskAnalyzer: MODERATE complexity, CODING domain
T+200ms   │ websocket │ { type: "swarm.mode_selected", payload: { mode: "LEAD_SUPPORT", lead: "claude" } }
T+300ms   │ backend   │ Claude Opus analyzing requirements
T+1500ms  │ websocket │ { type: "tool.execution_started", payload: { tool: "write", path: "src/LoginForm.tsx" } }
T+2000ms  │ websocket │ { type: "tool.execution_completed", payload: { tool: "write", success: true } }
T+2100ms  │ websocket │ { type: "fsm.state_changed", payload: { from: "EXECUTING_TOOL", to: "VALIDATING_CFL" } }
T+3000ms  │ backend   │ Gemini 3 Pro reviewing code
T+3500ms  │ websocket │ { type: "swarm.review_complete", payload: { approved: true } }
T+4000ms  │ websocket │ { type: "workflow.completed", payload: { success: true, files_created: 1 } }
T+4050ms  │ websocket │ { type: "fsm.state_changed", payload: { from: "VALIDATING_CFL", to: "WAITING_USER" } }
```

---

## Error Handling Flow

```
Normal Flow                          Error Flow
    │                                    │
    ▼                                    ▼
Execution                          Execution fails
    │                                    │
    ▼                                    ▼
Success                            ┌─────────────────┐
    │                              │ Phase 5:        │
    ▼                              │ DIAGNOSIS       │
WAITING_USER                       │ (error analysis)│
                                   └─────────────────┘
                                         │
                                         ▼
                                   ┌─────────────────┐
                                   │ Phase 6:        │
                                   │ RETRY           │
                                   │ (max 3 attempts)│
                                   └─────────────────┘
                                         │
                                   ┌─────┴─────┐
                                   │           │
                              Retry OK    Retry failed
                                   │           │
                                   ▼           ▼
                              WAITING_USER   ERROR state
                                               │
                                               ▼
                                         User: /reset
                                               │
                                               ▼
                                             IDLE
```

---

## Fallback Chain Example

```
Selected mode: RED_BLUE (adversarial)
    │
    ▼
RED_BLUE execution fails (agents can't reach consensus)
    │
    ▼
Self-Healing: Try LEAD_SUPPORT
    │
    ▼
LEAD_SUPPORT execution fails (lead encounters error)
    │
    ▼
Self-Healing: Try SPECIALIST
    │
    ▼
SPECIALIST succeeds (single expert completes task)
    │
    ▼
Result returned to user
```

---

## Memory Integration

```
Task Completed
    │
    ▼
┌───────────────────────────────────┐
│ SuccessMemory.record()            │
│                                   │
│ Stored:                           │
│ - Task description                │
│ - Selected mode                   │
│ - Agent performance               │
│ - Tool sequence                   │
│ - Success/failure                 │
└───────────────────────────────────┘
    │
    ▼
Next similar task
    │
    ▼
┌───────────────────────────────────┐
│ ModeSelector uses SuccessMemory   │
│                                   │
│ - Check past success patterns     │
│ - Adjust DyLAN scores             │
│ - Select optimal mode             │
└───────────────────────────────────┘
```

---

*Full System Flow V12.4 - NEXUS Documentation*
