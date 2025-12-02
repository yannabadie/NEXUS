#!/usr/bin/env python3
"""
NEXUS CORE - Unified Entry Point
"""
import sys
import argparse
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from NEXUS_V7_CHRYSALIS.core.swarm.standalone import StandaloneSwarm

def main():
    parser = argparse.ArgumentParser(description="NEXUS CORE - Autonomous Collaborative Intelligence")
    parser.add_argument("objective", help="The task to accomplish")
    parser.add_argument("--context", help="Path to project context", default=".")
    parser.add_argument("--config", help="Path to config file", default=None)

    args = parser.parse_args()

    print(f"🚀 NEXUS CORE Initializing...")
    print(f"🎯 Objective: {args.objective}")
    print(f"📂 Context: {args.context}")

    # Initialize Core
    swarm = StandaloneSwarm(config=args.config)

    # Execute
    result = swarm.process(args.objective)

    print("\n✅ Result:")
    print(result.final_output)

if __name__ == "__main__":
    main()
