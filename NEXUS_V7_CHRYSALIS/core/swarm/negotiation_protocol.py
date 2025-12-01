"""
Negotiation Protocol - Sprint 9 Hybrid Swarm Engine

Implements hybrid negotiation where agents debate in natural language
with embedded structured proposals in <negotiate> tags.

Example exchange:
    Gemini: "Pour cette tâche de debugging, je pense que LEAD_SUPPORT serait optimal.

    <negotiate>
    {"proposed_mode": "lead_support", "proposed_lead": "Claude", "confidence": 0.85}
    </negotiate>"

    Claude: "D'accord, je mènerai l'investigation.

    <negotiate>
    {"agrees_with_partner": true, "consensus_reached": true}
    </negotiate>"
"""

import re
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable, Any
from datetime import datetime
from enum import Enum

from .collaboration_modes import CollaborationMode
from .task_analyzer import TaskAnalysis
from .mode_selector import ModeProposal, AgentAssignment


class NegotiationStatus(Enum):
    """Status of negotiation process"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONSENSUS = "consensus"
    TIMEOUT = "timeout"
    FORCED = "forced"  # User forced a mode


@dataclass
class NegotiationProposal:
    """
    Structured proposal extracted from <negotiate> tags.

    Contains the agent's formal position on mode selection.
    """
    proposed_mode: Optional[str] = None
    proposed_lead: Optional[str] = None
    confidence: float = 0.5
    my_role: Optional[str] = None
    justification: Optional[str] = None
    agrees_with_partner: bool = False
    consensus_reached: bool = False
    subtasks: Optional[Dict[str, str]] = None
    counter_proposal: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict) -> "NegotiationProposal":
        """Parse proposal from dictionary"""
        # Validate subtasks is a dict, not a list
        subtasks_raw = data.get("subtasks")
        if isinstance(subtasks_raw, list):
            # Convert list to dict: index -> value or skip malformed entries
            subtasks = {}
            for i, item in enumerate(subtasks_raw):
                if isinstance(item, dict):
                    # Try to extract agent and task from dict
                    agent = item.get("agent", f"agent_{i}")
                    task = item.get("task", str(item))
                    subtasks[agent] = task
                elif isinstance(item, str):
                    subtasks[f"agent_{i}"] = item
        elif isinstance(subtasks_raw, dict):
            subtasks = subtasks_raw
        else:
            subtasks = None

        return cls(
            proposed_mode=data.get("proposed_mode"),
            proposed_lead=data.get("proposed_lead"),
            confidence=data.get("confidence", 0.5),
            my_role=data.get("my_role"),
            justification=data.get("justification"),
            agrees_with_partner=data.get("agrees_with_partner", False),
            consensus_reached=data.get("consensus_reached", False),
            subtasks=subtasks,
            counter_proposal=data.get("counter_proposal")
        )

    def to_dict(self) -> Dict:
        return {
            "proposed_mode": self.proposed_mode,
            "proposed_lead": self.proposed_lead,
            "confidence": self.confidence,
            "my_role": self.my_role,
            "justification": self.justification,
            "agrees_with_partner": self.agrees_with_partner,
            "consensus_reached": self.consensus_reached,
            "subtasks": self.subtasks,
            "counter_proposal": self.counter_proposal
        }


@dataclass
class HybridNegotiationMessage:
    """
    Message combining natural language debate with structured proposal.

    The natural content is for rich discussion,
    the structured proposal is for machine-readable consensus detection.
    """
    sender: str  # "gemini" or "claude"
    natural_content: str
    structured_proposal: Optional[NegotiationProposal] = None
    timestamp: datetime = field(default_factory=datetime.now)
    turn_number: int = 0

    @property
    def agrees_with_partner(self) -> bool:
        if self.structured_proposal:
            return self.structured_proposal.agrees_with_partner
        return False

    @property
    def consensus_reached(self) -> bool:
        if self.structured_proposal:
            return self.structured_proposal.consensus_reached
        return False

    @property
    def proposed_mode(self) -> Optional[CollaborationMode]:
        if self.structured_proposal and self.structured_proposal.proposed_mode:
            try:
                return CollaborationMode.from_string(
                    self.structured_proposal.proposed_mode
                )
            except ValueError:
                return None
        return None

    def to_dict(self) -> Dict:
        return {
            "sender": self.sender,
            "natural_content": self.natural_content,
            "structured_proposal": (
                self.structured_proposal.to_dict()
                if self.structured_proposal else None
            ),
            "timestamp": self.timestamp.isoformat(),
            "turn_number": self.turn_number
        }


@dataclass
class NegotiationResult:
    """
    Result of negotiation process.

    Contains final mode selection and negotiation history.
    """
    status: NegotiationStatus
    selected_mode: CollaborationMode
    agent_assignments: List[AgentAssignment]
    negotiation_history: List[HybridNegotiationMessage]
    total_turns: int
    consensus_confidence: float
    final_subtasks: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict:
        return {
            "status": self.status.value,
            "selected_mode": self.selected_mode.value,
            "agent_assignments": [
                {
                    "agent_id": a.agent_id,
                    "role": a.role,
                    "subtask": a.subtask
                }
                for a in self.agent_assignments
            ],
            "negotiation_history": [m.to_dict() for m in self.negotiation_history],
            "total_turns": self.total_turns,
            "consensus_confidence": round(self.consensus_confidence, 3),
            "final_subtasks": self.final_subtasks
        }


class NegotiationProtocol:
    """
    Manages hybrid negotiation between agents.

    Protocol:
    1. ModeSelector proposes initial mode
    2. Agent 1 (Gemini) reacts/counter-proposes
    3. Agent 2 (Claude) reacts/accepts
    4. Repeat until consensus or max_turns
    5. Fallback to initial proposal if no consensus
    """

    # Regex to extract <negotiate> JSON
    NEGOTIATE_PATTERN = re.compile(
        r'<negotiate>\s*(\{.*?\})\s*</negotiate>',
        re.DOTALL | re.IGNORECASE
    )

    def __init__(
        self,
        max_turns: int = 4,
        consensus_threshold: float = 0.6,
        skip_trivial: bool = True,
        timeout_seconds: Optional[float] = 60.0
    ):
        """
        Initialize NegotiationProtocol.

        Args:
            max_turns: Maximum negotiation turns before timeout
            consensus_threshold: Minimum confidence for consensus
            skip_trivial: Skip negotiation for trivial tasks
            timeout_seconds: Maximum time in seconds for negotiation (None = no limit)
        """
        self.max_turns = max_turns
        self.consensus_threshold = consensus_threshold
        self.skip_trivial = skip_trivial
        self.timeout_seconds = timeout_seconds
        self.negotiation_log: List[Dict] = []

    def run_negotiation(
        self,
        task_analysis: TaskAnalysis,
        initial_proposal: ModeProposal,
        invoke_agent: Callable[[str, str, str], str]
    ) -> NegotiationResult:
        """
        Run full negotiation process.

        Args:
            task_analysis: Analysis of the task
            initial_proposal: Initial mode proposal from ModeSelector
            invoke_agent: Callable(agent_id, task_type, context) -> response

        Returns:
            NegotiationResult with final mode and history
        """
        # Skip negotiation for trivial tasks
        if self.skip_trivial and task_analysis.should_skip_negotiation:
            return NegotiationResult(
                status=NegotiationStatus.FORCED,
                selected_mode=initial_proposal.mode,
                agent_assignments=initial_proposal.agent_assignments,
                negotiation_history=[],
                total_turns=0,
                consensus_confidence=initial_proposal.confidence
            )

        history: List[HybridNegotiationMessage] = []
        current_turn = 0
        current_proposal = initial_proposal
        start_time = time.time()

        # Agents alternate: Gemini starts
        agents = ["gemini", "claude"]

        while current_turn < self.max_turns:
            # Check time-based timeout
            if self.timeout_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed > self.timeout_seconds:
                    # Time limit exceeded - use current best proposal
                    return NegotiationResult(
                        status=NegotiationStatus.TIMEOUT,
                        selected_mode=current_proposal.mode,
                        agent_assignments=current_proposal.agent_assignments,
                        negotiation_history=history,
                        total_turns=current_turn,
                        consensus_confidence=current_proposal.confidence
                    )

            agent_id = agents[current_turn % 2]

            # Build context for agent
            context = self._build_negotiation_context(
                task_analysis,
                current_proposal,
                history,
                agent_id
            )

            # Invoke agent
            response = invoke_agent(agent_id, "negotiation", context)

            # Parse response
            message = self._parse_response(response, agent_id, current_turn)
            history.append(message)

            # Check for consensus
            if message.consensus_reached:
                final_mode = message.proposed_mode or current_proposal.mode
                final_assignments = self._finalize_assignments(
                    final_mode,
                    message,
                    current_proposal.agent_assignments
                )

                return NegotiationResult(
                    status=NegotiationStatus.CONSENSUS,
                    selected_mode=final_mode,
                    agent_assignments=final_assignments,
                    negotiation_history=history,
                    total_turns=current_turn + 1,
                    consensus_confidence=self._calculate_consensus_confidence(
                        history
                    ),
                    final_subtasks=(
                        message.structured_proposal.subtasks
                        if message.structured_proposal else None
                    )
                )

            # Update proposal if counter-proposed
            if message.proposed_mode:
                current_proposal = self._update_proposal(
                    current_proposal,
                    message
                )

            current_turn += 1

        # Timeout: use initial proposal
        return NegotiationResult(
            status=NegotiationStatus.TIMEOUT,
            selected_mode=initial_proposal.mode,
            agent_assignments=initial_proposal.agent_assignments,
            negotiation_history=history,
            total_turns=current_turn,
            consensus_confidence=initial_proposal.confidence
        )

    def _build_negotiation_context(
        self,
        analysis: TaskAnalysis,
        proposal: ModeProposal,
        history: List[HybridNegotiationMessage],
        agent_id: str
    ) -> str:
        """Build context string for agent negotiation turn"""
        lines = [
            "=== SWARM NEGOTIATION ===",
            "",
            f"TASK ANALYSIS:",
            f"- Complexity: {analysis.complexity.name}",
            f"- Domains: {', '.join(d.value for d in analysis.domains)}",
            f"- Gemini fit: {analysis.gemini_fit_score:.0%}",
            f"- Claude fit: {analysis.claude_fit_score:.0%}",
            f"- Recommended lead: {analysis.recommended_lead}",
            "",
            f"INITIAL PROPOSAL: {proposal.mode.value}",
            f"Reasoning: {proposal.reasoning}",
            "",
        ]

        if history:
            lines.append("NEGOTIATION HISTORY:")
            for msg in history[-4:]:  # Last 4 messages
                lines.append(f"[{msg.sender}]: {msg.natural_content[:200]}...")
                if msg.structured_proposal:
                    lines.append(f"  → Proposal: {msg.structured_proposal.to_dict()}")
            lines.append("")

        lines.extend([
            f"YOUR TURN ({agent_id}):",
            "1. Discuss your perspective on the proposed mode",
            "2. Agree, counter-propose, or negotiate subtasks",
            "3. Include <negotiate>JSON</negotiate> with your position",
            "",
            "Available modes: parallel, sequential, lead_support, ping_pong, specialist, red_blue"
        ])

        return "\n".join(lines)

    def _parse_response(
        self,
        response: str,
        sender: str,
        turn_number: int
    ) -> HybridNegotiationMessage:
        """Parse agent response into HybridNegotiationMessage"""
        # Extract natural content (everything outside <negotiate>)
        natural_content = self.NEGOTIATE_PATTERN.sub("", response).strip()

        # Extract structured proposal
        structured_proposal = None
        match = self.NEGOTIATE_PATTERN.search(response)
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                structured_proposal = NegotiationProposal.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                pass  # Invalid JSON, continue without structured proposal

        return HybridNegotiationMessage(
            sender=sender,
            natural_content=natural_content,
            structured_proposal=structured_proposal,
            turn_number=turn_number
        )

    def _update_proposal(
        self,
        current: ModeProposal,
        message: HybridNegotiationMessage
    ) -> ModeProposal:
        """Update proposal based on agent's counter-proposal"""
        if not message.proposed_mode:
            return current

        new_mode = message.proposed_mode
        new_assignments = current.agent_assignments.copy()

        # Update lead if proposed
        if message.structured_proposal and message.structured_proposal.proposed_lead:
            lead_id = message.structured_proposal.proposed_lead.lower()
            for assignment in new_assignments:
                if lead_id in assignment.agent_id.lower():
                    assignment.role = "lead"
                else:
                    assignment.role = "support"

        return ModeProposal(
            mode=new_mode,
            confidence=message.structured_proposal.confidence if message.structured_proposal else 0.6,
            agent_assignments=new_assignments,
            reasoning=f"Counter-proposed by {message.sender}",
            alternatives=current.alternatives
        )

    def _finalize_assignments(
        self,
        mode: CollaborationMode,
        message: HybridNegotiationMessage,
        default_assignments: List[AgentAssignment]
    ) -> List[AgentAssignment]:
        """Finalize agent assignments based on consensus"""
        assignments = []

        subtasks = message.structured_proposal.subtasks if message.structured_proposal else None

        # Defensive check: ensure subtasks is a dict before iterating
        if subtasks and isinstance(subtasks, dict):
            # Use negotiated subtasks
            for agent_id, subtask in subtasks.items():
                role = "equal"
                if message.structured_proposal.proposed_lead:
                    if agent_id.lower() == message.structured_proposal.proposed_lead.lower():
                        role = "lead"
                    else:
                        role = "support"

                assignments.append(AgentAssignment(
                    agent_id=agent_id.lower() + "_primary" if "gemini" in agent_id.lower() else agent_id.lower() + "_opus",
                    role=role,
                    subtask=subtask,
                    confidence=0.8
                ))

        if not assignments:
            # Use default assignments
            assignments = default_assignments

        return assignments

    def _calculate_consensus_confidence(
        self,
        history: List[HybridNegotiationMessage]
    ) -> float:
        """Calculate confidence in consensus based on negotiation"""
        if not history:
            return 0.5

        # Count agreements
        agreements = sum(1 for m in history if m.agrees_with_partner)

        # Average confidence from proposals
        confidences = [
            m.structured_proposal.confidence
            for m in history
            if m.structured_proposal
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5

        # Combine factors
        agreement_factor = agreements / len(history)
        consensus = (agreement_factor * 0.5) + (avg_confidence * 0.5)

        return min(1.0, consensus)

    def force_mode(
        self,
        mode: CollaborationMode,
        task_analysis: TaskAnalysis,
        reason: str = "User forced"
    ) -> NegotiationResult:
        """Force a specific mode without negotiation"""
        from .mode_selector import ModeSelector

        # Generate assignments for forced mode
        selector = ModeSelector()
        proposal = selector.select_mode(task_analysis)

        # Override mode
        return NegotiationResult(
            status=NegotiationStatus.FORCED,
            selected_mode=mode,
            agent_assignments=proposal.agent_assignments,
            negotiation_history=[],
            total_turns=0,
            consensus_confidence=1.0  # Full confidence (user choice)
        )

    def create_negotiation_prompt(
        self,
        agent_id: str,
        task_description: str,
        initial_mode: CollaborationMode
    ) -> str:
        """
        Create a negotiation prompt for an agent.

        Used to inject negotiation instructions into agent context.
        """
        return f"""
You are participating in a SWARM NEGOTIATION to decide how to collaborate on:
"{task_description}"

The ModeSelector suggests: {initial_mode.value}

Your role ({agent_id}):
1. Discuss whether this mode is appropriate
2. Consider your strengths and the task requirements
3. Propose alternatives if you disagree
4. Work toward consensus with your partner

Include your formal position in a <negotiate> block:
<negotiate>
{{
  "proposed_mode": "your_preferred_mode",
  "proposed_lead": "gemini or claude",
  "confidence": 0.0-1.0,
  "my_role": "lead/support/equal",
  "justification": "why this mode",
  "agrees_with_partner": true/false,
  "consensus_reached": true/false if you agree with partner
}}
</negotiate>

Discuss naturally, then include the structured proposal.
"""


def extract_negotiate_json(text: str) -> Optional[Dict]:
    """
    Extract JSON from <negotiate> tags in text.

    Helper function for external use.
    """
    match = NegotiationProtocol.NEGOTIATE_PATTERN.search(text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None
