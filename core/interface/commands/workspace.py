"""
V9 Workspace Commands - /bootstrap, /specialize, /workspace

These commands manage workspace configuration and project specialization.
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus


class BootstrapCommand(Command):
    """Bootstrap a new project with NEXUS.md."""

    @property
    def name(self) -> str:
        return "/bootstrap"

    @property
    def aliases(self) -> List[str]:
        return ["/bs"]

    @property
    def description(self) -> str:
        return "Generate NEXUS.md for a project directory"

    @property
    def usage(self) -> str:
        return "/bootstrap [path] (default: current directory)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute bootstrap command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.run_bootstrap(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Bootstrap failed: {e}"
            )


class SpecializeCommand(Command):
    """Create a specialized NEXUS spinoff."""

    @property
    def name(self) -> str:
        return "/specialize"

    @property
    def aliases(self) -> List[str]:
        return ["/spec"]

    @property
    def description(self) -> str:
        return "Create a specialized NEXUS spinoff for a specific mission"

    @property
    def usage(self) -> str:
        return "/specialize <mission_description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute specialize command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /specialize <mission_description>"
            )

        try:
            repl.run_specialization(mission=args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Specialization failed: {e}"
            )


class WorkspaceCommand(Command):
    """Manage workspace settings."""

    @property
    def name(self) -> str:
        return "/workspace"

    @property
    def aliases(self) -> List[str]:
        return ["/ws"]

    @property
    def description(self) -> str:
        return "Manage workspace settings (show, set, info)"

    @property
    def usage(self) -> str:
        return "/workspace [show|set <path>|info]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute workspace command."""
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.handle_workspace_command(args)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Workspace command failed: {e}"
            )


def register_workspace_commands(registry: "CommandRegistry") -> None:
    """Register all workspace commands with a registry."""
    registry.register(BootstrapCommand())
    registry.register(SpecializeCommand())
    registry.register(WorkspaceCommand())
