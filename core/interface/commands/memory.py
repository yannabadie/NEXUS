"""
V9.1 Memory Commands - /learn, /forget, /memory-status, /rag

These commands manage Project Memory (RAG) for context retrieval.
Uses MemoryService for business logic (Service Layer Pattern).
"""

from typing import List, TYPE_CHECKING
from .registry import Command, CommandContext, CommandResult, CommandStatus

if TYPE_CHECKING:
    from .registry import CommandRegistry


def _get_memory_service(context: CommandContext):
    """Retrieve or initialize a MemoryService instance from the command context.

    This helper function extracts the necessary dependencies (project_memory,
    workspace_path, console) from the provided CommandContext to create a
    MemoryService instance. It attempts to retrieve a cached service from
    extras first.

    Args:
        context (CommandContext): The command execution context containing
            the orchestrator, console, and extra parameters.

    Returns:
        MemoryService: An initialized and configured memory service instance.

    Raises:
        ValueError: If `project_memory` or `workspace_path` cannot be resolved
            from the context.
    """
    from core.memory import MemoryService

    # Try to get cached service from extras
    service = context.extras.get("memory_service")
    if service:
        return service

    # Get project_memory from orchestrator
    project_memory = None
    if hasattr(context.orchestrator, "project_memory"):
        project_memory = context.orchestrator.project_memory

    if not project_memory:
        raise ValueError("Project memory not available")

    # Get workspace_path from extras or orchestrator
    workspace_path = context.extras.get("workspace_path")
    if not workspace_path and hasattr(context.orchestrator, "workspace_path"):
        workspace_path = context.orchestrator.workspace_path

    if not workspace_path:
        # Fallback: try to get from repl if available
        repl = context.extras.get("repl")
        if repl and hasattr(repl, "workspace_path"):
            workspace_path = repl.workspace_path

    if not workspace_path:
        raise ValueError("workspace_path not available in context")

    return MemoryService(
        project_memory=project_memory,
        workspace_path=workspace_path,
        console=context.console,
    )


class LearnCommand(Command):
    """Command to add knowledge to Project Memory.

    This command handles indexing files or directories into the
    Project Memory (RAG) system.

    Attributes:
        name (str): The command name ("/learn").
        aliases (List[str]): List of command aliases.
        description (str): The command description.
        usage (str): The usage syntax.
    """

    @property
    def name(self) -> str:
        """Get the command name.

        Returns:
            str: The primary command name, "/learn".
        """
        return "/learn"

    @property
    def aliases(self) -> List[str]:
        """Get the command aliases.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Get the command description.

        Returns:
            str: A short description of the command's purpose.
        """
        return "Index file or directory into Project Memory (RAG)"

    @property
    def usage(self) -> str:
        """Get the command usage syntax.

        Returns:
            str: The usage string showing arguments.
        """
        return "/learn <path> (e.g., /learn core/)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the learn command using MemoryService.

        Args:
            args (str): The command arguments, expected to be the path to
                the file or directory to learn.
            context (CommandContext): The execution context containing
                dependencies and system state.

        Returns:
            CommandResult: The result of the execution, indicating
                success (knowledge added) or failure.
        """
        try:
            service = _get_memory_service(context)
            result = service.learn(args.strip() if args else "")

            if result.success:
                return CommandResult(status=CommandStatus.SUCCESS, message="")
            else:
                return CommandResult(
                    status=CommandStatus.ERROR, message=result.error or "Learn failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR, message=f"Learn command failed: {e}"
            )


class ForgetCommand(Command):
    """Command to remove knowledge from Project Memory.

    This command handles removing files or directories from the
    Project Memory (RAG) system.

    Attributes:
        name (str): The command name ("/forget").
        aliases (List[str]): List of command aliases.
        description (str): The command description.
        usage (str): The usage syntax.
    """

    @property
    def name(self) -> str:
        """Get the command name.

        Returns:
            str: The primary command name, "/forget".
        """
        return "/forget"

    @property
    def aliases(self) -> List[str]:
        """Get the command aliases.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Get the command description.

        Returns:
            str: A short description of the command's purpose.
        """
        return "Remove file or directory from Project Memory"

    @property
    def usage(self) -> str:
        """Get the command usage syntax.

        Returns:
            str: The usage string showing arguments.
        """
        return "/forget <path>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the forget command using MemoryService.

        Args:
            args (str): The command arguments, expected to be the path to
                the file or directory to forget.
            context (CommandContext): The execution context containing
                dependencies and system state.

        Returns:
            CommandResult: The result of the execution, indicating
                success (knowledge removed) or failure.
        """
        try:
            service = _get_memory_service(context)
            result = service.forget(args.strip() if args else "")

            if result.success:
                return CommandResult(status=CommandStatus.SUCCESS, message="")
            else:
                return CommandResult(
                    status=CommandStatus.ERROR, message=result.error or "Forget failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR, message=f"Forget command failed: {e}"
            )


class MemoryStatusCommand(Command):
    """Command to show Project Memory status.

    This command displays current statistics and status of the
    Project Memory (RAG) system.

    Attributes:
        name (str): The command name ("/memory-status").
        aliases (List[str]): List of command aliases.
        description (str): The command description.
    """

    @property
    def name(self) -> str:
        """Get the command name.

        Returns:
            str: The primary command name, "/memory-status".
        """
        return "/memory-status"

    @property
    def aliases(self) -> List[str]:
        """Get the command aliases.

        Returns:
            List[str]: A list of alternative names like "/ms".
        """
        return ["/ms"]

    @property
    def description(self) -> str:
        """Get the command description.

        Returns:
            str: A short description of the command's purpose.
        """
        return "Show Project Memory (RAG) status and statistics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the memory-status command using MemoryService.

        Args:
            args (str): Command arguments (unused).
            context (CommandContext): The execution context containing
                dependencies.

        Returns:
            CommandResult: The result of the execution, indicating
                success (status displayed) or failure.
        """
        try:
            service = _get_memory_service(context)
            service.get_status()
            return CommandResult(status=CommandStatus.SUCCESS, message="")
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR, message=f"Failed to get memory status: {e}"
            )


class RagCommand(Command):
    """Command for RAG operations in Project Memory.

    This command handles various RAG operations including initialization,
    clearing memory, and querying the memory.

    Attributes:
        name (str): The command name ("/rag").
        aliases (List[str]): List of command aliases.
        description (str): The command description.
        usage (str): The usage syntax.
    """

    @property
    def name(self) -> str:
        """Gets the command name.

        Returns:
            str: The primary command name "/rag".
        """
        return "/rag"

    @property
    def aliases(self) -> List[str]:
        """Gets the command aliases.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Gets the command description.

        Returns:
            str: A short description of the command's purpose.
        """
        return "RAG operations: init, clear, query"

    @property
    def usage(self) -> str:
        """Gets the command usage syntax.

        Returns:
            str: The usage string showing arguments.
        """
        return "/rag <init|clear|query <text>>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Executes the rag command using MemoryService.

        Args:
            args (str): The arguments for the RAG command (subcommand + args).
            context (CommandContext): The execution context containing
                dependencies.

        Returns:
            CommandResult: The result of the execution, indicating
                success or failure.
        """
        try:
            service = _get_memory_service(context)
            service.handle_rag_command(args.strip() if args else "")
            return CommandResult(status=CommandStatus.SUCCESS, message="")
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR, message=f"RAG command failed: {e}"
            )


def register_memory_commands(registry: "CommandRegistry") -> None:
    """Registers all memory commands with the provided registry.

    Args:
        registry (CommandRegistry): The command registry instance to register
            the memory commands with.
    """
    registry.register(LearnCommand())
    registry.register(ForgetCommand())
    registry.register(MemoryStatusCommand())
    registry.register(RagCommand())
