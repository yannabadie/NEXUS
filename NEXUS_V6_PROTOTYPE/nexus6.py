#!/usr/bin/env python3
"""
NEXUS V6.0 - The Omniscient REPL
Persistent FSM Orchestrator with Hybrid Drivers

Architecture:
- FSM (Finite State Machine) for persistent state management
- Claude Hybrid Driver (natural language + XML tool blocks)
- Gemini JSON Driver (strict JSON mode)
- Adaptive stagnation detection
- Bootstrap verification at startup
"""
import sys
import argparse
from pathlib import Path
import importlib.util

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Constantes
ENV_TEMPLATE = """# NEXUS V6.0 Configuration
GEMINI_CLI_PATH=gemini
CLAUDE_CLI_PATH=claude
MAX_STALEMATE_COUNT=5
STAGNATION_SIMILARITY_THRESHOLD=0.8
WORKSPACE_PATH=./workspace
LOG_LEVEL=INFO
UI_VERBOSE=False
"""

def bootstrap():
    """
    Bootstrap NEXUS V6 - Vérifie tout avant de démarrer

    Vérifie:
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
    print("🚀 NEXUS V6.0 Bootstrap...")

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
    print("✅ NEXUS V6.0 Bootstrap Complete")
    print("="*60)
    print(f"\n📊 Gemini")
    print(f"   Model: {gemini_info['model']}")
    print(f"   Context: {gemini_info['context_window']:,} tokens")
    print(f"   Version: {gemini_info.get('version', 'Unknown')}")

    print(f"\n🧠 Claude")
    print(f"   Model: {claude_info['model']}")
    print(f"   Context: {claude_info['context_window']:,} tokens")
    print(f"   Version: {claude_info.get('version', 'Unknown')}")

    print("\n" + "="*60)
    print()

    return gemini_info, claude_info


def main():
    """Entry point NEXUS V6.0"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="NEXUS V6.0 - The Omniscient REPL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nexus6                    Launch interactive REPL
  nexus6 --verify           Verify installation (bootstrap only)
  nexus6 --version          Show version
  nexus6 --workspace ./myproject  Use custom workspace

Documentation: https://github.com/nexus-ai/nexus-v6
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
        print("NEXUS V6.0 - The Omniscient REPL")
        print("Persistent FSM Orchestrator with Hybrid Drivers")
        print("https://github.com/nexus-ai/nexus-v6")
        sys.exit(0)

    try:
        # Bootstrap system
        gemini_info, claude_info = bootstrap()

        # Handle --verify (exit after bootstrap)
        if args.verify:
            print("\n✅ Bootstrap verification successful!")
            print("   NEXUS V6.0 is ready to use.")
            sys.exit(0)

        # Import and launch REPL
        from core.interface.repl import InteractiveNexusV6

        workspace_path = Path(args.workspace).resolve()
        workspace_path.mkdir(parents=True, exist_ok=True)

        repl = InteractiveNexusV6(
            workspace_path=workspace_path,
            gemini_info=gemini_info,
            claude_info=claude_info
        )

        # Run interactive loop
        repl.run()

    except KeyboardInterrupt:
        print("\n\n👋 NEXUS V6.0 terminated by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
