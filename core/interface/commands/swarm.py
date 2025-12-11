"""
Swarm Commands for NEXUS V7.

Handles /swarm, /swarm-status, /swarm-fsm.
"""

from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class SwarmCommand(Command):
    """Execute a task using the Swarm Engine."""

    @property
    def name(self) -> str:
        return "/swarm"

    @property
    def description(self) -> str:
        return "Execute a task using the Hybrid Swarm Engine"

    @property
    def usage(self) -> str:
        return "/swarm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        if not args.strip():
            return CommandResult(
                CommandStatus.INVALID_ARGS, 
                "Usage: /swarm <task description>\nExample: /swarm Analyze this codebase and find bugs"
            )

        try:
            repl.run_swarm_task(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Swarm task failed: {e}")


class SwarmStatusCommand(Command):
    """Show Swarm Engine status."""

    @property
    def name(self) -> str:
        return "/swarm-status"

    @property
    def description(self) -> str:
        return "Show current status of the Swarm Engine"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.show_swarm_status()
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Failed to show swarm status: {e}")


class SwarmFSMCommand(Command):
    """Debug Swarm FSM."""

    @property
    def name(self) -> str:
        return "/swarm-fsm"

    @property
    def description(self) -> str:
        return "Execute Swarm task using explicit FSM states (Debug)"

    @property
    def usage(self) -> str:
        return "/swarm-fsm <task description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        if not args.strip():
            return CommandResult(
                CommandStatus.INVALID_ARGS,
                "Usage: /swarm-fsm <task description>"
            )

        try:
            repl.run_swarm_task_fsm(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Swarm FSM task failed: {e}")
