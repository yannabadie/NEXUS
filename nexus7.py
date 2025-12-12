#!/usr/bin/env python3
"""
NEXUS - The Omniscient REPL
Persistent FSM Orchestrator with Hybrid Drivers
(Version loaded from .env: NEXUS_VERSION, NEXUS_CODENAME)

Architecture:
- FSM (Finite State Machine) for persistent state management
- Claude Hybrid Driver (natural language + XML tool blocks)
- Gemini JSON Driver (strict JSON mode)
- Adaptive stagnation detection
- Bootstrap verification at startup
"""
import sys
import signal
import argparse
import asyncio
import atexit
from pathlib import Path
import importlib.util
from typing import Dict, Optional

# Fix Windows ANSI colors - V9.1.1: Simplified approach
# Let Rich handle ANSI auto-detection. Only enable VT100 mode via Windows API.
# DO NOT use colorama - it conflicts with Rich's output handling.
if sys.platform == 'win32':
    import ctypes
    try:
        # Enable VT100 mode (ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004)
        # This allows Windows 10+ terminals to interpret ANSI codes natively
        kernel32 = ctypes.windll.kernel32
        stdout_handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        stderr_handle = kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(stdout_handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(stdout_handle, mode.value | 0x0004)
        if kernel32.GetConsoleMode(stderr_handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(stderr_handle, mode.value | 0x0004)
    except Exception:
        pass  # Non-critical: Rich will fallback gracefully

# Load version from .env (single source of truth)
import os
import logging
from dotenv import load_dotenv
load_dotenv()
NEXUS_VERSION = os.getenv("NEXUS_VERSION", "8.4.0")
NEXUS_CODENAME = os.getenv("NEXUS_CODENAME", "TRUE HIVE MIND")

# Configure logging EARLY - FORCE override any existing config
# Default to WARNING to hide INFO messages in production
_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
_log_level_int = getattr(logging, _log_level, logging.WARNING)
# Force reconfigure by clearing root logger handlers
logging.root.handlers.clear()
logging.basicConfig(
    level=_log_level_int,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True  # Python 3.8+ - forces reconfiguration
)

# Constantes
ENV_TEMPLATE = f"""# NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} Configuration
GEMINI_CLI_PATH=gemini
CLAUDE_CLI_PATH=claude
MAX_STALEMATE_COUNT=5
STAGNATION_SIMILARITY_THRESHOLD=0.8
WORKSPACE_PATH=./workspace
LOG_LEVEL=WARNING
UI_VERBOSE=False
"""

# =============================================================================
# V8.4.5: Graceful Shutdown Handlers
# =============================================================================

_shutdown_requested = False
_async_factory = None


def _cleanup_processes():
    """
    Cleanup function called at exit.

    V8.4.5: Ensures all subprocess and async processes are terminated.
    """
    global _async_factory

    # Cleanup driver processes (Gemini and Claude)
    try:
        from core.drivers.gemini_driver_v7 import _cleanup_processes as cleanup_gemini
        cleanup_gemini()
    except Exception:
        pass

    try:
        from core.drivers.claude_driver_hybrid import _cleanup_claude_processes
        _cleanup_claude_processes()
    except Exception:
        pass

    # Cleanup async factory if available
    if _async_factory:
        try:
            # Run cleanup in a new event loop since atexit runs outside async context
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_async_factory.cancel_all())
            loop.close()
        except Exception:
            pass


def _signal_handler(signum, frame):
    """
    Signal handler for graceful shutdown.

    V8.4.5: Handles SIGINT and SIGTERM for graceful termination.
    """
    global _shutdown_requested

    if _shutdown_requested:
        # Second signal - force exit
        print("\n[SHUTDOWN] Force exit requested", file=sys.stderr)
        sys.exit(1)

    _shutdown_requested = True
    sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
    print(f"\n[SHUTDOWN] Received {sig_name}, cleaning up...", file=sys.stderr)

    # Cleanup will happen via atexit or explicit call
    raise KeyboardInterrupt


def setup_signal_handlers():
    """
    Setup signal handlers for graceful shutdown.

    V8.4.5: Cross-platform signal handling.
    - Windows: SIGINT only (SIGTERM not supported)
    - Unix: SIGINT and SIGTERM
    """
    # Register atexit handler first (always works)
    atexit.register(_cleanup_processes)

    # SIGINT (Ctrl+C) - works on all platforms
    signal.signal(signal.SIGINT, _signal_handler)

    # SIGTERM - Unix only
    if sys.platform != 'win32':
        signal.signal(signal.SIGTERM, _signal_handler)


def bootstrap():
    """
    Bootstrap NEXUS V7 - Vérifie tout avant de démarrer

    Vérifie:
    0. KERNEL.py integrity (immutability verification)
    1. Python version (3.11+)
    2. Dependencies installées
    3. Structure workspace créée
    4. .env configuré
    5. CLIs (gemini, claude) disponibles

    Returns:
        Tuple[Dict, Dict]: (gemini_info, claude_info)

    Raises:
        SystemExit: Si bootstrap échoue
    """
    print(f"🚀 NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} Bootstrap...")

    # 0. VERIFY KERNEL.PY INTEGRITY (CRITICAL SECURITY CHECK)
    # KERNEL.py location:
    # - For children: same directory (copied by clone_and_mutate.py)
    # - For parent NEXUS_V7_CHRYSALIS: at 20_NEXUS/KERNEL.py (parent.parent)
    nexus_dir = Path(__file__).parent
    kernel_locations = [
        nexus_dir,                    # Children: KERNEL.py in same dir
        nexus_dir.parent,             # Fallback: parent dir
        nexus_dir.parent.parent,      # Parent NEXUS: 20_NEXUS/
    ]

    kernel_found = False
    for loc in kernel_locations:
        if (loc / "KERNEL.py").exists():
            sys.path.insert(0, str(loc))
            kernel_found = True
            break

    if not kernel_found:
        print("❌ FATAL: KERNEL.py not found in any expected location!")
        print(f"   Searched: {[str(l) for l in kernel_locations]}")
        sys.exit(1)

    from KERNEL import verify_kernel_integrity

    print("\n🔒 Verifying KERNEL.py integrity...")
    if not verify_kernel_integrity():
        print("\n" + "="*60)
        print("❌ SECURITY VIOLATION: KERNEL.py has been modified!")
        print("="*60)
        print("\nNEXUS cannot start with compromised KERNEL.")
        print("This file contains immutable invariants and must never change.")
        print("\nIf this is intentional, delete KERNEL_HASH.txt and restart.")
        print("="*60)
        sys.exit(1)

    print("✓ KERNEL.py integrity verified")

    # 1. Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        print(f"   Current: Python {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)

    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # 2. Check dependencies
    required_packages = [
        'prompt_toolkit',
        'rich',
        'pydantic',
        'python-dotenv',
        'tiktoken'
    ]

    missing = []
    for pkg in required_packages:
        # Handle special case for python-dotenv
        check_name = 'dotenv' if pkg == 'python-dotenv' else pkg
        if not importlib.util.find_spec(check_name):
            missing.append(pkg)

    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print(f"\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)

    print(f"✓ Dependencies installed ({len(required_packages)} packages)")

    # 3. Create workspace structure
    workspace = Path("workspace")
    directories = [
        workspace / "_IO_BUFFER",
        workspace / ".nexus",
        workspace / "logs",
        workspace / "sessions"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    print(f"✓ Workspace structure ({len(directories)} directories)")

    # 4. Check .env
    env_path = Path(".env")
    if not env_path.exists():
        print("\n⚠️  No .env file found. Creating template...")
        env_path.write_text(ENV_TEMPLATE)
        print("✓ Created .env - Please configure your CLI paths if needed")
    else:
        print("✓ .env file found")

    # 5. Test CLIs with Inspector
    print("\n🔍 Testing CLI tools...")

    # Import CLI Inspector
    sys.path.insert(0, str(Path(__file__).parent))
    from core.meta.cli_inspector import CLIInspector

    inspector = CLIInspector()
    gemini_info = inspector.inspect_gemini()
    claude_info = inspector.inspect_claude()

    # Check Gemini
    if not gemini_info["available"]:
        print("\n❌ Gemini CLI not available")
        print("   Install: https://ai.google.dev/gemini-api/docs/cli")
        if "error" in gemini_info:
            print(f"   Error: {gemini_info['error']}")
        sys.exit(1)

    # Check Claude
    if not claude_info["available"]:
        print("\n❌ Claude CLI not available")
        print("   Install: https://docs.anthropic.com/en/docs/claude-cli")
        if "error" in claude_info:
            print(f"   Error: {claude_info['error']}")
        sys.exit(1)

    # Success!
    print("\n" + "="*60)
    print(f"✅ NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} Bootstrap Complete")
    print("="*60)
    print(f"\n📊 Gemini")
    print(f"   Model: {gemini_info['model']}")
    print(f"   Context: {gemini_info['context_window']:,} tokens")
    print(f"   Version: {gemini_info.get('version', 'Unknown')}")

    print(f"\n🧠 Claude (Dynamic Routing)")
    print(f"   Default: {claude_info['model']}")
    print(f"   Opus 4.5: brainstorm, evolution, redteam, architect")
    print(f"   Sonnet 4.5: tool, validation, simple tasks")
    print(f"   Context: {claude_info['context_window']:,} tokens")
    print(f"   Version: {claude_info.get('version', 'Unknown')}")

    print("\n" + "="*60)

    # V9.1.1: Windows Terminal recommendation for best experience
    if sys.platform == 'win32':
        # Check if running in Windows Terminal (has WT_SESSION env var)
        if not os.environ.get('WT_SESSION'):
            print("\n💡 Tip: For best colors/Unicode, use Windows Terminal:")
            print("   https://aka.ms/terminal")

    print()

    return gemini_info, claude_info


# =============================================================================
# V9 CYBORG: Async Entry Point
# =============================================================================

async def async_main(
    workspace_path: Path,
    gemini_info: Dict,
    claude_info: Dict,
    pending_metadata: Optional[Dict],
    config
):
    """
    V9 Cyborg Async Entry Point.

    Wraps the V7 REPL in an async context, enabling:
    - Non-blocking user input (prompt_async)
    - Async LLM streaming
    - Graceful Ctrl+C cancellation

    Falls back to sync REPL if run_async() not available.
    """
    global _async_factory

    from core.interface.repl import InteractiveNexusV7

    # Initialize async driver factory for process management
    try:
        from core.drivers.async_factory import AsyncDriverFactory
        # Create factory instance (will be accessible via get_driver_factory)
        factory = AsyncDriverFactory(config, workspace_path)
        # Store in module for global access
        import core.drivers.async_factory as factory_module
        factory_module._global_factory = factory
        # V8.4.5: Store reference for graceful shutdown
        _async_factory = factory
    except ImportError:
        # Async drivers not available, continue with sync
        pass

    # Display pending review alerts (sync, fast)
    if pending_metadata:
        from core.notifications.repl_alert import get_repl_alert_message, should_block_evolution
        print(get_repl_alert_message(pending_metadata, config))
        if should_block_evolution(pending_metadata, config):
            print("\n⚠️  WARNING: Evolution is BLOCKED until review is completed.")
            print("   Use /review command to evaluate children.\n")

    repl = InteractiveNexusV7(
        workspace_path=workspace_path,
        gemini_info=gemini_info,
        claude_info=claude_info
    )

    # V9 Cyborg: Prefer async, fallback to sync
    if hasattr(repl, 'run_async'):
        await repl.run_async()
    else:
        # Sync fallback (V7 mode)
        repl.run()


def main():
    """Entry point for NEXUS interactive REPL."""
    # V8.4.5: Setup graceful shutdown handlers early
    setup_signal_handlers()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description=f"NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} - The Omniscient REPL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nexus6                    Launch interactive REPL
  nexus6 --verify           Verify installation (bootstrap only)
  nexus6 --version          Show version
  nexus6 --workspace ./myproject  Use custom workspace

Documentation: https://github.com/nexus-ai/nexus-v7
        """
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Run bootstrap verification only (no REPL)'
    )

    parser.add_argument(
        '--version',
        action='store_true',
        help='Show NEXUS version'
    )

    parser.add_argument(
        '--workspace',
        type=str,
        default='./workspace',
        help='Workspace directory path (default: ./workspace)'
    )

    args = parser.parse_args()

    # Handle --version
    if args.version:
        print(f"NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} - The Omniscient REPL")
        print("Persistent FSM Orchestrator with Hybrid Drivers")
        print("https://github.com/yannabadie/NEXUS")
        sys.exit(0)

    try:
        # Bootstrap system
        gemini_info, claude_info = bootstrap()

        # Handle --verify (exit after bootstrap)
        if args.verify:
            print("\n✅ Bootstrap verification successful!")
            print(f"   NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} is ready to use.")
            sys.exit(0)

        # Import config and check pending reviews
        from core.notifications import check_pending_review
        from core.config import load_config

        workspace_path = Path(args.workspace).resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)

        # CHECK FOR PENDING REVIEW (Evolution notification system)
        config = load_config()
        pending_metadata = check_pending_review(workspace_path)

        # V9 CYBORG: Launch via asyncio.run()
        asyncio.run(async_main(
            workspace_path=workspace_path,
            gemini_info=gemini_info,
            claude_info=claude_info,
            pending_metadata=pending_metadata,
            config=config
        ))

    except KeyboardInterrupt:
        print(f"\n\n👋 NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} terminated by user")
        # V8.4.5: Cleanup handled by atexit and signal handlers
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
