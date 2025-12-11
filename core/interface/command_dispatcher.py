"""
Command Dispatcher for NEXUS V7 REPL.

This module acts as the bridge between the REPL loop and the CommandRegistry.
It initializes the registry and registers all available commands.
"""

from typing import Optional, Dict, Any
from core.interface.commands.registry import (
    CommandRegistry, 
    CommandContext, 
    CommandResult, 
    CommandStatus
)
from core.interface.commands.system import StatusCommand, HelpCommand, QuitCommand

# We will import other command modules here as we create them
# from core.interface.commands.evolution import ...
# from core.interface.commands.swarm import ...

class CommandDispatcher:
    """
    Dispatches commands from the REPL to the appropriate handler.
    """

    def __init__(self, repl_instance):
        """
        Initialize the dispatcher.
        
        Args:
            repl_instance: The InteractiveNexusV7 instance (for context)
        """
        self.registry = CommandRegistry()
        self.repl = repl_instance
        self._register_commands()

    def _register_commands(self):
        """Register all available commands."""
        # System commands
        self.registry.register(StatusCommand())
        self.registry.register(QuitCommand())
        
        # Help command needs registry reference
        help_cmd = HelpCommand()
        help_cmd.set_registry(self.registry)
        self.registry.register(help_cmd)

        # Evolution commands
        from core.interface.commands.evolution import (
            EvolveCommand, EvolveStatusCommand, SpawnCommand, 
            AgentsCommand, ReviewCommand
        )
        self.registry.register(EvolveCommand())
        self.registry.register(EvolveStatusCommand())
        self.registry.register(SpawnCommand())
        self.registry.register(AgentsCommand())
        self.registry.register(ReviewCommand())

        # Swarm commands
        from core.interface.commands.swarm import (
            SwarmCommand, SwarmStatusCommand, SwarmFSMCommand
        )
        self.registry.register(SwarmCommand())
        self.registry.register(SwarmStatusCommand())
        self.registry.register(SwarmFSMCommand())

        # Workspace commands
        from core.interface.commands.workspace import WorkspaceCommand
        self.registry.register(WorkspaceCommand())

        # Telemetry commands
        from core.interface.commands.telemetry import TelemetryCommand, BudgetCommand
        self.registry.register(TelemetryCommand())
        self.registry.register(BudgetCommand())

        # Memory commands
        from core.interface.commands.memory import (
            LearnCommand, ForgetCommand, MemoryStatusCommand, RagCommand
        )
        self.registry.register(LearnCommand())
        self.registry.register(ForgetCommand())
        self.registry.register(MemoryStatusCommand())
        self.registry.register(RagCommand())

        # Misc commands
        from core.interface.commands.misc import (
            ClearCommand, DoctorCommand, ResetCommand, ModeCommand,
            PoolStatsCommand, BootstrapCommand, SpecializeCommand,
            TutorialCommand, QuickstartCommand, ChatCommand
        )
        self.registry.register(ClearCommand())
        self.registry.register(DoctorCommand())
        self.registry.register(ResetCommand())
        self.registry.register(ModeCommand())
        self.registry.register(PoolStatsCommand())
        self.registry.register(BootstrapCommand())
        self.registry.register(SpecializeCommand())
        self.registry.register(TutorialCommand())
        self.registry.register(QuickstartCommand())
        self.registry.register(ChatCommand())

    def dispatch(self, user_input: str) -> bool:
        """
        Dispatch a command string.
        
        Args:
            user_input: The full command string (e.g. "/status detail")
            
        Returns:
            bool: True if session should continue, False if it should exit
        """
        # Create context for this execution
        context = CommandContext(
            orchestrator=self.repl.orchestrator,
            console=self.repl.console,
            config=self.repl.config,
            extras={
                "repl": self.repl,  # Pass REPL for callbacks (legacy support)
                "workspace_path": self.repl.workspace_path
            }
        )

        # Execute
        result = self.registry.dispatch(user_input, context)

        # Handle result
        if result.status == CommandStatus.SUCCESS:
            if result.message:
                self.repl.console.print(result.message)
        elif result.status == CommandStatus.HELP:
            self.repl.console.print(result.message)
        elif result.status == CommandStatus.ERROR:
            self.repl.console.print_error(result.message)
        elif result.status == CommandStatus.NOT_FOUND:
            self.repl.console.print_error(result.message)
        elif result.status == CommandStatus.INVALID_ARGS:
            self.repl.console.print_error(result.message)

        return result.continue_session
