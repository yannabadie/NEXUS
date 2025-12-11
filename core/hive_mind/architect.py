"""
The Architect - Dynamic Role Negotiation System (V9.0).

Implements "Fluid Dialectic Intelligence" where Gemini and Claude
negotiate roles (LEAD/SUPPORT) based on task context and self-confidence.

This module is the "Brain" of the Hive Mind, deciding WHO does WHAT.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

# Configure logger
logger = logging.getLogger("nexus.architect")

# Try to import UniversalIO for Semantic Analysis
try:
    from core.io.universal_io import UniversalIO
    UNIVERSAL_IO_AVAILABLE = True
except ImportError:
    UNIVERSAL_IO_AVAILABLE = False
    UniversalIO = None

class Role(Enum):
    LEAD = "lead"
    SUPPORT = "support"

@dataclass
class AgentBid:
    """A bid from an agent to take on a specific role."""
    agent_id: str
    confidence: float
    proposed_role: Role
    reasoning: str

class Architect:
    """
    The Architect arbitrates between agents to assign roles dynamically.
    
    V9.0: Uses Semantic Analysis (LLM) via UniversalIO if available,
    falling back to Heuristics if not.
    """

    def __init__(self, config: Any = None):
        self.config = config
        self.logger = logger
        
        # Initialize UniversalIO if available
        self.universal_io = None
        if UNIVERSAL_IO_AVAILABLE and UniversalIO.is_available():
            self.universal_io = UniversalIO(verbose=getattr(config, "log_level", "INFO") == "DEBUG")
        
        # Fast model for negotiation (can be configured)
        self.model = getattr(config, "architect_model", "gemini-2.0-flash-exp") 

    async def negotiate_roles(self, task_description: str) -> Dict[str, Any]:
        """
        Negotiate roles based on task description.
        
        Strategy:
        1. Try Semantic Analysis (LLM) via UniversalIO.
        2. Fallback to Heuristics (Keyword Matching).
        """
        self.logger.info(f"Architect negotiating roles for task: {task_description[:50]}...")

        # 1. Try Semantic Analysis
        if self.universal_io:
            try:
                return await self._negotiate_with_llm(task_description)
            except Exception as e:
                self.logger.warning(f"Semantic negotiation failed: {e}. Falling back to heuristics.")

        # 2. Fallback to Heuristics
        return await self._negotiate_with_heuristics(task_description)

    async def _negotiate_with_llm(self, task: str) -> Dict[str, Any]:
        """
        Use a fast LLM to decide roles.
        """
        prompt = f"""
        You are the Hive Mind Architect. Analyze the following task and decide which agent should lead.

        AGENTS:
        - GEMINI: Best for coding, implementation, fast execution, Python, refactoring, debugging.
        - CLAUDE: Best for architecture, design, complex reasoning, security, documentation, analysis.
        - SPAWN: Create a NEW specialized agent if the task requires deep domain expertise not present in Gemini/Claude (e.g., Rust, Go, Quantum Physics, Legal, Medical).

        TASK:
        {task}

        DECISION CRITERIA:
        - If the task is primarily about WRITING CODE (Python/JS), choose GEMINI.
        - If the task is primarily about DESIGN or ANALYSIS, choose CLAUDE.
        - If the task requires SPECIALIZED KNOWLEDGE (e.g., "Write a Rust kernel module"), choose SPAWN.
        - If unsure, default to GEMINI.

        Return strictly valid JSON:
        {{
            "lead": "gemini" | "claude" | "spawn",
            "support": "claude" | "gemini" | "none",
            "reasoning": "Brief explanation (max 10 words)",
            "spawn_details": {{ "name": "AgentName", "system_prompt": "..." }} (Only if lead is spawn)
        }}
        """

        messages = [{"role": "user", "content": prompt}]
        
        # Use JSON mode if supported by the model/provider, otherwise just parse text
        # Note: UniversalIO.invoke returns a dict with "content"
        response = await self.universal_io.invoke(
            model=self.model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"} 
        )
        
        content = response["content"]
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        decision = json.loads(content)
        
        # Validate keys
        if "lead" not in decision:
            raise ValueError("Missing 'lead' key in LLM response")
            
        result = {
            "lead": decision["lead"].lower(),
            "support": decision.get("support", "none").lower(),
            "reasoning": decision.get("reasoning", "Semantic Analysis")
        }
        
        if result["lead"] == "spawn":
            result["spawn_details"] = decision.get("spawn_details", {})
            
        return result

    async def _negotiate_with_heuristics(self, task_description: str) -> Dict[str, Any]:
        """
        Simulate negotiation using keyword heuristics (Fallback).
        """
        gemini_bid, claude_bid = await asyncio.gather(
            self._get_gemini_bid(task_description),
            self._get_claude_bid(task_description)
        )
        
        return self._arbitrate(gemini_bid, claude_bid)

    async def _get_gemini_bid(self, task: str) -> AgentBid:
        """Simulate Gemini's bid."""
        task_lower = task.lower()
        confidence = 0.5
        role = Role.SUPPORT
        reasoning = "Standard capability"

        if any(k in task_lower for k in ["python", "analysis", "research", "data", "debug", "fix", "script", "code"]):
            confidence = 0.9
            role = Role.LEAD
            reasoning = "I am strong at Python, analysis, and debugging."
        elif "creative" in task_lower or "design" in task_lower:
            confidence = 0.6
            role = Role.SUPPORT
            reasoning = "I can support with technical constraints."

        return AgentBid("gemini", confidence, role, reasoning)

    async def _get_claude_bid(self, task: str) -> AgentBid:
        """Simulate Claude's bid."""
        task_lower = task.lower()
        confidence = 0.5
        role = Role.SUPPORT
        reasoning = "Standard capability"

        if any(k in task_lower for k in ["architecture", "design", "creative", "plan", "complex", "strategy"]):
            confidence = 0.95
            role = Role.LEAD
            reasoning = "I excel at architectural design and creative tasks."
        elif "python" in task_lower:
            confidence = 0.7
            role = Role.SUPPORT
            reasoning = "I can write Python but Gemini is often faster/more precise."

        return AgentBid("claude", confidence, role, reasoning)

    def _arbitrate(self, bid_a: AgentBid, bid_b: AgentBid) -> Dict[str, Any]:
        """Resolve role conflicts."""
        # Logic 1: Mutual Agreement
        if bid_a.proposed_role == Role.LEAD and bid_b.proposed_role == Role.SUPPORT:
            return self._make_decision(bid_a.agent_id, bid_b.agent_id, "Mutual agreement")
        
        if bid_b.proposed_role == Role.LEAD and bid_a.proposed_role == Role.SUPPORT:
            return self._make_decision(bid_b.agent_id, bid_a.agent_id, "Mutual agreement")

        # Logic 2: Both want LEAD -> Higher confidence wins
        if bid_a.proposed_role == Role.LEAD and bid_b.proposed_role == Role.LEAD:
            if bid_a.confidence > bid_b.confidence:
                return self._make_decision(bid_a.agent_id, bid_b.agent_id, 
                    f"{bid_a.agent_id} has higher confidence ({bid_a.confidence:.1f} vs {bid_b.confidence:.1f})")
            elif bid_b.confidence > bid_a.confidence:
                return self._make_decision(bid_b.agent_id, bid_a.agent_id, 
                    f"{bid_b.agent_id} has higher confidence ({bid_b.confidence:.1f} vs {bid_a.confidence:.1f})")
            else:
                return self._make_decision("gemini", "claude", "Confidence tie, defaulting to Gemini")

        # Logic 3: Both want SUPPORT -> Higher confidence forced to LEAD
        if bid_a.proposed_role == Role.SUPPORT and bid_b.proposed_role == Role.SUPPORT:
            if bid_a.confidence > bid_b.confidence:
                return self._make_decision(bid_a.agent_id, bid_b.agent_id, 
                    f"Both wanted SUPPORT, but {bid_a.agent_id} is more confident")
            else:
                return self._make_decision(bid_b.agent_id, bid_a.agent_id, 
                    f"Both wanted SUPPORT, but {bid_b.agent_id} is more confident")

        return self._make_decision("gemini", "claude", "Fallback decision")

    def _make_decision(self, lead: str, support: str, reasoning: str) -> Dict[str, Any]:
        return {
            "lead": lead,
            "support": support,
            "reasoning": reasoning
        }

    def format_decision_log(self, decision: Dict[str, Any]) -> str:
        """Format the decision for CLI display."""
        lead = decision['lead'].upper()
        support = decision['support'].upper()
        reasoning = decision['reasoning']
        
        return (
            f"\n╔══════════════════════════════════════════════════════════════╗\n"
            f"║  🧠 ARCHITECT DECISION                                       ║\n"
            f"╠══════════════════════════════════════════════════════════════╣\n"
            f"║  LEAD AGENT    : {lead:<40}║\n"
            f"║  SUPPORT AGENT : {support:<40}║\n"
            f"║  REASONING     : {reasoning:<40}║\n"
            f"╚══════════════════════════════════════════════════════════════╝\n"
        )
