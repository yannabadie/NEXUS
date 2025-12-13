# Interaction Module - User Interaction Abstraction Layer

**Version**: V9.8 DETOX
**Author**: Claude (NEXUS DETOX)
**Date**: 2025-12-13

---

## Overview

The Interaction module provides a clean abstraction for user interaction, enabling NEXUS to run in both interactive CLI and headless server modes without code changes.

### Problem Solved

Before V9.8, NEXUS used raw `input()` calls throughout the codebase:

```python
# OLD: Blocks forever in headless mode, crashes web servers
confirm = input("Continue? (y/n): ")
```

This causes:
- **Server Hangs**: Web servers (FastAPI, Flask) block indefinitely waiting for stdin
- **CI/CD Failures**: Automated pipelines timeout on input prompts
- **Multi-tenant Issues**: One user's input() blocks all other requests

### Solution

The Interaction module provides async-first, provider-based user interaction:

```python
# NEW: Works everywhere - CLI, servers, CI/CD
provider = get_interaction_provider()
confirm = await provider.confirm("Continue?", default=True)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    InteractionProvider (ABC)                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  async ask(prompt, default, timeout, required) -> str   ││
│  │  async confirm(prompt, default, timeout) -> bool        ││
│  │  async choose(prompt, choices, default, timeout) -> str ││
│  │  async announce(message, level) -> None                 ││
│  │  async progress(message, current, total) -> None        ││
│  │  @property is_interactive -> bool                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      CLIProvider         │    │    HeadlessProvider      │
│  ┌────────────────────┐  │    │  ┌────────────────────┐  │
│  │ Uses run_in_executor│  │    │ │ Returns defaults   │  │
│  │ for non-blocking   │  │    │ │ immediately        │  │
│  │ input() calls      │  │    │ │                    │  │
│  │                    │  │    │ │ Logs all prompts   │  │
│  │ Rich UI support    │  │    │ │ for audit trail    │  │
│  └────────────────────┘  │    │  └────────────────────┘  │
│  is_interactive = True   │    │  is_interactive = False  │
└──────────────────────────┘    └──────────────────────────┘
```

---

## Module Structure

```
core/interaction/
├── __init__.py           # Factory functions + exports
├── base.py               # Abstract base class + types
├── cli_provider.py       # Interactive CLI provider
├── headless_provider.py  # Non-blocking headless provider
└── README.md             # This file
```

---

## Components

### 1. InteractionProvider (Abstract Base Class)

**File**: `base.py`

The abstract base class defining the interaction contract.

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from enum import Enum
from dataclasses import dataclass

class InteractionLevel(Enum):
    """Severity levels for announcements."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Choice:
    """A choice option for choose() method."""
    key: str           # Unique identifier (e.g., "a", "option1")
    label: str         # Display text (e.g., "Option A")
    description: str = ""  # Optional description

class InteractionRequiredError(Exception):
    """Raised when user input is required but unavailable."""
    def __init__(self, prompt: str, context: str = ""):
        self.prompt = prompt
        self.context = context
        super().__init__(f"User input required: {prompt}")

class InteractionProvider(ABC):
    """Abstract base class for user interaction."""

    @abstractmethod
    async def ask(
        self,
        prompt: str,
        default: Optional[str] = None,
        timeout: Optional[float] = None,
        required: bool = False
    ) -> str:
        """Ask user for text input."""
        pass

    @abstractmethod
    async def confirm(
        self,
        prompt: str,
        default: bool = False,
        timeout: Optional[float] = None
    ) -> bool:
        """Ask user for yes/no confirmation."""
        pass

    @abstractmethod
    async def choose(
        self,
        prompt: str,
        choices: List[Choice],
        default: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Present multiple choices to user."""
        pass

    @abstractmethod
    async def announce(
        self,
        message: str,
        level: InteractionLevel = InteractionLevel.INFO
    ) -> None:
        """Announce a message to user (no input required)."""
        pass

    @abstractmethod
    async def progress(
        self,
        message: str,
        current: int,
        total: int
    ) -> None:
        """Show progress indicator."""
        pass

    @property
    @abstractmethod
    def is_interactive(self) -> bool:
        """Whether this provider supports interactive input."""
        pass
```

### 2. CLIProvider

**File**: `cli_provider.py`

Interactive command-line provider using `run_in_executor` to prevent blocking.

**Key Features**:
- Uses `asyncio.run_in_executor()` to wrap blocking `input()` calls
- Supports timeout with default fallback
- Rich formatting for choices and progress
- Handles Ctrl+C and Ctrl+D gracefully

```python
class CLIProvider(InteractionProvider):
    """Interactive CLI provider using run_in_executor."""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix

    async def ask(self, prompt, default=None, timeout=None, required=False):
        loop = asyncio.get_event_loop()
        display = f"{self.prefix}{prompt}"
        if default:
            display += f" [{default}]"
        display += ": "

        try:
            if timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, input, display),
                    timeout=timeout
                )
            else:
                result = await loop.run_in_executor(None, input, display)
            return result.strip() or default or ""
        except asyncio.TimeoutError:
            return default or ""
        except EOFError:
            return default or ""

    @property
    def is_interactive(self) -> bool:
        return True
```

### 3. HeadlessProvider

**File**: `headless_provider.py`

Non-blocking provider for servers and automated environments.

**Key Features**:
- Never calls `input()` or any blocking I/O
- Returns default values immediately
- Logs all prompts and responses for audit trail
- Supports strict mode (raises on missing defaults)

```python
class HeadlessProvider(InteractionProvider):
    """Non-blocking provider for server/daemon mode."""

    def __init__(self, strict: bool = False, logger_name: Optional[str] = None):
        self.strict = strict
        self._logger = logging.getLogger(logger_name or "nexus.interaction.headless")

    async def ask(self, prompt, default=None, timeout=None, required=False):
        self._logger.info(f"[HEADLESS] Prompt: {prompt}")

        if default is not None:
            self._logger.info(f"[HEADLESS] Using default: {default}")
            return default

        if required or self.strict:
            raise InteractionRequiredError(
                prompt=prompt,
                context="Headless mode cannot provide user input"
            )

        return ""

    async def confirm(self, prompt, default=False, timeout=None):
        self._logger.info(f"[HEADLESS] Confirm: {prompt} -> {default}")
        return default

    @property
    def is_interactive(self) -> bool:
        return False
```

### 4. Factory Functions

**File**: `__init__.py`

Singleton factory with thread-safe initialization.

```python
import os
import threading
from typing import Optional

_provider: Optional[InteractionProvider] = None
_provider_lock = threading.Lock()

def get_interaction_provider() -> InteractionProvider:
    """
    Get the global interaction provider singleton.

    Provider type determined by NEXUS_INTERACTION_MODE env var:
    - "cli": Interactive CLIProvider (default)
    - "headless": Non-blocking HeadlessProvider
    - "strict": HeadlessProvider with strict=True
    """
    global _provider

    if _provider is None:
        with _provider_lock:
            if _provider is None:
                mode = os.environ.get("NEXUS_INTERACTION_MODE", "cli").lower()

                if mode == "headless":
                    _provider = HeadlessProvider(strict=False)
                elif mode == "strict":
                    _provider = HeadlessProvider(strict=True)
                else:
                    _provider = CLIProvider()

    return _provider

def set_interaction_provider(provider: InteractionProvider) -> None:
    """Override the global interaction provider."""
    global _provider
    with _provider_lock:
        _provider = provider

def reset_interaction_provider() -> None:
    """Reset the global provider to None."""
    global _provider
    with _provider_lock:
        _provider = None
```

---

## Configuration

### Environment Variable

```bash
# Interactive CLI mode (default)
export NEXUS_INTERACTION_MODE=cli

# Headless mode - returns defaults, never blocks
export NEXUS_INTERACTION_MODE=headless

# Strict headless mode - raises InteractionRequiredError if no default
export NEXUS_INTERACTION_MODE=strict
```

### Programmatic Override

```python
from core.interaction import set_interaction_provider, HeadlessProvider

# Force headless mode
set_interaction_provider(HeadlessProvider(strict=True))

# Custom provider
class MyProvider(InteractionProvider):
    # ... custom implementation
set_interaction_provider(MyProvider())
```

---

## Usage Examples

### Example 1: Simple Confirmation

```python
from core.interaction import get_interaction_provider

async def delete_file(path: str):
    provider = get_interaction_provider()

    if await provider.confirm(f"Delete {path}?", default=False):
        os.remove(path)
        await provider.announce(f"Deleted {path}")
    else:
        await provider.announce("Cancelled", level=InteractionLevel.WARNING)
```

### Example 2: Text Input with Default

```python
async def get_project_name():
    provider = get_interaction_provider()

    name = await provider.ask(
        "Enter project name",
        default="my-project",
        timeout=30.0  # 30 second timeout
    )

    return name
```

### Example 3: Multiple Choice

```python
from core.interaction import get_interaction_provider, Choice

async def select_model():
    provider = get_interaction_provider()

    choice = await provider.choose(
        "Select AI model",
        choices=[
            Choice("opus", "Claude Opus", "Best for complex reasoning"),
            Choice("sonnet", "Claude Sonnet", "Fast and efficient"),
            Choice("gemini", "Gemini Pro", "Google's flagship model"),
        ],
        default="sonnet"
    )

    return choice
```

### Example 4: Progress Indicator

```python
async def process_files(files: list):
    provider = get_interaction_provider()

    for i, file in enumerate(files):
        await provider.progress(f"Processing {file}", i, len(files))
        # ... process file

    await provider.progress("Complete", len(files), len(files))
```

### Example 5: Service with Dependency Injection

```python
from core.interaction import InteractionProvider, get_interaction_provider

class MyService:
    def __init__(self, interaction: Optional[InteractionProvider] = None):
        self._interaction = interaction

    def _get_provider(self) -> InteractionProvider:
        return self._interaction or get_interaction_provider()

    async def dangerous_operation(self):
        provider = self._get_provider()

        if not provider.is_interactive:
            # In headless mode, check for explicit confirmation flag
            raise RuntimeError("Dangerous operation requires interactive confirmation")

        if await provider.confirm("This is dangerous. Continue?", default=False):
            # ... do dangerous thing
            pass
```

### Example 6: Sync/Async Bridge

For sync code that needs to use the async provider:

```python
import asyncio
from core.interaction import get_interaction_provider

def sync_function():
    provider = get_interaction_provider()

    # Option 1: If event loop exists
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            provider.confirm("Continue?", default=True)
        )
    except RuntimeError:
        # Option 2: Create new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                provider.confirm("Continue?", default=True)
            )
        finally:
            loop.close()

    return result
```

---

## Integration Patterns

### Pattern 1: Service Layer Integration

Services that need user interaction should accept an optional `InteractionProvider`:

```python
class BudgetService:
    def __init__(
        self,
        workspace_path: Path,
        console: ConsoleV7,
        config: Optional[Config] = None,
        interaction: Optional[InteractionProvider] = None,  # V9.8 DETOX
    ):
        self.workspace_path = Path(workspace_path)
        self.console = console
        self.config = config
        self._interaction = interaction

    def _confirm_action(self, prompt: str, default: bool = False) -> bool:
        """
        Confirm action with user.

        V9.8 DETOX: Uses InteractionProvider for headless compatibility.
        """
        if self._interaction is not None:
            return asyncio.get_event_loop().run_until_complete(
                self._interaction.confirm(prompt, default=default)
            )
        else:
            from core.interaction import get_interaction_provider
            provider = get_interaction_provider()

            if provider.is_interactive:
                response = input(f"{prompt} (y/N): ").strip().lower()
                return response in ('y', 'yes')
            else:
                return asyncio.get_event_loop().run_until_complete(
                    provider.confirm(prompt, default=default)
                )
```

### Pattern 2: Breakpoint Handler Integration

For complex interaction flows (like HiveMind breakpoints):

```python
class UserInteractionHandler:
    def __init__(
        self,
        default_timeout: int = 60,
        enable_rich: bool = True,
        auto_accept: bool = False,
        interaction: Optional[InteractionProvider] = None  # V9.8 DETOX
    ):
        self._interaction = interaction
        # ...

    def request_breakpoint_sync(self, ...):
        # Check for headless mode first
        if self._interaction is not None and not self._interaction.is_interactive:
            return self._headless_breakpoint(request)

        # Otherwise use rich UI or basic input
        if self._use_rich:
            return self._rich_breakpoint(request)
        else:
            return self._basic_breakpoint(request)

    def _headless_breakpoint(self, request) -> BreakpointResponse:
        """Handle breakpoint in headless mode - return recommended option."""
        logger.info(f"[HEADLESS BREAKPOINT] Type: {request.breakpoint_type}")
        logger.info(f"[HEADLESS BREAKPOINT] Recommendation: {request.recommendation}")

        recommended = next(
            (opt for opt in request.options if opt.is_recommended),
            request.options[0] if request.options else None
        )

        return BreakpointResponse(
            breakpoint_type=request.breakpoint_type,
            chosen_option=recommended.id if recommended else "accept"
        )
```

### Pattern 3: FastAPI Integration

```python
import os
os.environ["NEXUS_INTERACTION_MODE"] = "headless"

from fastapi import FastAPI, HTTPException
from core.interaction import InteractionRequiredError
from core.bootstrap.service import BootstrapService

app = FastAPI()

@app.post("/bootstrap")
async def bootstrap_project(project_path: str):
    try:
        service = BootstrapService(console)
        result = service.bootstrap(Path(project_path))
        return {"status": "success", "data": result.data}
    except InteractionRequiredError as e:
        raise HTTPException(
            status_code=400,
            detail=f"User interaction required: {e.prompt}"
        )
```

---

## Testing

### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock
from core.interaction import (
    InteractionProvider,
    HeadlessProvider,
    InteractionRequiredError
)

class MockProvider(InteractionProvider):
    """Mock provider for testing."""

    def __init__(self):
        self.ask_responses = []
        self.confirm_responses = []

    async def ask(self, prompt, default=None, timeout=None, required=False):
        if self.ask_responses:
            return self.ask_responses.pop(0)
        return default or ""

    async def confirm(self, prompt, default=False, timeout=None):
        if self.confirm_responses:
            return self.confirm_responses.pop(0)
        return default

    # ... other methods

    @property
    def is_interactive(self):
        return False

@pytest.mark.asyncio
async def test_headless_returns_default():
    provider = HeadlessProvider(strict=False)
    result = await provider.confirm("Delete?", default=True)
    assert result is True

@pytest.mark.asyncio
async def test_strict_raises_on_missing_default():
    provider = HeadlessProvider(strict=True)
    with pytest.raises(InteractionRequiredError):
        await provider.ask("Enter name", required=True)

def test_service_with_mock_provider():
    mock = MockProvider()
    mock.confirm_responses = [True]

    service = MyService(interaction=mock)
    # ... test service behavior
```

---

## Migration Guide

### Before V9.8 (Old Pattern)

```python
# Direct input() call - blocks in headless mode
def reset_budget(self):
    confirm = input("Reset budget? (y/n): ").strip().lower()
    if confirm == 'y':
        self._do_reset()
```

### After V9.8 (New Pattern)

```python
from typing import Optional
from core.interaction import InteractionProvider

class BudgetService:
    def __init__(self, ..., interaction: Optional[InteractionProvider] = None):
        self._interaction = interaction

    def reset_budget(self):
        if self._confirm_reset():
            self._do_reset()

    def _confirm_reset(self) -> bool:
        """V9.8 DETOX: Uses InteractionProvider for headless compatibility."""
        if self._interaction is not None:
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                self._interaction.confirm("Reset budget?", default=False)
            )
        else:
            from core.interaction import get_interaction_provider
            provider = get_interaction_provider()

            if provider.is_interactive:
                response = input("Reset budget? (y/n): ").strip().lower()
                return response in ('y', 'yes')
            else:
                import asyncio
                return asyncio.get_event_loop().run_until_complete(
                    provider.confirm("Reset budget?", default=False)
                )
```

### Migration Checklist

1. [ ] Add `interaction: Optional[InteractionProvider] = None` to `__init__`
2. [ ] Store as `self._interaction = interaction`
3. [ ] Create private helper method (e.g., `_confirm_action()`)
4. [ ] Replace direct `input()` calls with helper method
5. [ ] Add `from core.interaction import InteractionProvider` to TYPE_CHECKING
6. [ ] Test with `NEXUS_INTERACTION_MODE=headless`

---

## Troubleshooting

### Issue: "RuntimeError: no running event loop"

**Cause**: Calling async provider methods from sync code without event loop.

**Solution**:
```python
import asyncio

def sync_method(self):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(
        provider.confirm("Continue?", default=True)
    )
```

### Issue: InteractionRequiredError in production

**Cause**: Strict mode enabled but no default provided.

**Solution**: Either provide defaults or use non-strict headless mode:
```bash
export NEXUS_INTERACTION_MODE=headless  # Not "strict"
```

### Issue: Input not working in Docker

**Cause**: No TTY attached to container.

**Solution**: Use headless mode for containerized deployments:
```dockerfile
ENV NEXUS_INTERACTION_MODE=headless
```

---

## See Also

- [DETOX_V9.8_STATUS.md](../../docs/DETOX_V9.8_STATUS.md) - Full DETOX operation status
- [core/bootstrap/service.py](../bootstrap/service.py) - Example integration
- [core/telemetry/service.py](../telemetry/service.py) - Example integration
- [core/hive_mind/user_interaction.py](../hive_mind/user_interaction.py) - Breakpoint integration
