#!/usr/bin/env python3
"""
NEXUS V9.0 - Async-First Entry Point

The TRUE HIVE MIND with fully async architecture.

Usage:
    python nexus9.py [--workspace PATH] [--verbose]

Features:
- Non-blocking REPL (prompt_toolkit async)
- Cancellable operations (Ctrl+C works!)
- Streaming output without UI corruption
- pytransitions AsyncMachine FSM
- AsyncClaudeDriver + AsyncGeminiDriver (create_subprocess_exec)

This is the V9 replacement for nexus7.py.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class V9Config:
    """V9 Configuration with sensible defaults."""
    # Workspace
    workspace_path: Path = field(default_factory=Path.cwd)
    verbose: bool = False

    # Claude
    claude_cli_path: str = "claude"
    claude_sonnet_model: str = "claude-sonnet-4-5-20250929"
    claude_opus_model: str = "claude-opus-4-5-20251101"

    # Gemini
    gemini_cli_path: str = "gemini"
    gemini_default_model: str = "gemini-3-pro-preview"
    gemini_persistent_mode: bool = True

    # Timeouts
    timeout: float = 300.0

    # Feature flags
    swarm_auto_route: bool = True
    hive_mind_budget_limit: int = 50000


async def main(config: V9Config):
    """Main async entry point."""
    from core.async_primitives import CancellationToken
    from core.drivers.async_factory import create_driver_factory
    from core.orchestration.async_orchestrator import create_async_orchestrator
    from core.interface.async_repl import create_async_repl

    # Create V9 components
    driver_factory = create_driver_factory(config, config.workspace_path)
    orchestrator = create_async_orchestrator(
        config=config,
        driver_factory=driver_factory,
        workspace_path=config.workspace_path,
    )

    # Create REPL
    repl = create_async_repl(
        orchestrator=orchestrator,
        config=config,
        workspace_path=config.workspace_path,
    )

    # Run
    token = CancellationToken()

    try:
        await repl.run(token)
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        token.cancel("User interrupt")
    except Exception as e:
        print(f"\n[Error] {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
    finally:
        # Cleanup any remaining processes
        from core.async_primitives.process_handle import get_process_registry
        registry = get_process_registry()
        await registry.cancel_all()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="NEXUS V9.0 - Async-First Multi-Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nexus9.py                    # Run in current directory
  python nexus9.py --workspace ./proj # Run in specific workspace
  python nexus9.py --verbose          # Enable verbose logging

For V7 compatibility, use nexus7.py instead.
        """
    )

    parser.add_argument(
        '--workspace', '-w',
        type=Path,
        default=Path.cwd(),
        help='Workspace directory (default: current directory)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--timeout', '-t',
        type=float,
        default=300.0,
        help='Command timeout in seconds (default: 300)'
    )

    parser.add_argument(
        '--claude-model',
        type=str,
        default='claude-sonnet-4-5-20250929',
        help='Claude model to use'
    )

    parser.add_argument(
        '--gemini-model',
        type=str,
        default='gemini-3-pro-preview',
        help='Gemini model to use'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='NEXUS V9.0.0 (Async-First Architecture)'
    )

    return parser.parse_args()


def run():
    """Synchronous entry point for CLI."""
    args = parse_args()

    # Create config from args
    config = V9Config(
        workspace_path=args.workspace.resolve(),
        verbose=args.verbose,
        timeout=args.timeout,
        claude_sonnet_model=args.claude_model,
        gemini_default_model=args.gemini_model,
    )

    # Ensure workspace exists
    config.workspace_path.mkdir(parents=True, exist_ok=True)

    # Configure logging
    if config.verbose:
        import logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
    else:
        import logging
        logging.basicConfig(
            level=logging.WARNING,
            format='%(message)s'
        )

    # Run async main
    try:
        asyncio.run(main(config))
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    run()
