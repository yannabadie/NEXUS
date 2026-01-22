"""
V9.1 Swarm Commands - /swarm, /swarm-status, /swarm-fsm

These commands manage the Hybrid Swarm Engine for multi-agent collaboration.
Uses SwarmService for business logic (Service Layer Pattern).
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus, CommandRegistry


def _get_swarm_service(context: CommandContext):
    """Gets or creates a SwarmService instance from the command context.

    Retrieves the SwarmService from context extras if available. Otherwise,
    initializes a new SwarmService using the orchestrator, console, and configuration
    found in the context or its components.

    Args:
        context (CommandContext): The command execution context containing
            orchestrator, console, and configuration.

    Returns:
        SwarmService: An initialized SwarmService instance.

    Raises:
        ImportError: If the SwarmService class cannot be imported.
        AttributeError: If the context is invalid or missing required components.
    """
    from core.swarm import SwarmService

    # Try to get cached service from extras
    service = context.extras.get("swarm_service")
    if service:
        return service

    # Get config from extras or orchestrator
    config = context.config
    if not config and hasattr(context.orchestrator, 'config'):
        config = context.orchestrator.config

    if not config:
        # Fallback: try to get from repl if available
        repl = context.extras.get("repl")
        if repl and hasattr(repl, 'config'):
            config = repl.config

    return SwarmService(
        orchestrator=context.orchestrator,
        console=context.console,
        config=config
    )


class SwarmCommand(Command):
    """Command to execute a task using the Swarm Engine.

    Attributes:
        name (str): The command name ("/swarm").
        aliases (List[str]): List of command aliases.
        description (str): Command description.
        usage (str): Usage string.
    """

    @property
    def name(self) -> str:
        """Gets the primary command name.

        Returns:
            str: The primary command name "/swarm".
        """
        return "/swarm"

    @property
    def aliases(self) -> List[str]:
        """Gets the list of command aliases.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Gets the command description.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Execute a task using multi-agent collaboration"

    @property
    def usage(self) -> str:
        """Gets the usage format string.

        Returns:
            str: The usage pattern for the command.
        """
        return "/swarm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the swarm command using SwarmService.

        Args:
            args (str): The arguments provided to the command (task description).
            context (CommandContext): The execution context.

        Returns:
            CommandResult: The result of the command execution, indicating success or failure.

        Raises:
            Exception: Any unexpected error during execution is caught and returned as a failure result.
        """
        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /swarm <task description>\nExample: /swarm Analyze this codebase and find bugs"
            )

        try:
            service = _get_swarm_service(context)
            result = service.run_task(args.strip())

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Swarm task failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Swarm task failed: {e}"
            )


class SwarmStatusCommand(Command):
    """Command to show the current Swarm Engine status.

    Attributes:
        name (str): The command name ("/swarm-status").
        aliases (List[str]): List of command aliases.
        description (str): Command description.
    """

    @property
    def name(self) -> str:
        """Gets the primary command name.

        Returns:
            str: The primary command name "/swarm-status".
        """
        return "/swarm-status"

    @property
    def aliases(self) -> List[str]:
        """Gets the list of command aliases.

        Returns:
            List[str]: A list of alternative names like "/ss".
        """
        return ["/ss"]

    @property
    def description(self) -> str:
        """Gets the command description.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Show Swarm Engine status and DyLAN metrics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the swarm-status command.

        Retrieves and displays the current status of the Swarm Engine.

        Args:
            args (str): Command arguments (unused).
            context (CommandContext): The execution context.

        Returns:
            CommandResult: The result of the command execution.

        Raises:
            Exception: Any unexpected error during execution is caught and returned as a failure result.
        """
        try:
            service = _get_swarm_service(context)
            service.get_status()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get swarm status: {e}"
            )


class SwarmFSMCommand(Command):
    """Command to execute a task using FSM-based Swarm mode.

    Attributes:
        name (str): The command name ("/swarm-fsm").
        aliases (List[str]): List of command aliases.
        description (str): Command description.
        usage (str): Usage string.
    """

    @property
    def name(self) -> str:
        """Gets the primary command name.

        Returns:
            str: The primary command name "/swarm-fsm".
        """
        return "/swarm-fsm"

    @property
    def aliases(self) -> List[str]:
        """Gets the list of command aliases.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Gets the command description.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Execute task via FSM states (debug mode)"

    @property
    def usage(self) -> str:
        """Gets the usage format string.

        Returns:
            str: The usage pattern for the command.
        """
        return "/swarm-fsm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the swarm-fsm command in debug mode.

        Runs the task using the Finite State Machine (FSM) based Swarm mode.

        Args:
            args (str): The task description.
            context (CommandContext): The execution context.

        Returns:
            CommandResult: The result of the command execution.

        Raises:
            Exception: Any unexpected error during execution is caught and returned as a failure result.
        """
        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /swarm-fsm <task description>\nDebug: Uses FSM states (SWARM_ANALYZING -> NEGOTIATING -> EXECUTING)"
            )

        try:
            service = _get_swarm_service(context)
            result = service.run_task_fsm(args.strip())

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Swarm FSM task failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Swarm FSM task failed: {e}"
            )


def register_swarm_commands(registry: CommandRegistry) -> None:
    """Registers all swarm commands with the provided registry.

    Args:
        registry (CommandRegistry): The registry to register commands with.

    Raises:
        AttributeError: If the registry is None or missing the register method.
    """
    registry.register(SwarmCommand())
    registry.register(SwarmStatusCommand())
    registry.register(SwarmFSMCommand())
