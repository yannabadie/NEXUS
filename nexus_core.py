#!/usr/bin/env python3
"""
NEXUS CORE - Unified Entry Point
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from NEXUS_V7_CHRYSALIS.core.swarm.standalone import StandaloneSwarm
from NEXUS_V7_CHRYSALIS.core.evolution.project_evolver import ProjectEvolver
from NEXUS_V7_CHRYSALIS.core.config import NexusConfig

def main():
    parser = argparse.ArgumentParser(description="NEXUS CORE - Autonomous Collaborative Intelligence")
    parser.add_argument("objective", help="The task to accomplish", nargs='?')
    parser.add_argument("--evolve", action="store_true", help="Run in Project Evolution mode")
    parser.add_argument("--context", help="Path to project context", default=".")
    parser.add_argument("--config", help="Path to config file", default=None)

    args = parser.parse_args()

    print(f"🚀 NEXUS CORE Initializing...")
    print(f"📂 Context: {args.context}")

    # Load config
    config = NexusConfig.load_from_env()

    if args.evolve:
        print("🧬 Mode: Project Evolution")
        evolver = ProjectEvolver(config, args.context)
        evolver.evolve()
    elif args.objective:
        print(f"🎯 Objective: {args.objective}")
        # Initialize Core
        swarm = StandaloneSwarm(config=config)
        # Execute
        result = swarm.process(args.objective)
        print("\n✅ Result:")
        print(result.final_output)
    else:
        print("❌ Error: Must provide either an objective or use the --evolve flag.")
        print("   Run 'python nexus_core.py --help' for usage information.")
        parser.print_help()

if __name__ == "__main__":
    main()
