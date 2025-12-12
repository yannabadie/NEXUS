"""
V9 Swarm Commands - /swarm, /swarm-status, /swarm-fsm

These commands manage the Hybrid Swarm Engine for multi-agent collaboration.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class SwarmCommand(Command):
    """Execute a task using the Swarm Engine."""

    @property
    def name(self) -> str:
        return "/swarm"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Execute a task using multi-agent collaboration"

    @property
    def usage(self) -> str:
        return "/swarm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute swarm command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /swarm <task description>\nExample: /swarm Analyze this codebase and find bugs"
            )

        try:
            repl.run_swarm_task(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Swarm task failed: {e}"
            )


class SwarmStatusCommand(Command):
    """Show current Swarm Engine status."""

    @property
    def name(self) -> str:
        return "/swarm-status"

    @property
    def aliases(self) -> List[str]:
        return ["/ss"]

    @property
    def description(self) -> str:
        return "Show Swarm Engine status and DyLAN metrics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute swarm-status command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.show_swarm_status()
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
    """Execute a task using FSM-based Swarm mode."""

    @property
    def name(self) -> str:
        return "/swarm-fsm"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Execute task via FSM states (SWARM_ANALYZING -> NEGOTIATING -> EXECUTING)"

    @property
    def usage(self) -> str:
        return "/swarm-fsm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute swarm-fsm command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /swarm-fsm <task description>\nDebug: Uses FSM states (SWARM_ANALYZING -> NEGOTIATING -> EXECUTING)"
            )

        try:
            repl.run_swarm_task_fsm(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Swarm FSM task failed: {e}"
            )


def register_swarm_commands(registry: "CommandRegistry") -> None:
    """Register all swarm commands with a registry."""
    registry.register(SwarmCommand())
    registry.register(SwarmStatusCommand())
    registry.register(SwarmFSMCommand())
