"""
V9.1 Agent Commands - /spawn, /agents, /pool-stats

These commands manage spawned agents and the agent pool.
Uses AgentService for business logic (Service Layer Pattern).
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


def _get_agent_service(context: CommandContext):
    """Retrieves or creates an AgentService instance from the command context.

    Args:
        context: The command execution context containing orchestrator,
            workspace_path, and console access.

    Returns:
        AgentService: An initialized agent service instance.

    Raises:
        ValueError: If workspace_path cannot be determined from the context.
    """
    from core.agents import AgentService

    # Try to get cached service from extras
    service = context.extras.get("agent_service")
    if service:
        return service

    # Get workspace_path from extras or orchestrator
    workspace_path = context.extras.get("workspace_path")
    if not workspace_path and hasattr(context.orchestrator, 'workspace_path'):
        workspace_path = context.orchestrator.workspace_path

    if not workspace_path:
        # Fallback: try to get from repl if available
        repl = context.extras.get("repl")
        if repl and hasattr(repl, 'workspace_path'):
            workspace_path = repl.workspace_path

    if not workspace_path:
        raise ValueError("workspace_path not available in context")

    return AgentService(
        orchestrator=context.orchestrator,
        workspace_path=workspace_path,
        console=context.console
    )


class SpawnCommand(Command):
    """Command to spawn a new specialized agent.

    This command uses the AgentService to create a new agent instance
    based on the provided role.

    Attributes:
        None
    """

    @property
    def name(self) -> str:
        """Retrieves the unique identifier name of the command.

        Returns:
            str: The command name string (e.g., "/spawn").
        """
        return "/spawn"

    @property
    def aliases(self) -> List[str]:
        """Retrieves the list of alternative names for the command.

        Returns:
            List[str]: A list of string aliases.
        """
        return []

    @property
    def description(self) -> str:
        """Retrieves the user-friendly description of the command.

        Returns:
            str: A brief description of what the command does.
        """
        return "Spawn a new specialized agent with a specific role"

    @property
    def usage(self) -> str:
        """Retrieves the usage syntax for the command.

        Returns:
            str: The command usage string showing expected arguments.
        """
        return "/spawn <role> (e.g., /spawn SQL Expert)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the spawn command logic.

        Parses the arguments to get the agent role and delegates the creation
        to the AgentService.

        Args:
            args: The command arguments containing the agent role.
            context: The command execution context providing access to services.

        Returns:
            CommandResult: The outcome of the command execution, including
                success status and any error messages.
        """
        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /spawn <role> (e.g., /spawn SQL Expert)"
            )

        try:
            service = _get_agent_service(context)
            result = service.spawn(args.strip())

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Spawn failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to spawn agent: {e}"
            )


class AgentsCommand(Command):
    """Command to list all currently registered agents.

    Retrieves the list of active agents from the AgentService and displays
    them to the user via the console.

    Attributes:
        None
    """

    @property
    def name(self) -> str:
        """Retrieves the unique identifier name of the command.

        Returns:
            str: The command name ("/agents").
        """
        return "/agents"

    @property
    def aliases(self) -> List[str]:
        """Retrieves the list of alternative names for the command.

        Returns:
            List[str]: A list of alternative names (e.g., ["/a"]).
        """
        return ["/a"]

    @property
    def description(self) -> str:
        """Retrieves the user-friendly description of the command.

        Returns:
            str: A brief description of what the command does.
        """
        return "List all registered agents and their capabilities"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the agents command to list registered agents.

        Delegates the listing operation to the AgentService.

        Args:
            args: The command arguments (unused for this command).
            context: The command execution context providing access to services.

        Returns:
            CommandResult: The outcome of the command execution.
        """
        try:
            service = _get_agent_service(context)
            service.list_agents()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to list agents: {e}"
            )


class PoolStatsCommand(Command):
    """Command to display statistics about the agent pool.

    Attributes:
        None
    """

    @property
    def name(self) -> str:
        """Gets the unique name of the command.

        Returns:
            str: The command name ("/pool-stats").
        """
        return "/pool-stats"

    @property
    def aliases(self) -> List[str]:
        """Gets the list of aliases for the command.

        Returns:
            List[str]: A list of alternative names (e.g., ["/ps"]).
        """
        return ["/ps"]

    @property
    def description(self) -> str:
        """Gets a brief description of the command.

        Returns:
            str: The command description.
        """
        return "Show agent pool statistics and usage metrics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the pool-stats command to show agent pool metrics.

        Args:
            args: The command arguments (unused for this command).
            context: The execution context containing dependencies.

        Returns:
            CommandResult: The result indicating success or failure of the stats operation.
        """
        try:
            service = _get_agent_service(context)
            service.get_pool_stats()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get pool stats: {e}"
            )


def register_agent_commands(registry: "CommandRegistry") -> None:
    """Registers all agent-related commands with the provided registry.

    Args:
        registry: The command registry to register the commands with.

    Returns:
        None
    """
    registry.register(SpawnCommand())
    registry.register(AgentsCommand())
    registry.register(PoolStatsCommand())
