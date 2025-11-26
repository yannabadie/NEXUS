"""
Automated First Evolution Script

This script automates the first evolution cycle:
1. Measures baseline V6.0
2. Creates 3 children (V6.1-A, B, C)
3. Checks evolution status
4. Reviews and selects best child

Usage:
    python run_first_evolution.py

Note: This script will run NEXUS in interactive mode.
      You can monitor progress in real-time.
"""

import subprocess
import sys
import time
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")

def run_nexus_command(command, description):
    """
    Run a single NEXUS command

    Args:
        command: Command to send to NEXUS REPL
        description: Human-readable description
    """
    print_header(description)
    print(f"Command: {command}\n")

    # Note: This creates a new NEXUS session for each command
    # In a real scenario, we'd need to maintain a persistent session
    # For now, this serves as documentation

    print(f"⚠️  MANUAL STEP REQUIRED:")
    print(f"    1. Open NEXUS REPL: python nexus6.py")
    print(f"    2. Enter command: {command}")
    print(f"    3. Wait for completion")
    print(f"    4. Press Enter here to continue...\n")

    input("Press Enter when done...")
    print("✓ Step completed\n")

def main():
    """Main execution flow"""

    print_header("🧬 NEXUS V6.0 - First Evolution Automation")

    print("""
This script will guide you through the first evolution cycle.

IMPORTANT: This is a SEMI-AUTOMATED process.
You will need to manually execute commands in the NEXUS REPL
and confirm completion here.

Why semi-automated?
- NEXUS REPL is interactive and stateful
- Evolution can take 10-30 minutes
- You need to monitor progress in real-time

Prerequisites:
✓ V6.0 validated and functional
✓ All commits pushed to remote
✓ Bootstrap passes (python nexus6.py --verify)
✓ .env configured (if notifications desired)

Ready to start?
""")

    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y', 'oui', 'o']:
        print("❌ Evolution cancelled by user")
        sys.exit(0)

    # Step 1: Baseline measurement
    run_nexus_command(
        "Effectue un test complet de tes capacités actuelles. Mesure ton ASI Proximity Score baseline avant toute évolution. Documente les résultats dans workspace/baseline_v6.0.md",
        "Step 1: Baseline V6.0 Measurement"
    )

    # Step 2: Create children
    run_nexus_command(
        "/evolve 3",
        "Step 2: Create 3 Children (V6.1-A, V6.1-B, V6.1-C)"
    )

    # Step 3: Check status
    run_nexus_command(
        "/evolve-status",
        "Step 3: Verify Evolution Status"
    )

    # Step 4: Review and select
    run_nexus_command(
        "/review",
        "Step 4: Review and Select Best Child"
    )

    print_header("🎉 Evolution Cycle Complete!")

    print("""
Next Steps:

1. Verify LINEAGE.json was updated:
   > type LINEAGE.json

2. Check evolution report:
   > type workspace\\EVOLUTION_REPORT_GEN6.md

3. Commit results:
   > git add LINEAGE.json workspace/
   > git commit -m "evolution(v6): First generation complete"
   > git push origin N6P

4. Review and decide:
   - If improvement: Continue with /evolve 3 for Gen 7
   - If stagnation: Analyze and adjust mutations
   - If errors: Check docs/sessions/CORRECTIONS_LOG.md

Documentation:
- See EVOLUTION_START_GUIDE.md for detailed info
- See SESSION_CONTINUITY.md for project state
- See docs/debugging/ for troubleshooting

🧬 Evolution pathway: V6.0 → V6.1 → V6.2 → ... → ASI
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Evolution interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("See EVOLUTION_START_GUIDE.md for troubleshooting")
        sys.exit(1)
