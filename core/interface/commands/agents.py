"""
V9 Agent Commands - /spawn, /agents, /pool-stats

These commands manage spawned agents and the agent pool.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class SpawnCommand(Command):
    """Spawn a new specialized agent."""

    @property
    def name(self) -> str:
        return "/spawn"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Spawn a new specialized agent with a specific role"

    @property
    def usage(self) -> str:
        return "/spawn <role> (e.g., /spawn SQL Expert)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute spawn command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /spawn <role> (e.g., /spawn SQL Expert)"
            )

        try:
            repl.spawn_agent(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to spawn agent: {e}"
            )


class AgentsCommand(Command):
    """List all registered agents."""

    @property
    def name(self) -> str:
        return "/agents"

    @property
    def aliases(self) -> List[str]:
        return ["/a"]

    @property
    def description(self) -> str:
        return "List all registered agents and their capabilities"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute agents command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.list_agents()
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
    """Show agent pool statistics."""

    @property
    def name(self) -> str:
        return "/pool-stats"

    @property
    def aliases(self) -> List[str]:
        return ["/ps"]

    @property
    def description(self) -> str:
        return "Show agent pool statistics and usage metrics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute pool-stats command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.show_pool_stats()
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
    """Register all agent commands with a registry."""
    registry.register(SpawnCommand())
    registry.register(AgentsCommand())
    registry.register(PoolStatsCommand())
