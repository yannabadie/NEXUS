import yaml
import os
from typing import Dict, List, Any, Optional
from .bridge import AIBridge
from .logger import NexusLogger

# --- Real Agent Classes (No Mocks) ---

class BaseAgent:
    def __init__(self, name: str, bridge: AIBridge, logger: NexusLogger):
        self.name = name
        self.bridge = bridge
        self.logger = logger

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class GeminiNativeAgent(BaseAgent):
    """
    Agent using Gemini CLI (The Driver).
    Used for massive analysis, reasoning, or planning.
    """
    def __init__(self, name: str, model: str, instructions: str, input_keys: list, output_key: str, bridge: AIBridge, logger: NexusLogger):
        super().__init__(name, bridge, logger)
        self.model = model
        self.instructions = instructions
        self.input_keys = input_keys
        self.output_key = output_key

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.system(f"🤖 ACTIVATING GEMINI AGENT: {self.name} ({self.model})")
        
        # 1. Build Context from State
        context_str = ""
        for key in self.input_keys:
            val = state.get(key, "N/A")
            context_str += f"\n--- {key.upper()} ---\n{val}\n"

        # 2. Construct Prompt
        prompt = f"""
        ROLE: {self.instructions}
        
        CONTEXT:
        {context_str}
        
        OBJECTIVE:
        Perform your role based on the context. Provide the specific output required.
        """

        # 3. Real Execution via Bridge
        response = self.bridge.call_gemini(prompt, model=self.model)
        
        # 4. Update State
        state[self.output_key] = response
        return state

class ClaudeProxyAgent(BaseAgent):
    """
    Agent using Claude CLI (The Worker or The Sage).
    - Model 'sonnet': High-performance coding & tasks (Worker).
    - Model 'opus': Reasoning, architecture, critical decisions (Sage).
    """
    def __init__(self, name: str, model: str, prompt_template: str, input_keys: list, output_key: str, bridge: AIBridge, logger: NexusLogger):
        super().__init__(name, bridge, logger)
        self.model = model # "sonnet" or "opus"
        self.prompt_template = prompt_template
        self.input_keys = input_keys
        self.output_key = output_key

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        role_icon = "🧙‍♂️" if "opus" in self.model.lower() else "👷"
        role_name = "SAGE (Opus)" if "opus" in self.model.lower() else "WORKER (Sonnet)"
        
        self.logger.system(f"{role_icon} ACTIVATING CLAUDE AGENT: {self.name} [{role_name}]")

        # 1. Hydrate Prompt Template
        prompt = self.prompt_template
        for key in self.input_keys:
            val = state.get(key, "")
            # Simple templating {{key}}
            prompt = prompt.replace(f"{{{{{key}}}}}", str(val))

        # 2. Real Execution via Bridge
        # The bridge handles the specific CLI flags for Opus vs Sonnet
        response = self.bridge.call_claude(prompt, model=self.model)

        # 3. Update State
        state[self.output_key] = response
        return state

class SequentialAgent(BaseAgent):
    """
    Orchestrator that runs a list of agents in order.
    Passes the 'state' dictionary from one to the next.
    """
    def __init__(self, name: str, agents: List[BaseAgent], bridge: AIBridge, logger: NexusLogger):
        super().__init__(name, bridge, logger)
        self.agents = agents

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.system(f"🚀 STARTING PIPELINE: {self.name} ({len(self.agents)} steps)")
        
        for i, agent in enumerate(self.agents):
            self.logger.system(f"▶️ STEP {i+1}/{len(self.agents)}: {agent.name}")
            state = agent.run(state)
            
        self.logger.system(f"🏁 PIPELINE FINISHED: {self.name}")
        return state

# --- Loader Logic ---

class ArchitectureLoader:
    def __init__(self, library_path: str = "20_NEXUS/06_Architecture_Library"):
        self.library_path = library_path
        self.logger = NexusLogger()
        self.bridge = AIBridge(self.logger)

    def load(self, arch_path: str) -> BaseAgent:
        """
        Loads a YAML architecture and builds the Agent object graph.
        Supports recursive definitions (sub-agents).
        """
        full_path = os.path.join(self.library_path, arch_path)
        # Handle absolute paths or relative to cwd
        if not os.path.exists(full_path):
            if os.path.exists(arch_path):
                full_path = arch_path
            else:
                raise FileNotFoundError(f"Architecture file not found: {full_path}")

        self.logger.system(f"📂 LOADING ARCHITECTURE: {full_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Root is usually an orchestrator (Sequential), but could be single agent
        root_type = config.get('orchestrator', {}).get('type', 'SequentialAgent')
        
        if root_type == 'SequentialAgent':
            agents = self._load_agent_list(config.get('agents', []))
            return SequentialAgent(
                name=config.get('metadata', {}).get('name', 'Unknown Pipeline'),
                agents=agents,
                bridge=self.bridge,
                logger=self.logger
            )
        else:
            raise ValueError(f"Unsupported root orchestrator type: {root_type}")

    def _load_agent_list(self, agents_conf: List[Dict]) -> List[BaseAgent]:
        loaded_agents = []
        for conf in agents_conf:
            agent_type = conf.get('type')
            
            if agent_type == 'gemini_native':
                loaded_agents.append(GeminiNativeAgent(
                    name=conf.get('id'),
                    model=conf.get('model', 'gemini-2.5-pro'),
                    instructions=conf.get('description'),
                    input_keys=conf.get('input_from_state', []),
                    output_key=conf.get('output_to_state', ['output'])[0],
                    bridge=self.bridge,
                    logger=self.logger
                ))
            
            elif agent_type == 'claude_proxy':
                loaded_agents.append(ClaudeProxyAgent(
                    name=conf.get('agent_id'),
                    model=conf.get('model', 'sonnet'), # Default to Sonnet (Worker)
                    prompt_template=conf.get('prompt_template', ''),
                    input_keys=conf.get('input_from_state', []),
                    output_key=conf.get('output_to_state', ['output'])[0],
                    bridge=self.bridge,
                    logger=self.logger
                ))
                
            elif agent_type == 'sequential':
                # Recursive loading for sub-pipelines
                sub_agents = self._load_agent_list(conf.get('agents', []))
                loaded_agents.append(SequentialAgent(
                    name=conf.get('id', 'Sub-Pipeline'),
                    agents=sub_agents,
                    bridge=self.bridge,
                    logger=self.logger
                ))
                
        return loaded_agents