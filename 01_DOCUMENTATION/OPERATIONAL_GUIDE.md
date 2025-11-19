# NEXUS 2.0 - Operational Guide                                                                                                                                                              
## Unified Documentation for the Driver/Worker Architecture                                                                                                                                  
### Version 2.0 - November 19, 2025                                                                                                                                                          
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🎯 Executive Summary                                                                                                                                                                       
                                                                                                                                                                                             
NEXUS 2.0 is a dual-agent system designed for complex project management and technical execution. It leverages the complementary strengths of two AI systems:                                
                                                                                                                                                                                             
- **Gemini 3.0 (Driver)**: Strategic brain with 1M+ token context, handles planning and decision-making                                                                                      
- **Claude Code (Worker)**: Technical executor with superior coding abilities, handles all file system operations                                                                            
                                                                                                                                                                                             
This guide defines their relationship, communication protocols, and operational procedures.                                                                                                  
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🏗️ System Architecture                                                                                                                                                                     
                                                                                                                                                                                             
### The Driver/Worker Relationship                                                                                                                                                           
                                                                                                                                                                                             
```                                                                                                                                                                                          
┌─────────────────────────────────────────┐                                                                                                                                                  
│            USER INTERFACE               │                                                                                                                                                  
│         (gemini --yolo)                │                                                                                                                                                   
└────────────────┬────────────────────────┘                                                                                                                                                  
                 │                                                                                                                                                                           
                 ▼                                                                                                                                                                           
┌─────────────────────────────────────────┐                                                                                                                                                  
│         GEMINI 3.0 (DRIVER)            │                                                                                                                                                   
│   • Strategy & Planning (Brain)         │                                                                                                                                                  
│   • 1M+ Token Context                   │                                                                                                                                                  
│   • Decision Making                     │                                                                                                                                                  
│   • Project Orchestration               │                                                                                                                                                  
└────────────────┬────────────────────────┘                                                                                                                                                  
                 │                                                                                                                                                                           
            claude -p "..."                                                                                                                                                                  
                 │                                                                                                                                                                           
                 ▼                                                                                                                                                                           
┌─────────────────────────────────────────┐                                                                                                                                                  
│       CLAUDE CODE (WORKER)              │                                                                                                                                                  
│   • Code Execution (Hands)              │                                                                                                                                                  
│   • File System Operations              │                                                                                                                                                  
│   • Git Management                      │                                                                                                                                                  
│   • Testing & Validation                │                                                                                                                                                  
└─────────────────────────────────────────┘                                                                                                                                                  
```                                                                                                                                                                                          
                                                                                                                                                                                             
### Core Principle                                                                                                                                                                           
**Gemini thinks, Claude acts.** The Driver never touches files directly; the Worker never makes strategic decisions independently.                                                           
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 📡 Communication Protocol                                                                                                                                                                  
                                                                                                                                                                                             
### Driver → Worker Commands                                                                                                                                                                 
                                                                                                                                                                                             
The Driver communicates with the Worker exclusively through shell commands:                                                                                                                  
                                                                                                                                                                                             
```bash                                                                                                                                                                                      
claude -p "YOUR_PRECISE_INSTRUCTION"                                                                                                                                                         
```                                                                                                                                                                                          
                                                                                                                                                                                             
### Worker Response Format                                                                                                                                                                   
                                                                                                                                                                                             
The Worker must respond with structured reports:                                                                                                                                             
                                                                                                                                                                                             
```text                                                                                                                                                                                      
[WORKER REPORT]                                                                                                                                                                              
Action: [Description of action taken]                                                                                                                                                        
Status: [✅ SUCCESS / ❌ FAILURE]                                                                                                                                                              
Details: [Specific results, logs, or error messages]                                                                                                                                         
```                                                                                                                                                                                          
                                                                                                                                                                                             
### Command Examples                                                                                                                                                                         
                                                                                                                                                                                             
#### Simple File Operations                                                                                                                                                                  
```bash                                                                                                                                                                                      
# Read and summarize                                                                                                                                                                         
claude -p "Read the file src/main.py and summarize its functionality"                                                                                                                        
                                                                                                                                                                                             
# Create new file                                                                                                                                                                            
claude -p "Create a Python script at scripts/test.py that validates database connections"                                                                                                    
                                                                                                                                                                                             
# Modify existing file                                                                                                                                                                       
claude -p "Update config.json to include the new API endpoint settings"                                                                                                                      
```                                                                                                                                                                                          
                                                                                                                                                                                             
#### Complex Operations Protocol                                                                                                                                                             
                                                                                                                                                                                             
**CRITICAL**: Never pass complex code directly in the CLI command. Use the two-step protocol:                                                                                                
                                                                                                                                                                                             
1. **Driver writes draft to temp file**:                                                                                                                                                     
   ```python                                                                                                                                                                                 
   # Driver uses write_file() to create _TEMP/payload.sql                                                                                                                                    
   ```                                                                                                                                                                                       
                                                                                                                                                                                             
2. **Driver instructs Worker to use it**:                                                                                                                                                    
   ```bash                                                                                                                                                                                   
   claude -p "Take the SQL code from _TEMP/payload.sql and integrate it into database/migrations/001_init.sql"                                                                               
   ```                                                                                                                                                                                       
                                                                                                                                                                                             
This prevents shell escaping issues with quotes and special characters.                                                                                                                      
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🗄️ Directory Structure                                                                                                                                                                     
                                                                                                                                                                                             
### Clean Slate Organization                                                                                                                                                                 
                                                                                                                                                                                             
```                                                                                                                                                                                          
20_NEXUS/                                                                                                                                                                                    
├── 01_DOCUMENTATION/           # All project documentation                                                                                                                                  
│   ├── OPERATIONAL_GUIDE.md    # This file                                                                                                                                                  
│   └── SESSION_STATE_*.md      # Persistence files                                                                                                                                          
├── 02_SOURCE/                  # Source code                                                                                                                                                
│   ├── api/                    # API implementations                                                                                                                                        
│   ├── connectors/             # CEGID/MAINTI4 connectors                                                                                                                                   
│   └── tests/                  # Unit and integration tests                                                                                                                                 
├── 03_CONFIGS/                 # Configuration files                                                                                                                                        
│   ├── production/             # Production configs                                                                                                                                         
│   └── development/            # Dev/test configs                                                                                                                                           
├── 04_OUTPUTS/                 # Generated outputs                                                                                                                                          
│   ├── reports/                # Analysis reports                                                                                                                                           
│   └── logs/                   # Execution logs                                                                                                                                             
├── 05_ARCHIVES/                # Old versions and backups                                                                                                                                   
└── _TEMP/                      # Temporary working directory                                                                                                                                
    └── *.tmp                   # Ephemeral files                                                                                                                                            
```                                                                                                                                                                                          
                                                                                                                                                                                             
### Directory Rules                                                                                                                                                                          
                                                                                                                                                                                             
1. **_TEMP/** is for ephemeral work - cleared regularly                                                                                                                                      
2. **01_DOCUMENTATION/** contains all persistent knowledge                                                                                                                                   
3. **02_SOURCE/** is the single source of truth for code                                                                                                                                     
4. **Never create duplicate files** - use clear naming conventions                                                                                                                           
5. **Archive old versions** to 05_ARCHIVES/ before major changes                                                                                                                             
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🔄 CLI Persistence Protocol (The "Neural Link")

### The Fixed Session Strategy
To maintain a continuous "consciousness" across shell commands, we use a **Fixed UUID** strategy.

**Master Session ID**: `550e8400-e29b-41d4-a716-446655440000`
*(Defined in `20_NEXUS/00_CONFIG/session.conf`)*

### Command Syntax
Every command sent to Claude MUST use the `--resume` flag with this ID.

```bash
claude -p "YOUR_PROMPT" --resume "550e8400-e29b-41d4-a716-446655440000" --model claude-opus-4-1-20250805
```

### Why this works?
1.  **State on Disk**: The CLI tool saves conversation history in a local database keyed by the UUID.
2.  **Context Reload**: On each call, `--resume` loads the full history into the model's context window.
3.  **Continuity**: Claude "remembers" previous instructions, file reads, and architectural decisions.

### Recovery Procedure
If a command fails or crashes:
1.  Check `20_NEXUS/05_LOGS/CHAT_HISTORY_MASTER.md` for the last known state.
2.  Retry the command with the same UUID. The history is saved atomically on disk by the CLI tool.
3.  **DO NOT** create a new UUID, or memory will be lost.                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🛡️ Rules of Engagement                                                                                                                                                                     
                                                                                                                                                                                             
### Security Rules                                                                                                                                                                           
                                                                                                                                                                                             
1. **Destructive Operations**:                                                                                                                                                               
   - Worker must **refuse and warn** on dangerous commands (e.g., `rm -rf /`)                                                                                                                
   - Worker must confirm before bulk deletions (>10 files)                                                                                                                                   
   - Driver must justify any production data modifications                                                                                                                                   
                                                                                                                                                                                             
2. **Credential Management**:                                                                                                                                                                
   - Never commit credentials to git                                                                                                                                                         
   - Use environment variables or secure vaults                                                                                                                                              
   - Worker alerts on any hardcoded credentials detected                                                                                                                                     
                                                                                                                                                                                             
3. **Code Injection Prevention**:                                                                                                                                                            
   - Driver uses file-based approach for complex code                                                                                                                                        
   - Worker validates all SQL/script inputs before execution                                                                                                                                 
   - No direct evaluation of user-provided code                                                                                                                                              
                                                                                                                                                                                             
### No Hallucination Policy                                                                                                                                                                  
                                                                                                                                                                                             
1. **Driver Responsibilities**:                                                                                                                                                              
   - Only reference files that exist (verify first)                                                                                                                                          
   - Base decisions on actual project data, not assumptions                                                                                                                                  
   - Document sources for all technical decisions                                                                                                                                            
                                                                                                                                                                                             
2. **Worker Responsibilities**:                                                                                                                                                              
   - Report exact error messages, not interpretations                                                                                                                                        
   - Never guess file contents - read them first                                                                                                                                             
   - Return "File not found" rather than creating placeholder content                                                                                                                        
                                                                                                                                                                                             
3. **Verification Chain**:                                                                                                                                                                   
   ```                                                                                                                                                                                       
   Driver plans → Worker verifies → Worker executes → Worker reports → Driver validates                                                                                                      
   ```                                                                                                                                                                                       
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🎯 Operational Scenarios                                                                                                                                                                   
                                                                                                                                                                                             
### Scenario 1: Business Query                                                                                                                                                               
**User**: "What's the impact of CEGID V11 instability on our timeline?"                                                                                                                      
                                                                                                                                                                                             
**Driver Action**:                                                                                                                                                                           
1. Analyzes context from knowledge base                                                                                                                                                      
2. Responds directly with strategic assessment                                                                                                                                               
3. No Worker involvement needed                                                                                                                                                              
                                                                                                                                                                                             
### Scenario 2: Technical Implementation                                                                                                                                                     
**User**: "Create the CEGID connector module"                                                                                                                                                
                                                                                                                                                                                             
**Driver Action**:                                                                                                                                                                           
1. Designs architecture in mind                                                                                                                                                              
2. Writes specification to `_TEMP/cegid_spec.md`                                                                                                                                             
3. Commands: `claude -p "Create CEGID connector module based on spec in _TEMP/cegid_spec.md"`                                                                                                
4. Worker creates files in `02_SOURCE/connectors/cegid/`                                                                                                                                     
5. Driver validates Worker output                                                                                                                                                            
6. Driver reports completion to user                                                                                                                                                         
                                                                                                                                                                                             
### Scenario 3: Complex Debugging                                                                                                                                                            
**User**: "The API tests are failing"                                                                                                                                                        
                                                                                                                                                                                             
**Driver Action**:                                                                                                                                                                           
1. Commands: `claude -p "Run the API test suite and report all failures"`                                                                                                                    
2. Worker runs tests, reports errors                                                                                                                                                         
3. Driver analyzes error patterns                                                                                                                                                            
4. Driver creates fix strategy in `_TEMP/fix_plan.md`                                                                                                                                        
5. Commands: `claude -p "Apply fixes from _TEMP/fix_plan.md to the test files"`                                                                                                              
6. Worker applies fixes                                                                                                                                                                      
7. Commands: `claude -p "Re-run the API test suite"`                                                                                                                                         
8. Worker confirms tests pass                                                                                                                                                                
9. Driver reports resolution to user                                                                                                                                                         
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 📊 Performance Metrics                                                                                                                                                                     
                                                                                                                                                                                             
### System Capabilities                                                                                                                                                                      
                                                                                                                                                                                             
| Component | Metric | Value |                                                                                                                                                               
|-----------|--------|-------|                                                                                                                                                               
| **Gemini Driver** | Context Window | 1M+ tokens |                                                                                                                                          
| | Planning Accuracy | High |                                                                                                                                                               
| | Strategic Thinking | Excellent |                                                                                                                                                         
| **Claude Worker** | Code Generation | SWE-bench 77% |                                                                                                                                      
| | File Operations | 100% reliable |                                                                                                                                                        
| | Context Window | 200K tokens |                                                                                                                                                           
                                                                                                                                                                                             
### 3. Optimization Guidelines

1.  **Decision Threshold (Standard vs Complex)**:
    *   **Standard Tasks** (Git, File CRUD, Linting): **Driver Acts Directly**. Do not invoke Opus for trivialities.
    *   **Complex Tasks** (Architecture, Debugging unknown errors): **Invoke Opus** for reasoning.

2.  **Context Management**:
    *   Driver maintains global context   - Worker receives focused, specific tasks                                                                                                                                                 
   - Never overload Worker with unnecessary context                                                                                                                                          
                                                                                                                                                                                             
2. **Task Distribution**:                                                                                                                                                                    
   - Strategic decisions → Driver                                                                                                                                                            
   - Code writing → Worker                                                                                                                                                                   
   - File operations → Worker                                                                                                                                                                
   - Architecture design → Driver                                                                                                                                                            
   - Testing execution → Worker                                                                                                                                                              
   - Results analysis → Driver                                                                                                                                                               
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🚨 Emergency Procedures                                                                                                                                                                    
                                                                                                                                                                                             
### Worker Failure Recovery                                                                                                                                                                  
1. Driver analyzes Worker error message                                                                                                                                                      
2. Driver adjusts command syntax/approach                                                                                                                                                    
3. Driver retries with corrected instruction                                                                                                                                                 
4. If persistent: Driver documents issue in SESSION_STATE                                                                                                                                    
                                                                                                                                                                                             
### Context Loss Recovery                                                                                                                                                                    
1. Driver reads latest SESSION_STATE file                                                                                                                                                    
2. Driver verifies file system current state                                                                                                                                                 
3. Driver reconstructs context from documentation                                                                                                                                            
4. Driver continues operations                                                                                                                                                               
                                                                                                                                                                                             
### Critical Error Protocol                                                                                                                                                                  
1. Worker immediately stops on critical errors                                                                                                                                               
2. Worker reports exact error to Driver                                                                                                                                                      
3. Driver assesses impact and recovery options                                                                                                                                               
4. Driver implements recovery or escalates to user                                                                                                                                           
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 📅 Project Context Reference                                                                                                                                                               
                                                                                                                                                                                             
### MES iDACS Tanger Deployment                                                                                                                                                              
- **Solution**: myPlant.AI / iDACS                                                                                                                                                           
- **Client**: Motherson Aerospace                                                                                                                                                            
- **Timeline**: Oct 2025 - Jun 2026                                                                                                                                                          
- **Integrations**: CEGID V11 (ERP), MAINTI4 (GMAO)                                                                                                                                          
- **Objective**: Zero paper, OEE +15%, AS9100 compliance                                                                                                                                     
                                                                                                                                                                                             
### Key Milestones                                                                                                                                                                           
- ✅ Oct 31, 2025: Kickoff M0 completed                                                                                                                                                       
- 🔄 Dec 12, 2025: Design Freeze deadline                                                                                                                                                     
- 📅 Jun 19, 2026: Go-Live target                                                                                                                                                             
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 🔧 Maintenance Notes                                                                                                                                                                       
                                                                                                                                                                                             
### Daily Operations                                                                                                                                                                         
1. Clear `_TEMP/` directory at session start                                                                                                                                                 
2. Update SESSION_STATE after major milestones                                                                                                                                               
3. Commit code changes with descriptive messages                                                                                                                                             
4. Archive obsolete files to `05_ARCHIVES/`                                                                                                                                                  
                                                                                                                                                                                             
### Weekly Reviews                                                                                                                                                                           
1. Consolidate SESSION_STATE files                                                                                                                                                           
2. Update documentation with learnings                                                                                                                                                       
3. Refactor redundant code                                                                                                                                                                   
4. Review and optimize directory structure                                                                                                                                                   
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
## 📝 Version History                                                                                                                                                                         
                                                                                                                                                                                             
| Version | Date | Changes |                                                                                                                                                                 
|---------|------|---------|                                                                                                                                                                 
| 2.0 | 2025-11-19 | Unified guide created from three source documents |                                                                                                                     
| 1.0 | 2025-11-18 | Initial NEXUS architecture defined |                                                                                                                                    
                                                                                                                                                                                             
---                                                                                                                                                                                          
                                                                                                                                                                                             
*End of Operational Guide*                                                                                                                                                                   
*NEXUS 2.0 - Gemini Driver + Claude Worker*                                                                                                                                                  
*Validated by Yann ABADIE - Project Architect*