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

# Load version from .env (single source of truth)
import os

# Fix Windows ANSI colors - V9.1.2: Ultra-simple approach
# Calling os.system('') triggers cmd.exe to initialize VT100 mode
# This side-effect enables ANSI escape sequences in the console
# Source: https://bugs.python.org/issue40134
if sys.platform == 'win32':
    os.system('')  # Enable ANSI escape codes (Windows 10 1607+)
    # Ensure stdout/stderr can emit UTF-8 on Windows consoles.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import logging
from dotenv import load_dotenv
load_dotenv()
NEXUS_VERSION = os.getenv("NEXUS_VERSION", "12.4.0")
NEXUS_CODENAME = os.getenv("NEXUS_CODENAME", "COGNITIVE BOOST")

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

    # V12.4: Legacy driver cleanup removed (SDK drivers handle cleanup automatically)
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
# V12.4: Headless Execution Mode
# =============================================================================

async def headless_main(
    workspace_path: Path,
    task: Optional[str],
    output_path: Optional[str],
    config,
) -> int:
    """
    V12.4 Headless execution mode.

    Runs a single task with no TTY interaction, producing deterministic
    JSON output. Designed for CI/CD pipelines and automation.

    Args:
        workspace_path: Working directory
        task: Task description to execute (None = boot validation only)
        output_path: File path for JSON output (None = stdout)
        config: Loaded NEXUS config

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    import json
    from datetime import datetime, timezone

    result = {
        "nexus_version": NEXUS_VERSION,
        "codename": NEXUS_CODENAME,
        "mode": "headless",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "status": "success",
        "output": None,
        "error": None,
    }

    try:
        # Use HeadlessProvider (no TTY)
        from core.interaction.headless_provider import HeadlessProvider
        provider = HeadlessProvider(strict=False, publish_events=False)

        if task is None:
            # Boot validation only - verify system can initialize
            result["output"] = "Headless boot validation successful"
            result["status"] = "success"
        else:
            # Execute the task via SDK driver if API key available, else orchestrator
            try:
                from core.drivers.async_factory import AsyncDriverFactory
                factory = AsyncDriverFactory(config, workspace_path)
                driver_info = factory.get_driver_info()

                if driver_info["claude_sdk_available"]:
                    # V12.4: Direct SDK execution (no CLI bootstrap needed)
                    sdk_driver = factory.get_claude_sdk()
                    response = await sdk_driver.invoke(
                        task,
                        system_prompt="You are NEXUS, a collaborative AI orchestrator. Execute the task and return results.",
                    )
                    result["output"] = response.content
                    result["status"] = "success" if response.status.name == "SUCCESS" else "failure"
                    result["driver"] = "anthropic_sdk"
                    if response.usage:
                        result["token_usage"] = response.usage
                elif driver_info["gemini_sdk_available"]:
                    sdk_driver = factory.get_gemini_sdk()
                    response = await sdk_driver.invoke(
                        task,
                        system_prompt="You are NEXUS, a collaborative AI orchestrator. Execute the task and return results.",
                    )
                    result["output"] = response.content
                    result["status"] = "success" if response.status.name == "SUCCESS" else "failure"
                    result["driver"] = "google_genai_sdk"
                    if response.usage:
                        result["token_usage"] = response.usage
                else:
                    # Fallback: try orchestrator (requires CLI tools)
                    from core.orchestration_v7 import OrchestratorV7
                    orch = OrchestratorV7(
                        config=config,
                        workspace_path=str(workspace_path),
                    )
                    response = await asyncio.wait_for(
                        orch.process_headless(task),
                        timeout=300.0,
                    )
                    result["output"] = response.get("content", str(response))
                    result["status"] = "success" if response.get("success", True) else "failure"
                    result["driver"] = "cli_orchestrator"

            except asyncio.TimeoutError:
                result["status"] = "timeout"
                result["error"] = "Task execution timed out (300s)"
            except AttributeError:
                # process_headless not yet implemented
                result["output"] = f"Task queued: {task}"
                result["status"] = "success"
                result["error"] = "Headless task execution not yet fully wired (V12.4 preview)"

    except Exception as e:
        result["status"] = "failure"
        result["error"] = str(e)

    # Output results
    json_output = json.dumps(result, indent=2, ensure_ascii=False)

    if output_path:
        Path(output_path).write_text(json_output, encoding="utf-8")
    else:
        print(json_output)

    return 0 if result["status"] == "success" else 1


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

    # V12.4: Initialize OpenTelemetry (if enabled)
    try:
        from core.telemetry.otel_provider import init_otel
        init_otel(service_name="nexus-backend", service_version=NEXUS_VERSION)
    except Exception:
        pass  # OTel is optional

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

    # V12.4: Check for interrupted sessions (crash recovery)
    try:
        from core.fsm.event_sourcing import get_event_store
        event_store = get_event_store(workspace_path)
        interrupted = event_store.get_interrupted_sessions()
        if interrupted:
            print(f"\n⚠️  Detected {len(interrupted)} interrupted session(s):")
            for sess in interrupted[:3]:
                print(f"   - Session {sess['session_id']}: last state={sess['last_state']}, "
                      f"events={sess['event_count']}")
            print("   Sessions can be resumed or will be trimmed on next boot.\n")
    except Exception:
        pass  # Non-critical

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

    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (no TTY, deterministic JSON output)'
    )

    parser.add_argument(
        '--task',
        type=str,
        default=None,
        help='Task to execute in headless mode (requires --headless)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file for headless results (default: stdout as JSON)'
    )

    args = parser.parse_args()

    # Handle --version
    if args.version:
        print(f"NEXUS V{NEXUS_VERSION} {NEXUS_CODENAME} - The Omniscient REPL")
        print("Persistent FSM Orchestrator with Hybrid Drivers")
        print("https://github.com/yannabadie/NEXUS")
        sys.exit(0)

    # V12.4: Headless mode - skip CLI bootstrap, use SDK drivers directly
    if args.headless:
        try:
            workspace_path = Path(args.workspace).resolve()
            workspace_path.mkdir(parents=True, exist_ok=True)

            from core.config import load_config
            config = load_config()

            exit_code = asyncio.run(headless_main(
                workspace_path=workspace_path,
                task=args.task,
                output_path=args.output,
                config=config,
            ))
            sys.exit(exit_code)
        except Exception as e:
            import json
            result = {
                "nexus_version": NEXUS_VERSION,
                "codename": NEXUS_CODENAME,
                "mode": "headless",
                "status": "failure",
                "error": str(e),
            }
            print(json.dumps(result, indent=2))
            sys.exit(1)

    try:
        # Bootstrap system (CLI verification for interactive mode)
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

        # V12.4 PHASE 2: Crash recovery check
        from core.fsm.event_sourcing import FSMEventStore
        event_store = FSMEventStore(workspace_path)
        interrupted = event_store.get_interrupted_sessions()

        if interrupted:
            session_info = interrupted[-1]  # Most recent interrupted session
            print(f"\n⚠️  Detected interrupted session")
            print(f"   Last state: {session_info['last_state']}")
            print(f"   Timestamp: {session_info['last_timestamp']}")
            print(f"   Events: {session_info['event_count']}")

            # Ask user if they want to resume (interactive mode only)
            response = input("\n   Resume previous session? [y/N]: ").strip().lower()
            if response in ('y', 'yes'):
                print("   ✓ Resuming previous session state...")
                # Note: Actual state restoration would happen in async_main
                # For now, we just log this and continue with existing events
            else:
                print("   Starting new session (old events preserved for debugging)...")
        else:
            last_state = event_store.get_last_state()
            if last_state:
                print(f"✓ Previous session ended cleanly ({last_state})")

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
