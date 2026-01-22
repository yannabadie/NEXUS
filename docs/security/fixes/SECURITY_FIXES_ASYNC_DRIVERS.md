# Security Fixes Summary - Async Drivers

## Overview
Fixed 4 security vulnerabilities in `core/drivers/async_claude_driver.py` and applied consistent security fixes to `core/drivers/async_gemini_driver.py` using the existing NEXUS security infrastructure (PathGuardian).

## Security Issues Fixed in AsyncClaudeDriver

### 1. Session UUID Path Traversal (CWE-22)
**Location**: `invoke_stream()` method, context file creation
**Risk**: Attackers could use path traversal patterns in session_uuid to write files outside the workspace
**Fix**: 
- Added `_is_safe_session_uuid()` validation method
- Validates session UUID format and blocks path traversal patterns
- Uses PathGuardian for additional path validation before file operations

### 2. Command Injection via cli_path (CWE-77)
**Location**: `__init__()` and subprocess execution
**Risk**: Malicious cli_path config could allow command injection (e.g., `claude; rm -rf /`)
**Fix**:
- Added `_is_safe_cli_path()` validation in `__init__()`
- Blocks shell metacharacters and command chaining
- Validates absolute paths are within approved system directories

### 3. Parameter Injection via model names (CWE-77)
**Location**: `invoke_stream()` method, command construction
**Risk**: Malicious model names could inject additional CLI parameters
**Fix**:
- Added `_is_safe_model_name()` and `_sanitize_model_param()` methods
- Validates model names contain only safe characters (alphanumeric, hyphens, underscores, dots)
- Blocks shell metacharacters and path traversal patterns

### 4. Workspace Path Traversal (CWE-22)
**Location**: `invoke_stream()` method, subprocess cwd parameter
**Risk**: Malicious workspace_path could escape intended directory boundaries
**Fix**:
- Added `_is_safe_workspace_path()` validation
- Blocks shell metacharacters and dangerous path patterns
- Validates path before passing to subprocess execution

## Security Issues Fixed in AsyncGeminiDriver

### Applied Consistent Security Model
**Changes Made**:
1. **PathGuardian Integration**: Added PathGuardian instance for consistent path validation
2. **CLI Path Validation**: Updated `_validate_cli_path()` to handle Windows extensions (.cmd, .exe, .bat, etc.)
3. **Session UUID Sanitization**: Existing `_sanitize_unique_id()` method integrated with PathGuardian
4. **Context Sanitization**: Existing `_sanitize_context()` method maintained for content validation

## Implementation Details

### New Security Methods in AsyncClaudeDriver

```python
def _validate_config(self) -> None:
    """Validate critical config values during initialization"""

def _is_safe_cli_path(self, path: str) -> bool:
    """Check if cli_path is safe from command injection"""

def _is_safe_model_name(self, model: str) -> bool:
    """Check if model name is safe from parameter injection"""

def _is_safe_session_uuid(self, session_uuid: str) -> bool:
    """Validate session UUID format to prevent path traversal"""

def _is_safe_workspace_path(self, workspace_path: str) -> bool:
    """Check if workspace path is safe for subprocess execution"""

def _sanitize_model_param(self, model: str) -> str:
    """Sanitize model parameter before using in command"""
```

### Updated Security in AsyncGeminiDriver

```python
def _validate_cli_path(self, cli_path: str) -> bool:
    """Enhanced to handle Windows file extensions"""

def _sanitize_unique_id(self, unique_id: str) -> str:
    """Prevent path traversal in session IDs"""

def _sanitize_context(self, context: str) -> str:
    """Sanitize context content"""
```

## Dependencies

### Added Imports
- `core.security.path_guardian import PathGuardian`

### Security Infrastructure Used
- PathGuardian for filesystem path validation
- Pattern matching for input validation
- Whitelist-based command validation

## Testing

### Verification Results
All security tests pass:
- ✅ Path traversal attacks blocked (Unix: `../../etc/passwd`, Windows: `..\..\Windows\System32`)
- ✅ Command injection attempts blocked (`;`, `|`, `&` metacharacters)
- ✅ Valid CLI paths accepted (`claude`, `gemini`, `/usr/bin/claude`)
- ✅ Valid model names accepted (`claude-sonnet-4-5-20250929`)
- ✅ Valid session UUIDs accepted (`safe-uuid-123`, UUID format)
- ✅ All existing async driver tests still pass (19/19)

### Test Execution
```bash
python verify_async_claude_security.py  # All security tests pass
python -m pytest tests/test_async_drivers.py -v  # 19/19 tests pass
```

## Impact

- ✅ **Security**: All path traversal and injection vulnerabilities mitigated
- ✅ **Compatibility**: No breaking changes to existing functionality
- ✅ **Cross-Platform**: Properly handles Windows and Unix path conventions
- ✅ **Consistency**: Applied same security model to both async drivers
- ✅ **Maintainability**: Uses existing, well-tested security infrastructure

## Compliance

- Addresses CWE-22 (Path Traversal)
- Addresses CWE-77 (Command Injection)
- Uses NEXUS security standards (PathGuardian)
- Follows existing code patterns and conventions
- Compatible with both Windows and Unix systems
