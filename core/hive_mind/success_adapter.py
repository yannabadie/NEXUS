"""
NEXUS V8.2.0 - HiveMind Success Adapter

Adapter to make HiveMind results compatible with SuccessMemory.
Bridges the gap between HiveMindResult and SuccessMemory.record_success().

The SuccessMemory uses duck typing, expecting objects with specific properties:
- analysis: raw_input, complexity, domains, primary_domain
- result: selected_mode/mode, status, total_time_seconds, execution_result

This module provides pseudo-dataclasses that satisfy those interfaces.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class PseudoExecutionResult:
    """Pseudo ExecutionResult for SuccessMemory compatibility.

    Attributes:
        total_rounds: Total number of execution rounds (default: 1).
        agent_outputs: List of pseudo-objects with 'agent_id' and 'status' attributes.
    """
    total_rounds: int = 1
    agent_outputs: Any = field(default_factory=list)

    def __post_init__(self):
        """Initializes default values for agent outputs if they are missing.

        Ensures that agent_outputs is populated with pseudo-objects for 'gemini' and 'claude'
        if no outputs are provided.
        """
        if not self.agent_outputs:
            # Create pseudo agent outputs
            self.agent_outputs = [
                type('AgentOutput', (), {'agent_id': 'gemini', 'status': 'success'})(),
                type('AgentOutput', (), {'agent_id': 'claude', 'status': 'success'})()
            ]


@dataclass
class HiveMindAnalysisAdapter:
    """Pseudo-TaskAnalysis for HiveMind -> SuccessMemory compatibility.

    Adapts HiveMind input data to match the structure expected by SuccessMemory.

    Attributes:
        raw_input: The original task description or input text.
        complexity: Pseudo-enum object with a 'name' attribute.
        domains: List of pseudo-enum objects with a 'value' attribute.
        primary_domain: Single pseudo-enum object with a 'value' attribute.
    """
    raw_input: str
    complexity: Any = None
    domains: Any = field(default_factory=lambda: ["hive_mind"])
    primary_domain: Any = "hive_mind"

    def __post_init__(self):
        """Initializes complexity, domains, and primary_domain objects.

        Converts string inputs for complexity and domains into pseudo-objects with
        required attributes for SuccessMemory compatibility.
        """
        # Create pseudo-complexity enum if not provided
        if self.complexity is None:
            self.complexity = type('Complexity', (), {'name': 'MODERATE', 'value': 3})()

        # Convert string domains to pseudo-enums with .value
        if self.domains and isinstance(self.domains[0], str):
            self.domains = [
                type('Domain', (), {'value': d, 'name': d.upper()})()
                for d in self.domains
            ]

        # Convert primary_domain to pseudo-enum
        if isinstance(self.primary_domain, str):
            self.primary_domain = type('Domain', (), {
                'value': self.primary_domain,
                'name': self.primary_domain.upper()
            })()


@dataclass
class HiveMindResultAdapter:
    """Pseudo-SwarmResult for HiveMind -> SuccessMemory compatibility.

    Adapts HiveMind execution results to match the structure expected by SuccessMemory.

    Attributes:
        selected_mode: The collaboration mode used (default: "hive_mind").
        status: Execution status string (e.g., "completed").
        total_time_seconds: Total duration of the execution in seconds.
        execution_result: Object containing detailed execution stats.
        agent_outputs: List of agent output objects (fallback if execution_result missing).
        total_rounds: Number of phases/rounds in the HiveMind process (default: 7).
    """
    selected_mode: str = "hive_mind"
    status: str = "completed"
    total_time_seconds: float = 0.0
    execution_result: Any = None
    agent_outputs: Any = field(default_factory=list)
    total_rounds: int = 7  # HiveMind has 7 phases

    def __post_init__(self):
        """Initializes execution result and agent outputs.

        Creates a PseudoExecutionResult if execution_result is missing, and ensures
        agent_outputs serves as a fallback or is derived from execution_result.
        """
        # Create pseudo execution_result if not provided
        if self.execution_result is None:
            self.execution_result = PseudoExecutionResult(
                total_rounds=self.total_rounds,
                agent_outputs=self.agent_outputs or []
            )

        # Ensure agent_outputs has fallback
        if not self.agent_outputs:
            self.agent_outputs = self.execution_result.agent_outputs

    @property
    def mode(self):
        """Alias for selected_mode (SuccessMemory checks both).

        Returns:
            str: The selected mode.
        """
        return self.selected_mode


@dataclass
class SwarmDelegationAnalysisAdapter:
    """V8.3.2: Adapter for SwarmBridge delegation -> SuccessMemory.

    Records Swarm delegations so the system learns which modes work best.

    Attributes:
        raw_input: The delegated task description.
        complexity: Object representing task complexity.
        domains: List of domain objects.
        primary_domain: Primary domain object.
        mode_used: The collaboration mode string used for the delegation.
    """
    raw_input: str
    complexity: Any = None
    domains: Any = field(default_factory=lambda: ["swarm_delegation"])
    primary_domain: Any = "swarm_delegation"
    mode_used: str = ""

    def __post_init__(self):
        """Initializes complexity, domains, and primary_domain objects.

        Converts string inputs for complexity and domains into pseudo-objects with
        required attributes for SuccessMemory compatibility.
        """
        if self.complexity is None:
            self.complexity = type('Complexity', (), {'name': 'MODERATE', 'value': 3})()
        if self.domains and isinstance(self.domains[0], str):
            self.domains = [
                type('Domain', (), {'value': d, 'name': d.upper()})()
                for d in self.domains
            ]
        if isinstance(self.primary_domain, str):
            self.primary_domain = type('Domain', (), {
                'value': self.primary_domain,
                'name': self.primary_domain.upper()
            })()


@dataclass
class SwarmDelegationResultAdapter:
    """V8.3.2: Adapter for SwarmBridge delegation result -> SuccessMemory.

    Attributes:
        selected_mode: The collaboration mode used (default: "specialist").
        status: Execution status string ("completed" or "failed").
        total_time_seconds: Total duration of the delegation in seconds.
        execution_result: Object containing execution details.
        agent_outputs: List of agent output objects.
        total_rounds: Total number of rounds including fallbacks (default: 1).
        fallback_count: Number of times the system fell back to another mode.
    """
    selected_mode: str = "specialist"
    status: str = "completed"
    total_time_seconds: float = 0.0
    execution_result: Any = None
    agent_outputs: Any = field(default_factory=list)
    total_rounds: int = 1
    fallback_count: int = 0

    def __post_init__(self):
        """Initializes execution result and agent outputs.

        Ensures execution_result exists (creating a PseudoExecutionResult if needed)
        and synchronizes agent_outputs with the execution result.
        """
        if self.execution_result is None:
            self.execution_result = PseudoExecutionResult(
                total_rounds=self.total_rounds,
                agent_outputs=self.agent_outputs or []
            )
        if not self.agent_outputs:
            self.agent_outputs = self.execution_result.agent_outputs

    @property
    def mode(self):
        """Returns the selected mode.

        Returns:
            str: The selected collaboration mode.
        """
        return self.selected_mode


def create_swarm_delegation_adapters(
    task: str,
    mode_used: str,
    duration: float,
    success: bool,
    fallback_count: int = 0,
    agents_used: Any = None
) -> tuple:
    """
    V8.3.2: Create adapters for SwarmBridge delegation.

    Args:
        task: The delegated task description
        mode_used: The collaboration mode that was used
        duration: Execution time in seconds
        success: Whether delegation succeeded
        fallback_count: Number of fallbacks used
        agents_used: List of agent IDs involved

    Returns:
        Tuple of (SwarmDelegationAnalysisAdapter, SwarmDelegationResultAdapter)
    """
    agents_used = agents_used or ["gemini", "claude"]

    analysis = SwarmDelegationAnalysisAdapter(
        raw_input=task,
        domains=["swarm_delegation", mode_used],
        mode_used=mode_used
    )

    result = SwarmDelegationResultAdapter(
        selected_mode=mode_used,
        status="completed" if success else "failed",
        total_time_seconds=duration,
        total_rounds=1 + fallback_count,
        fallback_count=fallback_count,
        agent_outputs=[
            type('AgentOutput', (), {'agent_id': aid, 'status': 'success'})()
            for aid in agents_used
        ]
    )

    return analysis, result


def create_hive_mind_adapters(
    task: str,
    duration: float,
    success: bool,
    phases_completed: int = 7,
    agents_used: Any = None
) -> tuple:
    """
    Convenience function to create both adapters.

    Args:
        task: Original task description
        duration: Total execution time in seconds
        success: Whether task succeeded
        phases_completed: Number of phases completed (default 7)
        agents_used: List of agent IDs used

    Returns:
        Tuple of (HiveMindAnalysisAdapter, HiveMindResultAdapter)
    """
    agents_used = agents_used or ["gemini", "claude"]

    analysis = HiveMindAnalysisAdapter(
        raw_input=task,
        domains=["hive_mind", "multi_agent"]
    )

    result = HiveMindResultAdapter(
        selected_mode="hive_mind",
        status="completed" if success else "failed",
        total_time_seconds=duration,
        total_rounds=phases_completed,
        agent_outputs=[
            type('AgentOutput', (), {'agent_id': aid, 'status': 'success'})()
            for aid in agents_used
        ]
    )

    return analysis, result
