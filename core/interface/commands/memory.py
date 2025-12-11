"""
Memory Commands for NEXUS V7.

Handles /learn, /forget, /memory-status, /rag.
"""

from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class LearnCommand(Command):
    """Index file or directory into project memory."""

    @property
    def name(self) -> str:
        return "/learn"

    @property
    def description(self) -> str:
        return "Index file or directory into project memory"

    @property
    def usage(self) -> str:
        return "/learn [path]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_learn_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Learn command failed: {e}")


class ForgetCommand(Command):
    """Remove file or directory from project memory."""

    @property
    def name(self) -> str:
        return "/forget"

    @property
    def description(self) -> str:
        return "Remove file or directory from project memory"

    @property
    def usage(self) -> str:
        return "/forget <path>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_forget_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Forget command failed: {e}")


class MemoryStatusCommand(Command):
    """Show project memory statistics."""

    @property
    def name(self) -> str:
        return "/memory-status"

    @property
    def description(self) -> str:
        return "Show project memory statistics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.show_memory_status()
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Memory status failed: {e}")


class RagCommand(Command):
    """RAG initialization and queries."""

    @property
    def name(self) -> str:
        return "/rag"

    @property
    def description(self) -> str:
        return "RAG initialization and queries"

    @property
    def usage(self) -> str:
        return "/rag [init|clear|query <text>]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_rag_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"RAG command failed: {e}")
