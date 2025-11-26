"""
Console UI V7 - Interface minimaliste avec Rich

Principes:
- Affiche: messages agents (content), résumés d'actions, résultats outils
- Cache: JSON, thought_process, internal state (sauf mode verbose)
- Utilise Rich pour: spinners, panels, formatting
"""
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.markdown import Markdown
from typing import Dict, Optional
import os


class ConsoleV7:
    """Console UI minimaliste pour NEXUS V7"""

    def __init__(self, verbose: bool = False):
        """
        Initialize console

        Args:
            verbose: Si True, affiche détails FSM et JSON
        """
        self.console = Console()
        self.verbose = verbose

    def print_banner(self, gemini_model: str, claude_model: str):
        """
        Print NEXUS V7 banner au démarrage

        Args:
            gemini_model: Nom du modèle Gemini détecté
            claude_model: Nom du modèle Claude détecté
        """
        banner = f"""
╔═══════════════════════════════════════════════════════════╗
║        NEXUS V7.0 "Chrysalis" - OMNISCIENT REPL           ║
║              Persistent FSM Orchestrator                  ║
╚═══════════════════════════════════════════════════════════╝

🧠 Gemini: {gemini_model}
🛠️  Claude: {claude_model} (Dynamic: Opus for evolution/brainstorm)

Mode: Hybrid Drivers (Natural Language + XML Tools)
Type your task or use slash commands (/help for list)
"""
        self.console.print(banner, style="bold cyan")

    def display_result(self, result: Dict):
        """
        Display turn result (appelé après chaque process_turn)

        Modes:
        - Normal: Affiche seulement content + résumé
        - Verbose: Affiche état FSM + détails

        Args:
            result: Dict returned by orchestrator.process_turn()
                {
                    "state": str,
                    "output": str,
                    "agent": str,
                    "finished": bool,
                    "error": Optional[str]
                }
        """
        state = result.get("state")
        output = result.get("output")
        agent = result.get("agent")
        error = result.get("error")

        # State transition (verbose only)
        if self.verbose and state and state != "IDLE":
            self.console.print(f"[dim][FSM: {state}][/dim]")

        # Agent message
        if output and agent:
            color = "cyan" if agent == "Gemini" else "green"
            self.console.print(f"[{color}][{agent}][/{color}] {output}")
        elif output and not agent:
            # Output without agent (system messages)
            self.console.print(output)

        # Tool execution indication
        if state == "EXECUTING_TOOL" and "tool" in result:
            tool_name = result["tool"]
            self.console.print(f"[yellow]⚙️  Executing: {tool_name}[/yellow]")

        # Error
        if error:
            self.console.print(f"[red]❌ {error}[/red]")

        # Validation results
        if "✓" in str(output):
            self.console.print(output, style="green")
        elif "✗" in str(output):
            self.console.print(output, style="yellow")

    def print_status(self, status: Dict):
        """
        Print orchestrator status (/status command)

        Args:
            status: {
                "state": str,
                "agent": str,
                "iteration": int,
                "objective": str
            }
        """
        content = f"""State: {status['state']}
Active Agent: {status['agent']}
Iteration: {status['iteration']}
Objective: {status['objective']}"""

        panel = Panel(
            content,
            title="📊 Orchestrator Status",
            border_style="cyan"
        )
        self.console.print(panel)

    def print_doctor_results(self, results: Dict):
        """
        Print diagnostics results (/doctor command)

        Args:
            results: {
                "gemini": {...},
                "claude": {...},
                "workspace": bool,
                "io_buffer": bool
            }
        """
        gemini = results["gemini"]
        claude = results["claude"]

        gemini_status = "✓" if gemini["available"] else "❌"
        claude_status = "✓" if claude["available"] else "❌"

        content = f"""{gemini_status} Gemini CLI: {gemini.get('model', 'N/A')}
{claude_status} Claude CLI: {claude.get('model', 'N/A')}
{"✓" if results.get('workspace') else "❌"} Workspace directory
{"✓" if results.get('io_buffer') else "❌"} IO Buffer directory"""

        panel = Panel(
            content,
            title="🔍 System Diagnostics",
            border_style="green" if results.get("workspace") and results.get("io_buffer") else "yellow"
        )
        self.console.print(panel)

    def print_help(self, help_message: str):
        """Print help message"""
        self.console.print(Panel(help_message, title="Help", border_style="cyan"))

    def print_error(self, error: str):
        """Print error message"""
        self.console.print(f"[red]❌ {error}[/red]")

    def print(self, message: str, style: Optional[str] = None):
        """
        Print simple message

        Args:
            message: Message to print
            style: Rich style (e.g. "bold", "red", "cyan")
        """
        if style:
            self.console.print(message, style=style)
        else:
            self.console.print(message)

    def clear(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_spinner(self, text: str):
        """
        Show animated spinner (context manager)

        Usage:
            with console.show_spinner("Processing..."):
                # Long operation
                time.sleep(5)

        Args:
            text: Spinner text
        """
        return Live(
            Spinner("dots", text=text),
            console=self.console,
            refresh_per_second=10
        )

    def print_markdown(self, markdown_text: str):
        """
        Print formatted markdown

        Args:
            markdown_text: Markdown string
        """
        md = Markdown(markdown_text)
        self.console.print(md)
