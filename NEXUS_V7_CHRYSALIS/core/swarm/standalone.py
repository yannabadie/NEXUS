"""
Simplified Swarm Engine Entry Point

Allows using the swarm engine without the full NEXUS FSM infrastructure.
"""

from .hybrid_swarm_engine import HybridSwarmEngine
from .agent_metrics import create_default_pool
from ..routing.model_router import ModelRouter

class StandaloneSwarm:
    def __init__(self, config=None):
        self.config = config
        self.agent_pool = create_default_pool(config)
        self.model_router = ModelRouter(config)

        # In a real standalone version, we would need to provide a default invoker
        # that connects to the drivers. For now, we assume the user provides one.
        self.engine = HybridSwarmEngine(
            agent_pool=self.agent_pool,
            model_router=self.model_router,
            config=config,
            invoke_agent=self._default_invoker
        )

    def _default_invoker(self, agent_id, task_type, context):
        # Placeholder for standalone invocation logic
        # In a full decoupling, this would instantiate the BaseDriver subclasses
        return f"[Mock Response from {agent_id}]"

    def process(self, task: str):
        return self.engine.process_task(task)
