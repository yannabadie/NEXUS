"""
V9 Evolution Commands - /evolve, /evolve-status, /review

These commands manage the evolution system for spawning and selecting
improved agent variants.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class EvolveCommand(Command):
    """Start an evolution cycle to generate child variants."""

    @property
    def name(self) -> str:
        return "/evolve"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Start evolution cycle to generate improved agent variants"

    @property
    def usage(self) -> str:
        return "/evolve [child_count] (default: 3)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute evolve command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            # Parse child count from args (default 3)
            child_count = int(args) if args.strip().isdigit() else 3
            repl.run_evolve(child_count=child_count)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""  # Method handles its own output
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Evolution failed: {e}"
            )


class EvolveStatusCommand(Command):
    """Show current evolution status."""

    @property
    def name(self) -> str:
        return "/evolve-status"

    @property
    def aliases(self) -> List[str]:
        return ["/es"]

    @property
    def description(self) -> str:
        return "Show current evolution status and child variants"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute evolve-status command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.show_evolve_status()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get evolution status: {e}"
            )


class ReviewCommand(Command):
    """Review and select from evolved children."""

    @property
    def name(self) -> str:
        return "/review"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Review evolved children and select best variant"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute review command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.run_review()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Review failed: {e}"
            )


def register_evolution_commands(registry: "CommandRegistry") -> None:
    """Register all evolution commands with a registry."""
    registry.register(EvolveCommand())
    registry.register(EvolveStatusCommand())
    registry.register(ReviewCommand())
