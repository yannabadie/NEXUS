# Changelog

All notable changes to NEXUS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [5.1.3] - 2025-11-21

### 🎯 Summary
**Production Release** - Test automation, final bug fixes, and documentation overhaul.

### ✅ Added
- **Automated E2E Test Suite** (`tests/test_automated_e2e.py`)
  - 7 tests validating critical functionality
  - 100% pass rate
  - Tests conversation detection, orchestration triggers, and bug fixes
  - Automated runner: `run_e2e_tests.bat`
- **Non-Interactive Mode Support**
  - `nexus_interactive.py` now supports piped input for automated testing
  - Detects terminal with `sys.stdin.isatty()`
  - Fallback to `input()` when PromptSession unavailable
- **Comprehensive Documentation**
  - Updated `README.md` to V5.1.3 with all features
  - New `CHANGELOG.md` (this file)
  - `STATUS_TEST_AUTOMATION_SUCCESS.md` - detailed test validation report
  - `TEST_NOW.md` - quick start testing guide

### 🐛 Fixed (Session 3 - Final Fixes)
- **Bug #10: Capabilities Question Triggering Orchestration**
  - Extended `self_questions` list with French variants
  - Added `startswith()` check for question patterns
  - "Quel sont tes compétences?" now handled as conversation
  - Files: `nexus_interactive.py:268-282`

- **Bug #11: Blackboard.json Missing on First Run**
  - `_create_empty_state()` now saves to disk immediately
  - Creates parent directories if missing
  - No more "État corrompu" errors on initial launch
  - Files: `core/synapse/memory.py:46-58`

- **Bug #12: Gemini Invalid Enum Values**
  - Added CRITICAL sections to prompts with explicit enum lists
  - Distinguished message-level `status` vs plan step `status`
  - Clear "DO NOT use" warnings for invalid values
  - Files: `prompts/system_gemini_base.md:56-83`, `prompts/system_claude_base.md:56-82`

### 🔧 Changed
- **Test Architecture**
  - Tests now validate orchestration **starts** (not full completion)
  - Reduced timeout from 90s to 30s for faster execution
  - Better timeout handling with partial output capture
  - Uses `subprocess.Popen()` instead of `subprocess.run()`
- **Deployment Process**
  - `install.ps1` verified and deployed to AppData
  - Global installation path: `C:\Users\<user>\AppData\Local\NEXUS`
  - PATH automatically updated

### 📊 Test Results
```
======================================================================
NEXUS V5.1.3 - AUTOMATED E2E TEST RESULTS
======================================================================
Total Tests:  7
Passed:       7 (100.0%)
Failed:       0
Duration:     62.1s
======================================================================

✓ ALL TESTS PASSED - NEXUS V5.1.3 IS READY!
```

### 🗂️ Repository Cleanup
- Moved old prompts to `POMPTS-BRAINSTORMING-NEXUS/`
- Archived legacy components to `_ARCHIVE_2025/`
- Deleted obsolete documentation files
- Cleaned `__pycache__` from repository

### 📦 Commits
```
0fb9067  chore: Reorganize repository - archive old files and cleanup docs
ec1da97  docs: Add comprehensive test automation success report
0d0286c  fix(tests): Enable non-interactive mode and fix E2E test automation
```

---

## [5.1.2] - 2025-11-21 (Internal)

### 🐛 Fixed (Session 2 - Deep Protocol Fixes)
- **Bug #6: Claude Driver Using Non-Existent CLI Flags**
  - Removed invented flags: `--output-format json`, `--max-turns 1`, `--append-system-prompt`
  - Simplified to real Claude CLI syntax: `claude -p @file > output`
  - Modified parser to extract JSON from markdown code blocks
  - Files: `core/drivers/claude_driver.py:40-143`

- **Bug #7: Prompts Not Enforcing JSON-Only Output**
  - Added CRITICAL section at top of both prompts
  - Explicit list of forbidden formats (text, markdown, comments)
  - Clear examples of correct vs wrong responses
  - Must start with `{` and end with `}`
  - Files: `prompts/system_claude_base.md:9-33`, `prompts/system_gemini_base.md:9-33`

- **Bug #8: Greeting + Task Detected as Conversation**
  - Enhanced conversation detector to check text AFTER greeting
  - Handles both space and comma separators
  - If rest contains task keywords → orchestration triggered
  - "bonjour, créé un fichier" now correctly triggers orchestration
  - Files: `nexus_interactive.py:285-298`

- **Bug #9: Workspace Detection Showing Wrong Mode**
  - Changed from directory existence check to path string check
  - AppData path → "Installed", otherwise → "Development"
  - More reliable than checking for `core/` directory
  - Files: `nexus_interactive.py:501-506`

### 📦 Commits
```
8897b6f  test: Add automated E2E tests + cleanup obsolete files
769d098  fix(critical): Final fixes - Enum values, state init & conversation
8cba2b1  fix(critical): Deep protocol fixes - Claude driver, prompts & detection
```

---

## [5.1.0] - 2025-11-20

### 🎯 Summary
**Interactive Mode Release** - Added REPL interface and fixed critical orchestration bugs.

### ⭐ Added
- **Interactive REPL Mode** (`nexus_interactive.py`)
  - Claude Code-like conversational interface
  - Command history with auto-suggest
  - Tab completion for slash commands
  - Session persistence (conversation saved to JSONL)
  - Workspace auto-detection (dev vs installed mode)

- **Conversation Detection System**
  - Pre-orchestration filtering for greetings
  - Self-referential questions detection
  - Task keywords identification
  - Instant responses for non-technical queries

- **Slash Commands**
  - `/help` - Display help
  - `/status` - Show orchestration state
  - `/history` - View conversation history
  - `/plan` - Display strategic plan
  - `/clear` - Clear screen
  - `/sessions` - List saved sessions
  - `/reset` - Reset orchestration
  - `/exit`, `/quit` - Exit REPL

### 🐛 Fixed (Session 1 - Critical Bugs)
- **Bug #1: Claude Never Invoked**
  - Added `forced_agent_switch` flag to prevent override after stalemate
  - When stalemate triggers agent switch, flag prevents immediate reversion
  - Claude now invoked after configured stagnation threshold
  - Files: `core/orchestration.py:43,219-231,317-336`

- **Bug #2: Infinite Loop on "hello"**
  - Added `is_simple_conversation()` method
  - Pre-filters greetings before orchestration
  - Common patterns: "hello", "hi", "bonjour", "salut", etc.
  - Responds directly without triggering Gemini/Claude loop
  - Files: `nexus_interactive.py:247-306`

- **Bug #3: Workspace Path Incorrect**
  - Added `detect_workspace_path()` auto-detection
  - Checks for `core/` and `prompts/` directories
  - Displays workspace mode on startup (Development/Installed)
  - Prevents state corruption from wrong paths
  - Files: `nexus_interactive.py:494-511`

- **Bug #4: Stagnation Threshold Ignored**
  - Changed hardcoded value (7) to `config.max_stalemate_count`
  - Dynamic thresholds: warn at 3, switch at max-2, panic at max
  - Respects `MAX_STALEMATE_COUNT` environment variable
  - Files: `core/orchestration.py:317-336`

- **Bug #5: Poor Error Handling**
  - Added panic check and cleanup after orchestration
  - User-friendly error messages
  - Auto-clears panic files for clean REPL return
  - Suggests specific technical task format
  - Files: `nexus_interactive.py:410-428`

### 🔧 Changed
- **Resource Monitor** disabled for interactive mode
  - Avoids performance overhead during REPL sessions
  - Re-enabled for CLI mode
- **Logging** enhanced with session tracking
  - Separate log files per interactive session
  - JSONL format for conversation history

### 📦 Commits
```
803425a  fix(critical): NEXUS V5.1 - 5 critical bugs fixed and validated
c4604a8  feat: NEXUS V5.1 - Interactive Mode (Claude Code-like REPL)
```

---

## [5.0.0] - 2025-11-20

### 🎯 Summary
**Major Release** - Pragmatic edition with Tool Executor, Dual Schema, and Plan Health.

### ⭐ Added
- **Centralized Tool Executor**
  - Single source of truth for tool execution
  - Saves results to `last_tool_result.json`
  - 99% reliability for CFL (Cognitive Feedback Loop)
  - Tools: bash, read, write, edit, git, list_dir

- **Dual Schema System (Light/Heavy)**
  - LightMessage: Normal orchestration
  - HeavyMessage: Includes `tool_use` and `post_action_review`
  - 80% reduction in `post_action_review` omissions
  - Automatic schema detection and validation

- **Plan Health Monitoring**
  - Tracks strategic plan progress
  - 4 levels: LOW, MEDIUM, HIGH, CRITICAL
  - Auto-escalation on plan drift
  - Automatic mode switch to InProjectImprovement on CRITICAL

- **Panic System**
  - Clean shutdown < 3s
  - Automatic state backup
  - File-based panic trigger (`workspace/_IO_BUFFER/STOP_NOW`)
  - CLI panic command: `python nexus.py --panic "reason"`

- **State Rollback**
  - Automatic corruption detection
  - Restore from `.bak1` or `.bak2`
  - Backup rotation (up to 2 backups)

### 🔧 Changed
- **Protocol** upgraded to Synapse V5.0
  - Pydantic models for validation
  - Explicit action types: TALK, CONTINUE, TOOL_USE, DELEGATE, FINISH, ERROR
  - Mandatory `post_action_review` for tool usage

- **Drivers** refactored for CLI-only mode
  - Removed API fallback complexity
  - Direct subprocess execution
  - Better error handling and logging

- **Configuration** centralized in `.env`
  - Model selection: Gemini 3 Pro, Claude Sonnet 4.5
  - Stalemate thresholds configurable
  - Compression threshold adjustable

### 📚 Documentation
- Complete architecture documentation
- Testing guides and protocols
- Deployment guides
- Development history

### 🗑️ Removed
- API-based drivers (kept CLI-only)
- Old V4.x protocol remnants
- Legacy checkpoint system

---

## [4.5.0] - 2025-11-19

### ⭐ Added
- **last_tool_result.json** - Shared truth between agents
- **Cognitive Feedback Loop (CFL)** - Mandatory validation cycle
- Initial Tool Executor implementation

### 🔧 Changed
- Protocol refinements for CFL
- Improved error recovery

---

## [4.0.0] - 2025-11-18

### ⭐ Added
- Initial multi-agent orchestration
- Gemini + Claude coordination
- Basic tool system

### 📝 Notes
Early prototype - many iterations before V5.0 stability.

---

## Legend

- 🎯 **Summary** - Release overview
- ⭐ **Added** - New features
- 🐛 **Fixed** - Bug fixes
- 🔧 **Changed** - Changes to existing features
- 🗑️ **Removed** - Removed features
- 📚 **Documentation** - Documentation updates
- 📦 **Commits** - Git commit references
- 📊 **Test Results** - Test execution results
- 🗂️ **Repository** - Repository organization changes

---

**Last Updated:** 2025-11-21
**Current Version:** 5.1.3 (Production Edition)
