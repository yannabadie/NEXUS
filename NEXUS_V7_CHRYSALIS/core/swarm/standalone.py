"""
Simplified Swarm Engine Entry Point

Allows using the swarm engine without the full NEXUS FSM infrastructure.
"""
from pathlib import Path
from .hybrid_swarm_engine import HybridSwarmEngine
from .agent_metrics import create_default_pool
from ..routing.model_router import ModelRouter
from ..drivers.gemini_driver_v7 import GeminiDriverV7
from ..drivers.claude_driver_hybrid import ClaudeDriverHybrid

class StandaloneSwarm:
    def __init__(self, config):
        self.config = config
        self.agent_pool = create_default_pool(config)
        self.model_router = ModelRouter(config)
        self.workspace_path = Path(".").resolve() # Default to current dir

        # Initialize Drivers
        self.gemini_driver = GeminiDriverV7(config, self.workspace_path)
        self.claude_driver = ClaudeDriverHybrid(config, self.workspace_path)

        self.engine = HybridSwarmEngine(
            agent_pool=self.agent_pool,
            model_router=self.model_router,
            config=config,
            invoke_agent=self._real_invoker
        )

    def _real_invoker(self, agent_id, task_type, context):
        """Invoke the real drivers."""
        try:
            if "claude" in agent_id.lower():
                # Task aware routing (simplified for standalone)
                # If "negotiation", use Opus (smart). If "execution", use Sonnet (fast).
                # But ClaudeDriverHybrid handles model selection or defaults.
                # We can enforce it here if config allows.
                response = self.claude_driver.invoke(context)
            else:
                response = self.gemini_driver.invoke(context)

            # Unpack response
            if isinstance(response, dict):
                content = response.get("content", "")
                # If error in status, prefix it
                if response.get("status") == "error":
                     return f"Error: {content}"
                return content
            return str(response)

        except Exception as e:
            return f"Error invoking {agent_id}: {str(e)}"

    def process(self, task: str):
        return self.engine.process_task(task)
