"""
Workspace Commands for NEXUS V7.

Handles /workspace.
"""

from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class WorkspaceCommand(Command):
    """Manage workspaces."""

    @property
    def name(self) -> str:
        return "/workspace"

    @property
    def description(self) -> str:
        return "Manage workspaces (list, new, switch)"

    @property
    def usage(self) -> str:
        return "/workspace [new|list|switch] [args]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.handle_workspace_command(args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Workspace command failed: {e}")
