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
from typing import Dict, Optional, Any, TYPE_CHECKING
import os

from core.agents.unified_registry import get_registry  # V8.4.0

if TYPE_CHECKING:
    from rich.console import RenderableType


class ConsoleV7:
    """Console UI minimaliste pour NEXUS"""

    def __init__(self, verbose: bool = False) -> None:
        """
        Initialize console

        Args:
            verbose: Si True, affiche détails FSM et JSON
        """
        # V9.1.1: Let Rich auto-detect terminal capabilities
        # - Don't force legacy_windows=False (breaks on conhost.exe)
        # - Don't force force_terminal=True (let Rich decide)
        # Rich will use VT100 if available, fallback to Windows API otherwise
        self.console: Console = Console()
        self.verbose: bool = verbose

    def print_banner(self, gemini_model: str, claude_model: str, version: Optional[str] = None, codename: Optional[str] = None) -> None:
        """
        Print NEXUS banner au démarrage

        Args:
            gemini_model: Nom du modèle Gemini détecté
            claude_model: Nom du modèle Claude détecté
            version: Version from config (e.g., "8.3.1")
            codename: Codename from config (e.g., "TRUE HIVE MIND")
        """
        # Default values if not provided (backward compatibility)
        version = version or "8.3.1"
        codename = codename or "TRUE HIVE MIND"

        banner = f"""
╔═══════════════════════════════════════════════════════════╗
║        NEXUS V{version} "{codename}"           ║
║              Persistent FSM Orchestrator                  ║
╚═══════════════════════════════════════════════════════════╝

🧠 Gemini: {gemini_model}
🛠️  Claude: {claude_model} (Dynamic: Opus for evolution/brainstorm)

Mode: Hybrid Drivers (Natural Language + XML Tools)
Type your task or use slash commands (/help for list)
"""
        self.console.print(banner, style="bold cyan")

    def display_result(self, result: Dict[str, Any]) -> None:
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
        state: Optional[str] = result.get("state")
        output: Optional[str] = result.get("output")
        agent: Optional[str] = result.get("agent")
        error: Optional[str] = result.get("error")

        # State transition (verbose only)
        if self.verbose and state and state != "IDLE":
            self.console.print(f"[dim][FSM: {state}][/dim]")

        # Agent message
        if output and agent:
            # V7 FIX: Handle Swarm agent with distinct color
            # V8.4.0: Use registry for agent identification
            registry = get_registry()
            if registry.is_gemini(agent):
                color = "cyan"
                self.console.print(f"[{color}][{agent}][/{color}] {output}")
            elif agent == "Swarm":
                # V7 FIX: Swarm output already has [Swarm] prefix from orchestration
                # Don't add another prefix, just use magenta color for the whole output
                color = "magenta"
                self.console.print(f"[{color}]{output}[/{color}]")
            else:  # Claude or others
                color = "green"
                self.console.print(f"[{color}][{agent}][/{color}] {output}")
        elif output and not agent:
            # Output without agent (system messages)
            self.console.print(output)

        # Tool execution indication
        if state == "EXECUTING_TOOL" and "tool" in result:
            tool_name: str = result["tool"]
            self.console.print(f"[yellow]⚙️  Executing: {tool_name}[/yellow]")

        # Error
        if error:
            self.console.print(f"[red]❌ {error}[/red]")

        # Validation results
        if output and "✓" in str(output):
            self.console.print(output, style="green")
        elif output and "✗" in str(output):
            self.console.print(output, style="yellow")

    def print_status(self, status: Dict[str, Any]) -> None:
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
        state: str = status.get('state', 'Unknown')
        agent: str = status.get('agent', 'Unknown')
        iteration: int = status.get('iteration', 0)
        objective: str = status.get('objective', 'Unknown')
        
        content: str = f"""State: {state}
Active Agent: {agent}
Iteration: {iteration}
Objective: {objective}"""

        panel = Panel(
            content,
            title="📊 Orchestrator Status",
            border_style="cyan"
        )
        self.console.print(panel)

    def print_doctor_results(self, results: Dict[str, Any]) -> None:
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
        gemini: Dict[str, Any] = results.get("gemini", {})
        claude: Dict[str, Any] = results.get("claude", {})

        gemini_status: str = "✓" if gemini.get("available", False) else "❌"
        claude_status: str = "✓" if claude.get("available", False) else "❌"

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

    def print_help(self, help_message: str) -> None:
        """Print help message"""
        panel: Panel = Panel(help_message, title="Help", border_style="cyan")
        self.console.print(panel)

    def print_error(self, error: str) -> None:
        """Print error message"""
        error_message: str = f"[red]❌ {error}[/red]"
        self.console.print(error_message)

    def print(self, message: str, style: Optional[str] = None) -> None:
        """
        Print simple message

        Args:
            message: Message to print
            style: Rich style (e.g. "bold", "red", "cyan")
        """
        if style:
            renderable: "RenderableType" = message
            self.console.print(renderable, style=style)
        else:
            self.console.print(message)

    def clear(self) -> None:
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_spinner(self, text: str) -> Live:
        """
        Show animated spinner (context manager)

        Usage:
            with console.show_spinner("Processing..."):
                # Long operation
                time.sleep(5)

        Args:
            text: Spinner text
        """
        spinner: Spinner = Spinner("dots", text=text)
        return Live(
            spinner,
            console=self.console,
            refresh_per_second=10
        )

    def print_markdown(self, markdown_text: str) -> None:
        """
        Print formatted markdown

        Args:
            markdown_text: Markdown string
        """
        md = Markdown(markdown_text)
        self.console.print(md)
