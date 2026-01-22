"""
V9.1 Miscellaneous Commands - /mode, /reset, /doctor, /telemetry, /budget, /tutorial, /quickstart, /chat, /clear

These commands provide various utility functions for the REPL.

V9.1: TelemetryCommand and BudgetCommand now use Service Layer (TelemetryService, BudgetService).
"""

from typing import List, TYPE_CHECKING
from .registry import Command, CommandContext, CommandResult, CommandStatus

if TYPE_CHECKING:
    from .registry import CommandRegistry


def _get_telemetry_service(context: CommandContext):
    """Get or create TelemetryService from context.

    Retrieves the telemetry service instance from the command context, initializing
    it if necessary using the internal factory function.

    Args:
        context: The command execution context containing services and state.

    Returns:
        TelemetryService: The requested telemetry service instance.
    """
    from core.telemetry import _get_telemetry_service as get_service
    return get_service(context)


def _get_budget_service(context: CommandContext):
    """Get or create BudgetService from context.

    Retrieves the budget service instance from the command context, initializing
    it if necessary using the internal factory function.

    Args:
        context: The command execution context containing services and state.

    Returns:
        BudgetService: The requested budget service instance.
    """
    from core.telemetry import _get_budget_service as get_service
    return get_service(context)


class ClearCommand(Command):
    """Command to clear the console screen.

    This command clears the terminal output buffer to provide a clean slate
    for the user.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/clear".
        """
        return "/clear"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: A list containing "/cls".
        """
        return ["/cls"]

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Clear the console screen"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the clear command.

        Clears the console screen using the console object provided in the context.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the console interface.

        Returns:
            CommandResult: A success result.
        """
        context.console.clear()
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=""
        )


class ModeCommand(Command):
    """Command to change the orchestrator mode.

    Allows the user to switch the operating mode of the orchestrator by updating
    the blackboard state.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/mode".
        """
        return "/mode"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: An empty list as there are no aliases.
        """
        return []

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Change the orchestrator mode"

    @property
    def usage(self) -> str:
        """Get the usage string for the command.

        Returns:
            str: The usage format "/mode <mode_name>".
        """
        return "/mode <mode_name>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the mode command.

        Updates the orchestrator's mode in the blackboard based on the provided argument.

        Args:
            args: The mode name to switch to.
            context: The execution context containing the orchestrator.

        Returns:
            CommandResult: A success result if mode is changed, or error if args are missing.
        """
        if not args.strip():
            return CommandResult(
                status=CommandStatus.INVALID_ARGS,
                message="Usage: /mode <mode_name>"
            )

        context.orchestrator.blackboard["mode"] = args.strip()
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=f"Mode changed to: {args.strip()}"
        )


class ResetCommand(Command):
    """Command to reset the orchestrator to IDLE state.

    Forces the orchestrator back to its initial IDLE state, clearing temporary
    states or tasks.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/reset".
        """
        return "/reset"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: An empty list as there are no aliases.
        """
        return []

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Reset the orchestrator to IDLE state"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the reset command.

        Attempts to reset the orchestrator to its IDLE state.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the orchestrator.

        Returns:
            CommandResult: A success result if reset, or error if an exception occurs.
        """
        try:
            context.orchestrator.reset_to_idle()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message="Orchestrator reset to IDLE"
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Reset failed: {e}"
            )


class DoctorCommand(Command):
    """Command to run system diagnostics.

    Triggers the system doctor routine to check health, connectivity, and configuration.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/doctor".
        """
        return "/doctor"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: A list containing "/diag".
        """
        return ["/diag"]

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Run system diagnostics and check API connectivity"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the doctor command.

        Runs the doctor diagnostics method on the REPL instance.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the REPL instance.

        Returns:
            CommandResult: A success result if diagnostics run, or error if REPL is missing or fails.
        """
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.run_doctor()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Diagnostics failed: {e}"
            )


class TelemetryCommand(Command):
    """Command to manage telemetry settings.

    Provides subcommands to view status, report data, or export telemetry logs.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/telemetry".
        """
        return "/telemetry"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: A list containing "/tel".
        """
        return ["/tel"]

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "View or configure telemetry settings"

    @property
    def usage(self) -> str:
        """Get the usage string for the command.

        Returns:
            str: The usage format "/telemetry [status|report|export] [days]".
        """
        return "/telemetry [status|report|export] [days]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the telemetry command using TelemetryService.

        Delegates the operation to the TelemetryService based on the subcommand provided.

        Args:
            args: The arguments string containing subcommand and options.
            context: The execution context containing services.

        Returns:
            CommandResult: The result of the telemetry operation.
        """
        try:
            service = _get_telemetry_service(context)
            parts = args.strip().split()
            subcommand = parts[0] if parts else "status"

            if subcommand == "status":
                result = service.status()
            elif subcommand == "report":
                days = int(parts[1]) if len(parts) > 1 else 7
                result = service.report(days=days)
            elif subcommand == "export":
                days = int(parts[1]) if len(parts) > 1 else None
                result = service.export(days=days)
            else:
                # Default to status for unknown subcommands
                result = service.status()

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""  # Service handles its own output
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Telemetry command failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Telemetry command failed: {e}"
            )


class BudgetCommand(Command):
    """Command to manage token budget.

    Provides functionality to view status, reset usage, add credits, or view history.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/budget".
        """
        return "/budget"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: An empty list as there are no aliases.
        """
        return []

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "View or set token budget for API calls"

    @property
    def usage(self) -> str:
        """Get the usage string for the command.

        Returns:
            str: The usage format "/budget [status|reset|add <amount>|history]".
        """
        return "/budget [status|reset|add <amount>|history]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the budget command using BudgetService.

        Delegates the operation to the BudgetService based on the subcommand provided.

        Args:
            args: The arguments string containing subcommand and options.
            context: The execution context containing services.

        Returns:
            CommandResult: The result of the budget operation.
        """
        try:
            service = _get_budget_service(context)
            parts = args.strip().split()
            subcommand = parts[0] if parts else "status"

            if subcommand == "status" or not subcommand:
                result = service.status()
            elif subcommand == "reset":
                result = service.reset(confirmed=False)
            elif subcommand == "add":
                if len(parts) < 2:
                    return CommandResult(
                        status=CommandStatus.INVALID_ARGS,
                        message="Usage: /budget add <amount>"
                    )
                try:
                    amount = float(parts[1])
                    result = service.add_credit(amount)
                except ValueError:
                    return CommandResult(
                        status=CommandStatus.INVALID_ARGS,
                        message="Amount must be a number"
                    )
            elif subcommand == "history":
                result = service.history()
            else:
                # Default to status for unknown subcommands
                result = service.status()

            if result.success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=""  # Service handles its own output
                )
            else:
                return CommandResult(
                    status=CommandStatus.ERROR,
                    message=result.error or "Budget command failed"
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Budget command failed: {e}"
            )


class TutorialCommand(Command):
    """Command to run the interactive tutorial.

    Launches the guided tutorial for new users.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/tutorial".
        """
        return "/tutorial"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: A list containing "/tut".
        """
        return ["/tut"]

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Run the interactive NEXUS tutorial"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the tutorial command.

        Initiates the tutorial sequence in the REPL.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the REPL instance.

        Returns:
            CommandResult: A success result if started, or error if REPL is missing or fails.
        """
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.run_tutorial()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Tutorial failed: {e}"
            )


class QuickstartCommand(Command):
    """Command to show the quickstart guide.

    Displays a brief guide to help users get started with the system.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/quickstart".
        """
        return "/quickstart"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: A list containing "/qs".
        """
        return ["/qs"]

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Show the NEXUS quickstart guide"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the quickstart command.

        Shows the quickstart information in the REPL.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the REPL instance.

        Returns:
            CommandResult: A success result if shown, or error if REPL is missing or fails.
        """
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.show_quickstart()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Quickstart failed: {e}"
            )


class ChatCommand(Command):
    """Command to toggle chat mode.

    Switches the interface between command mode and direct conversational AI mode.
    """

    @property
    def name(self) -> str:
        """Get the primary name of the command.

        Returns:
            str: The command name "/chat".
        """
        return "/chat"

    @property
    def aliases(self) -> List[str]:
        """Get the list of aliases for the command.

        Returns:
            List[str]: An empty list as there are no aliases.
        """
        return []

    @property
    def description(self) -> str:
        """Get the description of the command.

        Returns:
            str: A brief description of the command's functionality.
        """
        return "Toggle chat mode for direct AI conversation"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the chat command.

        Toggles the chat mode state in the REPL.

        Args:
            args: The arguments passed to the command (ignored).
            context: The execution context containing the REPL instance.

        Returns:
            CommandResult: A success result if toggled, or error if REPL is missing or fails.
        """
        repl = context.extras.get("repl")
        if not repl:
            return CommandResult(
                status=CommandStatus.ERROR,
                message="REPL instance not available"
            )

        try:
            repl.toggle_chat_mode()
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=""
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.ERROR,
                message=f"Chat toggle failed: {e}"
            )


def register_misc_commands(registry: "CommandRegistry") -> None:
    """Register all miscellaneous commands with a registry.

    Instantiates and registers all command classes defined in this module
    to the provided command registry.

    Args:
        registry: The command registry to register commands with.

    Raises:
        ValueError: If a command with the same name or alias is already registered.
    """
    registry.register(ClearCommand())
    registry.register(ModeCommand())
    registry.register(ResetCommand())
    registry.register(DoctorCommand())
    registry.register(TelemetryCommand())
    registry.register(BudgetCommand())
    registry.register(TutorialCommand())
    registry.register(QuickstartCommand())
    registry.register(ChatCommand())
