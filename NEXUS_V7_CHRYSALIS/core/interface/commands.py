"""
Slash Commands - Commandes système pour NEXUS V7 Chrysalis

Commandes disponibles:
- /clear: Efface l'écran
- /status: Affiche l'état de l'orchestrateur
- /doctor: Diagnostique le système (CLIs, workspace)
- /reset: Reset l'orchestrateur à IDLE
- /mode <name>: Change le mode (Normal, InProjectImprovement, etc.)
- /chat: Mode conversation pure (pas d'outils)
- exit/quit: Quitter NEXUS
"""

# Available slash commands with descriptions
SLASH_COMMANDS = {
    "/clear": "Clear terminal screen",
    "/status": "Show orchestrator status (state, agent, iteration)",
    "/doctor": "Run system diagnostics (CLIs, workspace, memory)",
    "/reset": "Reset orchestrator to IDLE state",
    "/mode <name>": "Change mode (Normal, InProjectImprovement, etc.)",
    "/chat": "Enter chat-only mode (no tool execution)",
    "/bootstrap [path]": "Analyze project and generate NEXUS.md (default: current dir)",
    "/evolve [count]": "Create and evaluate child generations (default: 3)",
    "/evolve-status": "Show evolution stats and stagnation counter",
    "/pool-stats": "Show agent pool DyLAN metrics (importance scores)",
    "/specialize <mission>": "Create a specialized NEXUS spinoff for a specific mission",
    "/review": "Review and evaluate pending children from evolution",
    "/help": "Show this help message",
    "exit": "Exit NEXUS V7.0 Chrysalis"
}


def get_help_message() -> str:
    """
    Generate help message with all commands

    Returns:
        Formatted help string
    """
    help_lines = ["Available commands:"]

    for cmd, desc in SLASH_COMMANDS.items():
        help_lines.append(f"  {cmd:<20} - {desc}")

    return "\n".join(help_lines)


def is_slash_command(user_input: str) -> bool:
    """
    Check if input is a slash command

    Args:
        user_input: User's input string

    Returns:
        True if starts with '/'
    """
    return user_input.strip().startswith('/')


def is_exit_command(user_input: str) -> bool:
    """
    Check if input is an exit command

    Args:
        user_input: User's input string

    Returns:
        True if 'exit', 'quit', or 'q'
    """
    return user_input.strip().lower() in ['exit', 'quit', 'q']


def parse_command(user_input: str) -> tuple:
    """
    Parse slash command into (command, args)

    Args:
        user_input: Slash command string (e.g. "/mode Normal")

    Returns:
        Tuple (command, args)
        Example: ("/mode Normal") → ("/mode", "Normal")

    Examples:
        >>> parse_command("/clear")
        ('/clear', '')

        >>> parse_command("/mode Normal")
        ('/mode', 'Normal')

        >>> parse_command("/status")
        ('/status', '')
    """
    parts = user_input.strip().split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ''

    return command, args
