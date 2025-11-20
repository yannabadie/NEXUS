"""
NEXUS V5.0 - Console UI
Affichage Rich avec panels pour visualisation de la symbiose.
"""
from typing import Dict, Any, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console
    class Console:
        """Fallback console when rich unavailable."""
        def print(self, message, style="", **kwargs):
            print(message)

    class Panel:
        """Fallback panel when rich unavailable."""
        def __init__(self, content, title="", border_style="", style=""):
            self.content = content
            self.title = title

        def __str__(self):
            if self.title:
                return f"\n=== {self.title} ===\n{self.content}\n"
            return str(self.content)

    console = Console()


def log(message: str, style: str = ""):
    """Log simple."""
    if RICH_AVAILABLE:
        console.print(message, style=style)
    else:
        print(message)


def display_header(mode: str, iteration: int, stalemate_counter: int = 0):
    """Affiche le header avec informations de session."""
    header_text = f"NEXUS V5.0 | Mode: {mode} | Tour: {iteration}"

    if stalemate_counter > 0:
        header_text += f" | ⚠ Stalemate: {stalemate_counter}"

    panel = Panel(header_text, style="bold white on blue")
    if RICH_AVAILABLE:
        console.print(panel)
    else:
        print(panel)


def display_thought_process(message: Dict, agent: str):
    """Affiche la pensée de l'agent."""
    color = "cyan" if agent == "Gemini" else "magenta"
    title = f"[{agent.upper()} - Stratège]" if agent == "Gemini" else f"[{agent.upper()} - Exécutant]"

    # Thought process
    if "thought_process" in message:
        thoughts = message["thought_process"]
        thought_text = "\n".join([
            f"  {t['step']}. {t['reasoning']}"
            for t in thoughts
        ])
        panel = Panel(thought_text, title=f"{title} Pensée", border_style=color)
        print(panel) if not RICH_AVAILABLE else console.print(panel)

    # Reflection
    if "reflection" in message:
        panel = Panel(message["reflection"], title=f"{title} Réflexion", border_style=color)
        print(panel) if not RICH_AVAILABLE else console.print(panel)

    # Action summary
    if "action_summary" in message:
        panel = Panel(message["action_summary"], title=f"{title} Action", border_style=color)
        print(panel) if not RICH_AVAILABLE else console.print(panel)


def display_tool_result(result: Dict):
    """Affiche le résultat d'un outil exécuté."""
    status = result.get("status", "UNKNOWN")

    if status == "SUCCESS":
        style = "green"
    elif status == "FAILURE":
        style = "yellow"
    else:
        style = "red"

    output = f"Tool: {result.get('tool_name')}\n"
    output += f"Status: {status}\n"
    output += f"Return Code: {result.get('returncode')}\n\n"

    if result.get("stdout"):
        output += f"STDOUT:\n{result['stdout'][:500]}\n"

    if result.get("stderr"):
        output += f"STDERR:\n{result['stderr'][:200]}\n"

    panel = Panel(output, title="[NEXUS - TOOL EXECUTOR]", border_style=style)
    print(panel) if not RICH_AVAILABLE else console.print(panel)


def display_cfl_review(review: Dict):
    """Affiche la revue CFL post-action."""
    status = review.get("validation_status", "UNKNOWN")

    if status == "SUCCESS":
        style = "bold green"
        emoji = "✓"
    elif status == "PARTIAL_SUCCESS":
        style = "yellow"
        emoji = "⚠"
    else:
        style = "bold red"
        emoji = "✗"

    output = f"{emoji} {status}\n\n"
    output += f"Analyse:\n{review.get('analysis', '')}\n"

    if review.get("discrepancies"):
        output += "\nÉcarts:\n"
        for disc in review["discrepancies"]:
            output += f"  - {disc}\n"

    if review.get("correction_plan"):
        output += f"\nPlan de correction:\n{review['correction_plan']}"

    panel = Panel(output, title="[CFL REVIEW]", border_style=style)
    print(panel) if not RICH_AVAILABLE else console.print(panel)


def display_strategic_plan(plan: list):
    """Affiche le plan stratégique."""
    if not plan:
        return

    output = ""
    for step in plan:
        status = step.get("status", "UNKNOWN")
        emoji = {
            "COMPLETED": "✓",
            "IN_PROGRESS": "→",
            "PENDING": " ",
            "FAILED": "✗"
        }.get(status, "?")

        output += f"{emoji} {step['step_id']}. {step['description']} [{status}]\n"

    panel = Panel(output, title="[PLAN STRATÉGIQUE]", border_style="blue")
    print(panel) if not RICH_AVAILABLE else console.print(panel)


def display_plan_health(health: Dict):
    """Affiche la santé du plan."""
    drift = health.get("drift_score", "UNKNOWN")

    if drift == "CRITICAL":
        style = "bold red"
    elif drift == "HIGH":
        style = "yellow"
    elif drift == "MEDIUM":
        style = "cyan"
    else:
        style = "green"

    output = f"Drift Score: {drift}\n"
    output += f"Steps bloquées (>20 tours): {health.get('steps_pending_more_than_20_turns', 0)}\n"
    output += f"Dernier progrès: tour {health.get('last_progress_turn', 0)}"

    panel = Panel(output, title="[PLAN HEALTH]", border_style=style)
    print(panel) if not RICH_AVAILABLE else console.print(panel)


def display_panic_alert(reason: str):
    """Affiche une alerte panic."""
    panel = Panel(
        f"🚨 ARRÊT D'URGENCE\n\nRaison: {reason}",
        title="[PANIC ABORT]",
        style="bold red on white"
    )
    print(panel) if not RICH_AVAILABLE else console.print(panel)
