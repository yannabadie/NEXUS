"""
ARCHIVED: PTY Mode for Gemini Driver V7 (Sprint 13)

REASON: PTY mode was DEPRECATED because Gemini's TUI doesn't accept PTY stdin input.
        The --prompt-interactive flag only works for initial prompt.
        For multi-turn: use subprocess mode with --resume latest.

ARCHIVED FROM: core/drivers/gemini_driver_v7.py
ARCHIVED DATE: 2025-12-04
ARCHIVED BY: NEXUS INTEGRITY SENTINEL

This code is preserved for historical reference only. DO NOT IMPORT.
"""

# === ORIGINAL CONSTANTS (gemini_driver_v7.py lines 43-46) ===

# PTY mode removed in V7 cleanup (was never used, gemini_pty_mode=False by default)
# Session persistence now uses --resume latest instead
PTY_AVAILABLE = False
PersistentGeminiPTY = None


# === ORIGINAL INIT PARAMETERS (gemini_driver_v7.py lines 94, 117-122) ===
"""
def __init__(..., pty_mode: Optional[bool] = None):
    # V7 Sprint 13: PTY PERSISTENT mode
    # Uses winpty to maintain a persistent Gemini session (~2s latency vs ~15s subprocess)
    # The PTY is kept alive between invocations for maximum performance
    self.pty_mode = pty_mode if pty_mode is not None else getattr(config, 'gemini_pty_mode', False)
    self.pty_available = PTY_AVAILABLE
    self._pty_instance: Optional[Any] = None  # Persistent PTY instance
"""


# === ORIGINAL PTY METHODS (gemini_driver_v7.py lines 183-265) ===

def _ensure_pty_started(self) -> bool:
    """
    Ensure the persistent PTY is started and alive.

    Returns:
        True if PTY is ready for use
    """
    # Check if PTY is already running
    if self._pty_instance and self._pty_instance.is_alive():
        return True

    # Calculate nexus_root for include_directories
    resolved_workspace = self.workspace_path.resolve()
    parent_dir = resolved_workspace.parent
    grandparent = parent_dir.parent
    if grandparent.name == "GENERATION_ACTIVE":
        nexus_root = grandparent.parent
    else:
        nexus_root = grandparent

    # Create new PTY instance
    print(f"[DEBUG] Starting persistent PTY for Gemini: {self.model}", file=sys.stderr)
    self._pty_instance = PersistentGeminiPTY(
        config=self.config,
        workspace_path=self.workspace_path,
        model=self.model,
        include_directories=[nexus_root]
    )

    # Start with a simple prompt that generates a direct response (not tool use)
    initial = "Say OK"
    if not self._pty_instance.start(initial_prompt=initial):
        print(f"[ERROR] Failed to start PTY process", file=sys.stderr)
        self._pty_instance = None
        return False

    print(f"[DEBUG] Persistent PTY started (PID: {self._pty_instance.process.pid})", file=sys.stderr)
    return True


def _close_pty(self):
    """Close the persistent PTY if running."""
    if self._pty_instance:
        try:
            self._pty_instance.close()
        except Exception:
            pass
        self._pty_instance = None


def _invoke_pty_persistent(self, context: str) -> dict:
    """
    Invoke Gemini using persistent PTY mode.

    Maintains a single PTY session across multiple invocations.
    ~2s latency vs ~15-20s for subprocess mode.

    Args:
        context: Context markdown

    Returns:
        Dict structured NEXUS response
    """
    import time

    # Ensure PTY is started
    if not self._ensure_pty_started():
        raise RuntimeError("Failed to start persistent PTY")

    start_time = time.time()
    print(f"[DEBUG] Invoking Gemini (PTY persistent): {self.model}", file=sys.stderr)

    try:
        # Send prompt via PTY and wait for response
        raw_response = self._pty_instance.send_prompt(context, timeout=self.timeout)

        elapsed = time.time() - start_time
        print(f"[DEBUG] PTY response received in {elapsed:.1f}s", file=sys.stderr)

        # Extract JSON from response
        return self._extract_json(raw_response)

    except Exception as e:
        # PTY might have died, close it for next retry
        print(f"[WARNING] PTY invocation failed: {e}", file=sys.stderr)
        self._close_pty()
        raise


# === ORIGINAL INVOKE() PTY LOGIC (gemini_driver_v7.py lines 161-171) ===
"""
def invoke(self, context: str, use_pty: Optional[bool] = None, session_uuid: Optional[str] = None) -> Dict:
    # Determine if we should try PTY mode
    try_pty = use_pty if use_pty is not None else self.pty_mode

    # V7 Sprint 13: Try PTY PERSISTENT mode if enabled and available
    if try_pty and self.pty_available:
        try:
            return self._invoke_pty_persistent(context)
        except Exception as e:
            print(f"[WARNING] PTY mode failed: {e}, falling back to subprocess", file=sys.stderr)
            # Kill failed PTY and fall through to subprocess
            self._close_pty()

    # ... rest of method continues with subprocess mode
"""


# === ORIGINAL CONFIG SETTINGS (core/config.py lines 199-214) ===
"""
# ====================================================================
# GEMINI PTY MODE (V7 Sprint 13) - DISABLED
# ====================================================================
# PTY mode is DISABLED because Gemini's TUI doesn't accept input via PTY stdin.
# The --prompt-interactive flag works for initial prompt only.
# For multi-turn conversations, use subprocess mode with --resume latest instead.
#
# - False (DEFAULT): Use subprocess mode with --resume latest (~5s latency)
# - True: Attempt PTY mode (experimental, single-turn only)
self.gemini_pty_mode: bool = os.getenv("GEMINI_PTY_MODE", "False").lower() == "true"

# PTY timeouts (seconds)
self.gemini_pty_startup_timeout: float = float(os.getenv("GEMINI_PTY_STARTUP_TIMEOUT", "60"))
self.gemini_pty_timeout: float = float(os.getenv("GEMINI_PTY_TIMEOUT", "300"))
self.gemini_pty_idle_timeout: float = float(os.getenv("GEMINI_PTY_IDLE_TIMEOUT", "5"))
self.gemini_pty_max_restarts: int = int(os.getenv("GEMINI_PTY_MAX_RESTARTS", "3"))
"""
