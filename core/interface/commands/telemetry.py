"""
Telemetry Commands for NEXUS V7.

Handles /telemetry, /budget.
"""

from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class TelemetryCommand(Command):
    """Manage telemetry."""

    @property
    def name(self) -> str:
        return "/telemetry"

    @property
    def description(self) -> str:
        return "Manage telemetry (status, export)"

    @property
    def usage(self) -> str:
        return "/telemetry [status|export [days]]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_telemetry_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Telemetry command failed: {e}")


class BudgetCommand(Command):
    """Manage API budget."""

    @property
    def name(self) -> str:
        return "/budget"

    @property
    def description(self) -> str:
        return "Manage API budget (status, reset, add)"

    @property
    def usage(self) -> str:
        return "/budget [reset|add <amount>|history]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_budget_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Budget command failed: {e}")
