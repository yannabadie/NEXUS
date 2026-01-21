"""
V9.1 Evolution Commands - /evolve, /evolve-status, /review

These commands manage the evolution system for spawning and selecting
improved agent variants.

Uses EvolutionService for business logic (Service Layer Pattern).
"""

from typing import List
from .registry import Command, CommandContext, CommandResult, CommandStatus, CommandRegistry


def _get_evolution_service(context: CommandContext):
    """Retrieves or creates an EvolutionService instance from the context.

    Args:
        context: The command execution context containing services and configuration.

    Returns:
        EvolutionService: An initialized evolution service.

    Raises:
        RuntimeError: If the EvolutionManager is not available in the context.
    """
    from core.evolution import EvolutionService

    # Try to get cached service from extras
    service = context.extras.get("evolution_service")
    if service:
        return service

    # Get evolution_manager from extras or repl
    evolution_manager = context.extras.get("evolution_manager")
    if not evolution_manager:
        repl = context.extras.get("repl")
        if repl and hasattr(repl, 'evolution_manager'):
            evolution_manager = repl.evolution_manager
        else:
            raise RuntimeError("EvolutionManager not available")

    # Get config
    config = context.config
    if not config and hasattr(context.orchestrator, 'config'):
        config = context.orchestrator.config
    if not config:
        repl = context.extras.get("repl")
        if repl and hasattr(repl, 'config'):
            config = repl.config

    # Get workspace_path and rate_limiter
    workspace_path = context.extras.get("workspace_path")
    rate_limiter = context.extras.get("rate_limiter")

    if not workspace_path and hasattr(evolution_manager, 'workspace_path'):
        workspace_path = evolution_manager.workspace_path
    if not rate_limiter:
        repl = context.extras.get("repl")
        if repl and hasattr(repl, 'rate_limiter'):
            rate_limiter = repl.rate_limiter
        elif hasattr(evolution_manager, 'rate_limiter'):
            rate_limiter = evolution_manager.rate_limiter

    return EvolutionService(
        evolution_manager=evolution_manager,
        console=context.console,
        config=config,
        workspace_path=workspace_path,
        rate_limiter=rate_limiter,
    )


class EvolveCommand(Command):
    """Command to start an evolution cycle to generate child variants.

    This command initiates the process of creating new agent variants based on
    the current best agent, allowing for improvement over time.
    """

    @property
    def name(self) -> str:
        """Return the primary command name.

        Returns:
            str: The command identifier '/evolve'.
        """
        return "/evolve"

    @property
    def aliases(self) -> List[str]:
        """Return list of aliases for this command.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Return the help description for this command.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Start evolution cycle to generate improved agent variants"

    @property
    def usage(self) -> str:
        """Return usage syntax string.

        Returns:
            str: The usage pattern for the command.
        """
        return "/evolve [child_count] (default: 3)"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute evolve command using EvolutionService.

        Args:
            args: Command arguments, typically the number of children to spawn.
            context: The command execution context.

        Returns:
            CommandResult: The result of the command execution.

        Raises:
            Exception: If evolution fails.
        """
        try:
            service = _get_evolution_service(context)
            # Parse child count from args (default 3)
            child_count = int(args) if args.strip().isdigit() else 3
            result = service.evolve(child_count=child_count)

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""  # Service handles its own output
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Evolution failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Evolution failed: {e}"
            )


class EvolveStatusCommand(Command):
    """Command to show current evolution status.

    Displays information about the current generation, active children, and
    the state of the evolution process.
    """

    @property
    def name(self) -> str:
        """Return the primary command name.

        Returns:
            str: The command identifier '/evolve-status'.
        """
        return "/evolve-status"

    @property
    def aliases(self) -> List[str]:
        """Return list of aliases for this command.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return ["/es"]

    @property
    def description(self) -> str:
        """Return the help description for this command.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Show current evolution status and child variants"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute evolve-status command using EvolutionService.

        Args:
            args: Command arguments (unused).
            context: The command execution context.

        Returns:
            CommandResult: The result of the command execution.

        Raises:
            Exception: If retrieving status fails.
        """
        try:
            service = _get_evolution_service(context)
            result = service.status()

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""  # Service handles its own output
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Failed to get status"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Failed to get evolution status: {e}"
            )


class ReviewCommand(Command):
    """Command to review and select from evolved children.

    Allows the user to examine the performance of evolved agents and choose
    which ones to promote or discard.
    """

    @property
    def name(self) -> str:
        """Return the primary command name.

        Returns:
            str: The command identifier '/review'.
        """
        return "/review"

    @property
    def aliases(self) -> List[str]:
        """Return list of aliases for this command.

        Returns:
            List[str]: A list of alternative names for the command.
        """
        return []

    @property
    def description(self) -> str:
        """Return the help description for this command.

        Returns:
            str: A brief description of the command's purpose.
        """
        return "Review evolved children and select best variant"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute review command.

        Note: /review still uses repl.run_review() because it requires
        interactive input (keyboard prompts). Service layer handles
        the promote/archive operations.

        Args:
            args: Command arguments (unused).
            context: The command execution context containing the REPL.

        Returns:
            CommandResult: The result of the command execution.

        Raises:
            Exception: If the review process encounters an error.
        """
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available (interactive review requires REPL)"
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


def register_evolution_commands(registry: CommandRegistry) -> None:
    """Register all evolution commands with a registry.

    Args:
        registry: The command registry to which commands will be added.

    Returns:
        None
    """
    registry.register(EvolveCommand())
    registry.register(EvolveStatusCommand())
    registry.register(ReviewCommand())
