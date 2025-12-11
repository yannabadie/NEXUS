import sys
import os
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from core.swarm.negotiation_protocol import NegotiationProtocol, NegotiationStatus
from core.swarm.mode_selector import ModeSelector, ModeProposal, AgentAssignment
from core.swarm.task_analyzer import TaskAnalysis, TaskComplexity, TaskDomain
from core.swarm.collaboration_modes import CollaborationMode
from core.swarm.agent_metrics import AgentPool, AgentProfile

def test_swarm_negotiation():
    print("--- Starting Swarm Negotiation Test ---")

    # 1. Setup Mocks
    print("1. Setting up mocks...")
    
    # Mock AgentPool
    agent_pool = MagicMock(spec=AgentPool)
    agent_pool.get_active_agents.return_value = [
        AgentProfile(agent_id="gemini_pro", provider="gemini", model="gemini-pro", capabilities=["reasoning", "coding"]),
        AgentProfile(agent_id="claude_opus", provider="anthropic", model="claude-opus", capabilities=["writing", "coding"])
    ]
    
    # Mock TaskAnalysis
    task_analysis = MagicMock(spec=TaskAnalysis)
    task_analysis.complexity = TaskComplexity.MODERATE
    task_analysis.primary_domain = TaskDomain.CODING
    task_analysis.domains = [TaskDomain.CODING]
    task_analysis.should_skip_negotiation = False
    task_analysis.gemini_fit_score = 0.8
    task_analysis.claude_fit_score = 0.8
    task_analysis.recommended_lead = "gemini"

    # 2. Initialize Components
    print("2. Initializing ModeSelector and NegotiationProtocol...")
    mode_selector = ModeSelector(agent_pool=agent_pool)
    protocol = NegotiationProtocol(max_turns=4)

    # 3. Create Initial Proposal (Simulate ModeSelector output)
    initial_proposal = ModeProposal(
        mode=CollaborationMode.PARALLEL,
        confidence=0.7,
        agent_assignments=[
            AgentAssignment(agent_id="gemini_pro", role="equal", subtask="task_a"),
            AgentAssignment(agent_id="claude_opus", role="equal", subtask="task_b")
        ],
        reasoning="Initial guess"
    )
    print(f"Initial Proposal: {initial_proposal.mode.value}")

    # 4. Define Mock Agent Behavior (The Script)
    # Scenario: ModeSelector proposes PARALLEL. 
    # Gemini counters with LEAD_SUPPORT (Gemini Lead).
    # Claude agrees.
    
    def mock_invoke_agent(agent_id, task_type, context):
        print(f"  -> Invoking agent: {agent_id}")
        
        if agent_id == "gemini":
            # Gemini disagrees and proposes LEAD_SUPPORT
            return """
            I think this task requires a clear lead. PARALLEL might cause conflicts.
            I propose LEAD_SUPPORT with me as lead.
            
            <negotiate>
            {
                "proposed_mode": "lead_support",
                "proposed_lead": "gemini",
                "confidence": 0.9,
                "my_role": "lead",
                "justification": "Complex coding task needs single owner",
                "agrees_with_partner": false,
                "consensus_reached": false,
                "subtasks": {
                    "gemini": "lead_implementation",
                    "claude": "support_review"
                }
            }
            </negotiate>
            """
        elif agent_id == "claude":
            # Claude agrees with Gemini's proposal
            return """
            I agree. LEAD_SUPPORT is better here. I will support you.
            
            <negotiate>
            {
                "proposed_mode": "lead_support",
                "proposed_lead": "gemini",
                "confidence": 0.95,
                "my_role": "support",
                "justification": "Agreed with Gemini",
                "agrees_with_partner": true,
                "consensus_reached": true,
                "subtasks": {
                    "gemini": "lead_implementation",
                    "claude": "support_review"
                }
            }
            </negotiate>
            """
        return ""

    # 5. Run Negotiation
    print("3. Running negotiation...")
    
    # Mock registry
    mock_registry = MagicMock()
    mock_registry.is_gemini.side_effect = lambda x: "gemini" in x.lower()
    
    with patch('core.swarm.negotiation_protocol.get_registry', return_value=mock_registry):
        result = protocol.run_negotiation(
            task_analysis=task_analysis,
            initial_proposal=initial_proposal,
            invoke_agent=mock_invoke_agent
        )

    # 6. Verify Results
    print("4. Verifying results...")
    print(f"  Final Status: {result.status}")
    print(f"  Selected Mode: {result.selected_mode}")
    print(f"  Total Turns: {result.total_turns}")

    assert result.status == NegotiationStatus.CONSENSUS, f"Expected CONSENSUS, got {result.status}"
    assert result.selected_mode == CollaborationMode.LEAD_SUPPORT, f"Expected LEAD_SUPPORT, got {result.selected_mode}"
    
    # Check assignments
    lead_assigned = False
    for assignment in result.agent_assignments:
        if assignment.role == "lead" and "gemini" in assignment.agent_id:
            lead_assigned = True
            print(f"  Verified Lead: {assignment.agent_id}")
            
    assert lead_assigned, "Gemini was not assigned as lead"

    print("\n--- TEST PASSED: Swarm Negotiation (DyLAN & Consensus) ---")

if __name__ == "__main__":
    test_swarm_negotiation()
