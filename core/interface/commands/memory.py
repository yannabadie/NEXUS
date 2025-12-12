"""
V9 Memory Commands - /learn, /forget, /memory-status, /rag

These commands manage Project Memory (RAG) for context retrieval.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class LearnCommand(Command):
    """Add knowledge to Project Memory."""

    @property
    def name(self) -> str:
        return "/learn"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Add knowledge chunk to Project Memory (RAG)"

    @property
    def usage(self) -> str:
        return "/learn <knowledge text>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute learn command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.handle_learn_command(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Learn command failed: {e}"
            )


class ForgetCommand(Command):
    """Remove knowledge from Project Memory."""

    @property
    def name(self) -> str:
        return "/forget"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Remove knowledge from Project Memory"

    @property
    def usage(self) -> str:
        return "/forget <query to match>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute forget command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.handle_forget_command(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Forget command failed: {e}"
            )


class MemoryStatusCommand(Command):
    """Show Project Memory status."""

    @property
    def name(self) -> str:
        return "/memory-status"

    @property
    def aliases(self) -> List[str]:
        return ["/ms"]

    @property
    def description(self) -> str:
        return "Show Project Memory (RAG) status and statistics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute memory-status command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.show_memory_status()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get memory status: {e}"
            )


class RagCommand(Command):
    """Query Project Memory (RAG)."""

    @property
    def name(self) -> str:
        return "/rag"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "Query Project Memory for relevant context"

    @property
    def usage(self) -> str:
        return "/rag <query>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute rag command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.handle_rag_command(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"RAG query failed: {e}"
            )


def register_memory_commands(registry: "CommandRegistry") -> None:
    """Register all memory commands with a registry."""
    registry.register(LearnCommand())
    registry.register(ForgetCommand())
    registry.register(MemoryStatusCommand())
    registry.register(RagCommand())
