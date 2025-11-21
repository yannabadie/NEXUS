"""
Windows Task Scheduler Script

Checks for PENDING_REVIEW.md and sends alert if email is disabled.

Schedule this script to run every hour via Windows Task Scheduler:
> schtasks /create /tn "NEXUS_Review_Checker" /tr "python C:\Code\NEXUS\20_NEXUS\scripts\check_pending_review.py" /sc hourly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "NEXUS_V6_PROTOTYPE"))

from core.config import load_config
from core.notifications import check_pending_review


def main():
    """Main entry point for scheduled task"""
    config = load_config()

    # Only run if email is disabled (otherwise email handles notifications)
    if config.email_enabled:
        print("[TASK SCHEDULER] Email enabled - skipping file check")
        return

    # Check for pending review
    pending = check_pending_review(config.workspace_path)

    if pending:
        generation = pending['generation']
        children_count = pending['children_count']
        hours_elapsed = pending['hours_elapsed']

        print(f"""
╔═══════════════════════════════════════════════════════════╗
║ ⚠️  NEXUS REVIEW REQUIRED                                 ║
╚═══════════════════════════════════════════════════════════╝

Generation: {generation}
Children Awaiting Review: {children_count}
Elapsed Time: {hours_elapsed:.1f}h

Location: {config.workspace_path}/.nexus/PENDING_REVIEW.md

Launch NEXUS REPL to review:
> cd {project_root}
> python NEXUS_V6_PROTOTYPE/nexus6.py
> /review

""")

        # Windows notification (optional - requires win10toast)
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(
                "NEXUS - Review Required",
                f"Generation {generation} ({children_count} children) awaiting review",
                duration=10,
                threaded=True
            )
        except ImportError:
            # win10toast not installed - skip desktop notification
            pass

    else:
        print("[TASK SCHEDULER] No pending reviews")


if __name__ == "__main__":
    main()
