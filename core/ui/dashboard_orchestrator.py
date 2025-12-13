"""
Dashboard Orchestrator - Embedded NEXUS Core for Web Interface

V10: Enables dashboard_server.py to invoke real Gemini/Claude agents
directly from the web interface, without requiring nexus7.py CLI.

Architecture:
    /api/chat (POST) → DashboardOrchestrator.process_message() 
                     → OrchestratorV7.process_turn()
                     → EventBus.publish("AGENT_RESPONSE")
                     → WebSocket broadcast
                     → Frontend AgentExchanges component
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("nexus.dashboard_orchestrator")

# Global singleton instance
_orchestrator_instance: Optional["DashboardOrchestrator"] = None


@dataclass
class DashboardConfig:
    """Minimal config for dashboard orchestrator."""
    workspace_path: Path
    gemini_cli_path: str
    claude_cli_path: str
    gemini_opus_model: str = "gemini-3-pro-preview"
    claude_sonnet_model: str = "claude-sonnet-4-5-20250929"
    timeout: int = 120
    log_level: str = "INFO"
    stagnation_similarity_threshold: float = 0.85
    streaming_enabled: bool = True
    nexus_version: str = "10.0"
    nexus_codename: str = "SINGULARITY"
    ui_verbose: bool = False
    budget_limit: float = 10.0


class DashboardOrchestrator:
    """
    Embedded NEXUS orchestrator for web dashboard.
    
    Provides a simplified interface for the dashboard to invoke
    agents without the full REPL infrastructure.
    """
    
    def __init__(self):
        self._orchestrator = None
        self._initialized = False
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """
        Initialize the orchestrator. Must be called before use.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return True
            
        async with self._lock:
            if self._initialized:
                return True
                
            try:
                # Import here to avoid circular imports
                from core.orchestration_v7 import OrchestratorV7
                
                # Determine paths
                workspace_path = Path("workspace").resolve()
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                # Create config
                config = DashboardConfig(
                    workspace_path=workspace_path,
                    gemini_cli_path=os.getenv("GEMINI_CLI_PATH", "gemini"),
                    claude_cli_path=os.getenv("CLAUDE_CLI_PATH", "claude"),
                )
                
                # Agent info
                gemini_info = {
                    "model": config.gemini_opus_model,
                    "cli_path": config.gemini_cli_path
                }
                
                claude_info = {
                    "model": config.claude_sonnet_model,
                    "cli_path": config.claude_cli_path
                }
                
                # Initialize orchestrator
                logger.info("Initializing Dashboard Orchestrator...")
                self._orchestrator = OrchestratorV7(
                    workspace_path=workspace_path,
                    config=config,
                    gemini_info=gemini_info,
                    claude_info=claude_info
                )
                
                self._initialized = True
                logger.info("Dashboard Orchestrator initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                return False
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message through the NEXUS orchestrator.
        
        Args:
            message: User's chat message
            
        Returns:
            Dict with 'response' and 'agent' keys, or 'error' key if failed.
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return {"error": "Orchestrator not initialized"}
        
        try:
            # Process through orchestrator
            result = await asyncio.to_thread(
                self._orchestrator.process_turn,
                message
            )
            
            # Extract response from result
            if result:
                return {
                    "response": result.get("output", ""),
                    "agent": result.get("agent", "Unknown"),
                    "state": result.get("state", "IDLE"),
                    "finished": result.get("finished", False)
                }
            else:
                return {"error": "No response from orchestrator"}
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"error": str(e)}
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_state(self) -> Dict[str, Any]:
        """Get current orchestrator state."""
        if not self._initialized or not self._orchestrator:
            return {"state": "NOT_INITIALIZED"}
            
        return {
            "state": self._orchestrator.state.value if hasattr(self._orchestrator.state, 'value') else str(self._orchestrator.state),
            "active_agent": self._orchestrator.active_agent,
            "iteration": self._orchestrator.iteration
        }


def get_dashboard_orchestrator() -> DashboardOrchestrator:
    """Get the singleton dashboard orchestrator instance."""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = DashboardOrchestrator()
    
    return _orchestrator_instance
