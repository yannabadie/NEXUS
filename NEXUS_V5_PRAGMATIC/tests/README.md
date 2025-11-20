# NEXUS V5.0 - Tests

**Version:** 5.0 Pragmatic Edition
**Date:** 20 Novembre 2025

---

## 🧪 Test Suite

### Files

- **test_suite.py** - Comprehensive automated test suite (11 scenarios)
- **log_analyzer.py** - Log analysis tool for post-test inspection
- **run_tests.bat** - Windows batch script to run tests easily

---

## 🚀 Quick Start

### Run Tests

```powershell
# Critical tests only (recommended)
.\run_tests.bat critical

# Advanced tests
.\run_tests.bat advanced

# Stress tests
.\run_tests.bat stress

# All tests
.\run_tests.bat all
```

### Or directly with Python

```powershell
python test_suite.py --suite critical --workspace test_workspaces
```

---

## 📊 Analyze Results

After running tests:

```powershell
# Analyze specific test logs
python log_analyzer.py ..\test_workspaces\test_cfl_basic_write_read\logs

# View reports
notepad ..\test_workspaces\TEST_REPORT_CRITICAL_*.md
```

---

## 📂 Test Workspaces

Tests create dedicated workspaces in `test_workspaces/`:

```
test_workspaces/
├── test_cfl_basic_write_read/
│   ├── logs/
│   │   ├── nexus_session_*.log
│   │   ├── events_*.jsonl
│   │   ├── cfl_*.jsonl
│   │   ├── errors_*.log
│   │   └── trace_*.log
│   └── workspace/
└── TEST_REPORT_CRITICAL_*.md
```

---

## 🎯 Test Scenarios

### Critical (4 tests)
1. CFL_BASIC_WRITE_READ - CFL cycle validation
2. DUAL_SCHEMA_ENFORCEMENT - Dual Schema compliance
3. TOOL_EXECUTOR_ALL_TOOLS - All 6 tools validation
4. STRATEGIC_PLAN_TRACKING - Strategic planning

### Advanced (4 tests)
5. ERROR_RECOVERY - Error handling
6. MULTI_STEP_ANALYSIS - Complex analysis
7. AGENT_COLLABORATION - Gemini ↔ Claude
8. GIT_OPERATIONS - Git integration

### Stress (3 tests)
9. STRESS_RAPID_TOOL_SWITCHING - Rapid tool changes
10. STRESS_LARGE_FILE_OPERATIONS - Large files
11. STRESS_PLAN_COMPLEXITY - Complex plans (20+ steps)

---

For detailed information, see [Testing Guide](../docs/testing/TESTING_GUIDE.md).
