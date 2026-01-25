"""
V9 System Commands - Status, Help, Doctor, etc.

These commands provide system information and diagnostics.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class StatusCommand(Command):
    """
    Show current NEXUS system status.

    Provides detailed information about the system's internal state,
    including FSM state, active agents, and memory statistics.
    """

    @property
    def name(self) -> str:
        """
        Get the command name.

        Returns:
            str: The primary command name ("/status").
        """
        return "/status"

    @property
    def aliases(self) -> List[str]:
        """
        Get the command aliases.

        Returns:
            List[str]: A list of alternative command names (e.g., ["/s"]).
        """
        return ["/s"]

    @property
    def description(self) -> str:
        """
        Get the command description.

        Returns:
            str: A brief description of what the command does.
        """
        return "Show current system status (FSM state, agents, memory)"

    @property
    def usage(self) -> str:
        """
        Get the command usage syntax.

        Returns:
            str: The usage string showing arguments.
        """
        return "/status [detail|brief]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute status command.

        Args:
            args: Command arguments ("detail" or "brief").
            context: Command execution context.

        Returns:
            CommandResult: Success result with status message.
        """
        try:
            status = context.orchestrator.get_system_status()

            # Format output based on args
            detail_level = args.strip().lower() if args else "normal"

            if detail_level == "brief":
                message = self._format_brief(status)
            elif detail_level == "detail":
                message = self._format_detail(status)
            else:
                message = self._format_normal(status)

            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=message,
                data=status
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get status: {e}"
            )

    def _format_brief(self, status: dict) -> str:
        """
        Brief one-line status.

        Args:
            status: System status dictionary.

        Returns:
            str: One-line status summary.
        """
        state = status.get("state", "UNKNOWN")
        agent = status.get("active_agent", "none")
        return f"State: {state} | Agent: {agent}"

    def _format_normal(self, status: dict) -> str:
        """
        Normal status display.

        Args:
            status: System status dictionary.

        Returns:
            str: Multi-line status overview.
        """
        lines = [
            "=== NEXUS Status ===",
            f"FSM State: {status.get('state', 'UNKNOWN')}",
            f"Active Agent: {status.get('active_agent', 'none')}",
            f"Iteration: {status.get('iteration', 0)}",
        ]

        # Add memory info if available
        if "memory" in status:
            mem = status["memory"]
            lines.append(f"Memory: {mem.get('history_length', 0)} turns")

        return "\n".join(lines)

    def _format_detail(self, status: dict) -> str:
        """
        Detailed status with all available info.

        Args:
            status: System status dictionary.

        Returns:
            str: Detailed status including blackboard.
        """
        lines = [self._format_normal(status), ""]

        # Add blackboard summary
        if "blackboard" in status:
            bb = status["blackboard"]
            lines.append("Blackboard:")
            for key, value in bb.items():
                if not key.startswith("_"):  # Skip private keys
                    val_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    lines.append(f"  {key}: {val_str}")

        return "\n".join(lines)


class HelpCommand(Command):
    """Show available commands and their usage."""

    def __init__(self, registry: "CommandRegistry" = None):
        """
        Initialize with optional registry reference.

        Args:
            registry: Optional command registry instance.
        """
        self._registry = registry

    def set_registry(self, registry: "CommandRegistry") -> None:
        """
        Set registry reference (for circular dependency).

        Args:
            registry: CommandRegistry instance.
        """
        self._registry = registry

    @property
    def name(self) -> str:
        """
        Get the command name.

        Returns:
            str: The primary command name ("/help").
        """
        return "/help"

    @property
    def aliases(self) -> List[str]:
        """
        Get the command aliases.

        Returns:
            List[str]: A list of alternative command names (e.g., ["/h", "/?"]).
        """
        return ["/h", "/?"]

    @property
    def description(self) -> str:
        """
        Get the command description.

        Returns:
            str: A brief description of what the command does.
        """
        return "Show available commands and their usage"

    @property
    def usage(self) -> str:
        """
        Get the command usage syntax.

        Returns:
            str: The usage string showing arguments.
        """
        return "/help [command]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute help command.

        Args:
            args: Command name to get help for, or empty for general help.
            context: Command execution context.

        Returns:
            CommandResult: Help message result.
        """
        if args.strip():
            # Help for specific command
            cmd_name = args.strip().lower()
            if not cmd_name.startswith("/"):
                cmd_name = "/" + cmd_name

            if self._registry and cmd_name in self._registry:
                cmd = self._registry.get_command(cmd_name)
                message = self._format_command_help(cmd)
            else:
                message = f"Unknown command: {cmd_name}"
                return CommandResult(
                    status=CommandStatus.NOT_FOUND,
                    message=message
                )
        else:
            # General help
            if self._registry:
                message = self._registry.get_help_text()
            else:
                message = "Help not available (no registry set)"

        return CommandResult(
            status=CommandStatus.HELP,
            message=message
        )

    def _format_command_help(self, cmd: Command) -> str:
        """
        Format detailed help for a single command.

        Args:
            cmd: Command instance.

        Returns:
            str: Formatted help string.
        """
        lines = [
            f"=== {cmd.name} ===",
            f"Description: {cmd.description}",
            f"Usage: {cmd.usage}",
        ]
        if cmd.aliases:
            lines.append(f"Aliases: {', '.join(cmd.aliases)}")
        return "\n".join(lines)


class QuitCommand(Command):
    """Exit NEXUS REPL."""

    @property
    def name(self) -> str:
        """
        Get the command name.

        Returns:
            str: The primary command name ("/quit").
        """
        return "/quit"

    @property
    def aliases(self) -> List[str]:
        """
        Get the command aliases.

        Returns:
            List[str]: A list of alternative command names (e.g., ["/exit", "/q"]).
        """
        return ["/exit", "/q"]

    @property
    def description(self) -> str:
        """
        Get the command description.

        Returns:
            str: A brief description of what the command does.
        """
        return "Exit NEXUS REPL"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute quit command.

        Args:
            args: Ignored arguments.
            context: Command execution context.

        Returns:
            CommandResult: Result with continue_session=False.
        """
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message="Goodbye!",
            continue_session=False
        )


def register_system_commands(registry: "CommandRegistry") -> None:
    """
    Register all system commands with a registry.

    Args:
        registry: CommandRegistry instance to register commands with.

    Returns:
        None
    """
    from .registry import CommandRegistry

    # Status command
    registry.register(StatusCommand())

    # Help command (needs registry reference)
    help_cmd = HelpCommand()
    help_cmd.set_registry(registry)
    registry.register(help_cmd)

    # Quit command
    registry.register(QuitCommand())
