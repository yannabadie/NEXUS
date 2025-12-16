# NEXUS Workflow Map

> Generated: 2025-12-16

## Architecture Overview

```mermaid
graph TB
    subgraph Entry Points
        CLI[nexus7.py CLI]
        API[FastAPI /api/chat]
        WS[WebSocket /ws/logs]
    end
    
    subgraph Orchestration Layer
        OV7[OrchestratorV7<br/>FSM + Main Loop]
        HSE[HybridSwarmEngine<br/>Multi-Agent Coordination]
        THM[TrueHiveMind<br/>7-Phase Pipeline]
    end
    
    subgraph Drivers
        GD[GeminiDriverV7]
        CD[ClaudeDriverV7]
    end
    
    subgraph Tools & Execution
        TM[ToolManager]
        AR[AgentRegistry]
    end
    
    CLI --> OV7
    API --> OV7
    OV7 --> HSE
    OV7 --> THM
    HSE --> GD
    HSE --> CD
    THM --> GD
    THM --> CD
    GD --> TM
    CD --> TM
    TM --> AR
```

---

## Backend Flows

### 1. User Message Flow (Simple Task)
```mermaid
sequenceDiagram
    participant User
    participant REPL as nexus7.py REPL
    participant OV7 as OrchestratorV7
    participant TA as TaskAnalyzer
    participant Driver as Gemini/Claude
    
    User->>REPL: "Hello"
    REPL->>OV7: process_turn(input)
    OV7->>TA: analyze(input)
    TA-->>OV7: complexity=TRIVIAL
    OV7->>Driver: send_message()
    Driver-->>OV7: response
    OV7-->>REPL: {output, agent, state}
    REPL-->>User: Display response
```

### 2. Swarm Flow (Moderate Task)
```mermaid
sequenceDiagram
    participant User
    participant OV7 as OrchestratorV7
    participant HSE as HybridSwarmEngine
    participant MS as ModeSelector
    participant NP as NegotiationProtocol
    participant EX as ModeExecutor
    
    User->>OV7: Complex task
    OV7->>HSE: process_task()
    HSE->>MS: select_mode(analysis)
    MS-->>HSE: PING_PONG mode
    HSE->>NP: negotiate()
    NP-->>HSE: agents_agree
    HSE->>EX: execute()
    EX-->>HSE: result
    HSE-->>OV7: SwarmResult
```

### 3. HiveMind Flow (Complex Task)
```mermaid
sequenceDiagram
    participant User
    participant FSM as FSMHandlers
    participant THM as TrueHiveMind
    participant P1 as Phase1:Analysis
    participant P2 as Phase2:Debate
    participant P3 as Phase3:Architecture
    participant P4 as Phase4:Execution
    participant P5 as Phase5:Diagnosis
    participant P6 as Phase6:Retry
    participant P7 as Phase7:Consolidation
    
    User->>FSM: Complex task
    FSM->>THM: process_task()
    
    THM->>P1: analyze()
    P1-->>THM: AnalysisResult
    
    THM->>P2: debate()
    P2-->>THM: DebateResult
    
    THM->>P3: generate_architecture()
    P3-->>THM: ArchitectureResult
    
    THM->>P4: execute()
    alt Success
        P4-->>THM: ExecutionResult
        THM->>P7: consolidate()
    else Failure
        P4-->>THM: ExecutionFailed
        THM->>P5: diagnose()
        P5-->>THM: Diagnosis
        THM->>P6: retry()
        P6->>P4: re-execute
    end
    
    THM-->>FSM: HiveMindResult
```

---

## Frontend Flows

### 4. Dashboard Connection Flow
```mermaid
sequenceDiagram
    participant Browser
    participant Next as Next.js App
    participant WS as WebSocket Hook
    participant API as FastAPI Backend
    
    Browser->>Next: Load page
    Next->>WS: useNexusWebSocket()
    WS->>API: Connect ws://8000/ws/logs
    API-->>WS: Connection OK
    
    loop Every event
        API->>WS: {type, data}
        WS->>Next: setExchanges()
        Next->>Browser: Render update
    end
```

### 5. Frontend Routes
| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | page.tsx | Dashboard overview |
| `/chat` | ChatPanel + AgentExchanges | Chat interface |
| `/hivemind` | HiveMindTracker + DebateViewer | Phase visualization |
| `/agents` | AgentConstellation + SpawnModal | Agent management |
| `/analytics` | BudgetGauge + EvolutionTree | Metrics |
| `/settings` | Settings form | Configuration |

---

## E2E Flows

### 6. Spawn Agent Flow
```mermaid
sequenceDiagram
    participant User
    participant UI as Frontend /agents
    participant API as POST /api/agents
    participant FS as workspace/agents/
    participant WS as WebSocket
    
    User->>UI: Click "Spawn Agent"
    UI->>UI: Open SpawnAgentModal
    User->>UI: Fill form + Submit
    UI->>API: POST {name, mission, capabilities}
    API->>FS: Create agent.json
    API->>WS: Broadcast AGENT_SPAWNED
    WS-->>UI: Event received
    UI->>UI: fetchData() - refresh list
```

### 7. Chat Message Flow
```mermaid
sequenceDiagram
    participant User
    participant UI as ChatPanel
    participant API as POST /api/chat
    participant OV7 as OrchestratorV7
    participant EB as EventBus
    participant WS as WebSocket
    
    User->>UI: Type message + Send
    UI->>API: POST {content}
    API->>OV7: invoke_agent()
    OV7->>EB: publish(AGENT_RESPONSE)
    EB->>API: POST /api/telemetry
    API->>WS: broadcast()
    WS-->>UI: Event in AgentExchanges
```

---

## Module Inventory

### Backend Core Modules (30)
| Module | Purpose | Has README |
|--------|---------|------------|
| `adapters/` | External service adapters | ❌ |
| `agents/` | Agent registry & descriptors | ❌ |
| `api/` | Internal API definitions | ✅ |
| `async_primitives/` | Async utilities | ❌ |
| `bootstrap/` | Startup & agent discovery | ❌ |
| `drivers/` | Gemini/Claude drivers | ❌ |
| `evolution/` | Self-improvement system | ❌ |
| `execution/` | Tool execution layer | ❌ |
| `fsm/` | Finite State Machine | ❌ |
| `governance/` | Rate limiting, policies | ❌ |
| `hive_mind/` | 7-phase orchestration | ✅ |
| `interface/` | CLI commands | ❌ |
| `io/` | File I/O primitives | ✅ |
| `logging/` | Structured logging | ❌ |
| `mcp/` | Model Context Protocol | ❌ |
| `memory/` | RAG & knowledge base | ❌ |
| `meta/` | Metaprogramming utils | ❌ |
| `notifications/` | Alert system | ❌ |
| `orchestration/` | Agent invoker, context | ❌ |
| `prompts/` | System prompts | ❌ |
| `reasoning/` | Chain-of-thought | ❌ |
| `routing/` | Model routing | ❌ |
| `security/` | Input/output guards | ❌ |
| `swarm/` | Multi-agent collaboration | ✅ |
| `synapse/` | Blackboard memory | ❌ |
| `telemetry/` | Metrics & budget | ❌ |
| `ui/` | Dashboard server | ❌ |
| `utils/` | Helper functions | ❌ |
| `workspace/` | Project management | ❌ |

### Frontend Modules (5)
| Module | Purpose | Has README |
|--------|---------|------------|
| `app/` | Next.js routes | ❌ |
| `components/` | UI components | ❌ |
| `hooks/` | Custom React hooks | ❌ |
| `lib/` | API client, design tokens | ❌ |
| `stores/` | Global state (chat) | ❌ |

---

*This document will be expanded as Phase 4 progresses.*
