"""
Task Analyzer - Sprint 9 Hybrid Swarm Engine

Analyzes user input to determine:
- Task complexity (TRIVIAL to EXPERT)
- Task domains (CODING, RESEARCH, etc.)
- Agent fit scores (Gemini vs Claude)
- Requirements (web, code execution, deep reasoning)

Used by ModeSelector to choose the optimal collaboration mode.
"""

import re
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import List, Dict, Optional, Tuple


class TaskComplexity(IntEnum):
    """Task complexity levels (1-5)"""
    TRIVIAL = 1   # Skip negotiation, direct execution
    SIMPLE = 2    # Basic task, minimal coordination
    MODERATE = 3  # Standard multi-agent task
    COMPLEX = 4   # Requires careful coordination
    EXPERT = 5    # Requires RED_BLUE or specialist


class TaskDomain(Enum):
    """Task domain categories"""
    CODING = "coding"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    DEBUGGING = "debugging"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    WEB_INTERACTION = "web_interaction"


# Keywords that indicate task domains
DOMAIN_KEYWORDS: Dict[TaskDomain, List[str]] = {
    TaskDomain.CODING: [
        "code", "implement", "function", "class", "method", "script",
        "python", "javascript", "typescript", "rust", "go", "program",
        "create file", "write code", "develop", "build"
    ],
    TaskDomain.RESEARCH: [
        "search", "find", "look up", "research", "investigate",
        "what is", "how does", "why", "compare", "difference between",
        "latest", "recent", "news", "documentation"
    ],
    TaskDomain.ANALYSIS: [
        "analyze", "examine", "review", "understand", "explain",
        "investigate", "study", "evaluate", "assess", "audit"
    ],
    TaskDomain.CREATIVE: [
        "brainstorm", "idea", "creative", "design", "propose",
        "suggest", "imagine", "innovate", "improve", "enhance"
    ],
    TaskDomain.DEBUGGING: [
        "debug", "fix", "bug", "error", "issue", "problem",
        "crash", "exception", "traceback", "broken", "not working"
    ],
    TaskDomain.SECURITY: [
        "security", "vulnerability", "exploit", "attack",
        "protect", "secure", "authentication", "authorization",
        "injection", "xss", "csrf", "penetration"
    ],
    TaskDomain.DOCUMENTATION: [
        "document", "readme", "guide", "tutorial", "explain how",
        "write docs", "api reference", "changelog"
    ],
    TaskDomain.TESTING: [
        "test", "pytest", "unittest", "coverage", "mock",
        "assert", "verify", "validate", "qa"
    ],
    TaskDomain.ARCHITECTURE: [
        "architecture", "design pattern", "structure", "system design",
        "scalability", "refactor", "reorganize", "modular"
    ],
    TaskDomain.WEB_INTERACTION: [
        "web", "url", "fetch", "api", "http", "request",
        "scrape", "download", "upload", "endpoint"
    ]
}

# Agent strengths by domain (Gemini 3 Pro vs Claude Opus 4.5)
AGENT_DOMAIN_STRENGTHS: Dict[str, Dict[TaskDomain, float]] = {
    "gemini": {
        TaskDomain.RESEARCH: 0.95,        # Grounding, web search
        TaskDomain.WEB_INTERACTION: 0.90, # Terminal-Bench leader
        TaskDomain.ANALYSIS: 0.85,        # Long-horizon planning
        TaskDomain.DOCUMENTATION: 0.75,
        TaskDomain.CREATIVE: 0.70,
        TaskDomain.CODING: 0.70,
        TaskDomain.TESTING: 0.65,
        TaskDomain.DEBUGGING: 0.60,
        TaskDomain.ARCHITECTURE: 0.60,
        TaskDomain.SECURITY: 0.65,
    },
    "claude": {
        TaskDomain.CODING: 0.95,          # SWE-bench 80.9%
        TaskDomain.DEBUGGING: 0.90,       # Sustained autonomy
        TaskDomain.ARCHITECTURE: 0.90,    # Complex reasoning
        TaskDomain.SECURITY: 0.85,        # Red team expertise
        TaskDomain.CREATIVE: 0.85,        # Creativity
        TaskDomain.ANALYSIS: 0.80,
        TaskDomain.TESTING: 0.80,
        TaskDomain.DOCUMENTATION: 0.75,
        TaskDomain.RESEARCH: 0.60,        # No native web search
        TaskDomain.WEB_INTERACTION: 0.50,
    }
}

# V7.5 HIVE MIND: Patterns for trivial conversational inputs (greetings, etc.)
# These inputs should NOT trigger multi-agent collaboration
CONVERSATIONAL_TRIVIAL_PATTERNS = [
    # Greetings (FR/EN/ES/DE)
    r'^(hello|hi|hey|bonjour|salut|coucou|hola|hallo|guten tag)( there| all| everyone| team)?[\s!?.]*$',
    r'^(bonsoir|good morning|good evening|good night)[\s!?.]*$',
    # Farewells
    r'^(bye|goodbye|au revoir|ciao|adieu|à bientôt|a\+)[\s!?.]*$',
    # Acknowledgments
    r'^(ok|okay|d\'accord|oui|yes|non|no|merci|thanks|thank you|thx|ty)[\s!?.]*$',
    r'^(parfait|perfect|great|cool|nice|super|génial)[\s!?.]*$',
    r'^(compris|understood|got it|roger)[\s!?.]*$',
    # Simple questions about the assistant
    r'^(ça va\??|how are you\??|comment vas-tu\??|tu vas bien\??)[\s!?.]*$',
    r'^(qui es-tu\??|who are you\??|what are you\??)[\s!?.]*$',
    # Testing/probing
    r'^(test|testing|1234?|ping|pong)[\s!?.]*$',
    # Continuation prompts
    r'^(continue|continues|go on|vas-y|go ahead)[\s!?.]*$',
    # Empty or whitespace-only (after strip)
    r'^\s*$',
]

# Keywords that increase complexity
COMPLEXITY_INDICATORS: Dict[str, int] = {
    # High complexity (+2)
    "security": 2, "vulnerability": 2, "architecture": 2,
    "refactor entire": 2, "redesign": 2, "migrate": 2,
    "critical": 2, "production": 2, "scalability": 2,

    # Medium complexity (+1)
    "implement": 1, "debug": 1, "analyze": 1,
    "integrate": 1, "optimize": 1, "test coverage": 1,
    "multiple files": 1, "across": 1, "complex": 1,

    # Low complexity (-1)
    "simple": -1, "quick": -1, "small": -1,
    "just": -1, "only": -1, "trivial": -1,
}


@dataclass
class TaskAnalysis:
    """
    Complete analysis of a user task.

    Contains all information needed for mode selection and negotiation.
    """
    # Core analysis
    complexity: TaskComplexity
    domains: List[TaskDomain]
    primary_domain: TaskDomain

    # Requirements
    requires_web: bool = False
    requires_code_execution: bool = False
    requires_deep_reasoning: bool = False
    requires_iteration: bool = False

    # Agent fit scores (0.0-1.0)
    gemini_fit_score: float = 0.5
    claude_fit_score: float = 0.5

    # Raw input for reference
    raw_input: str = ""

    # Confidence in analysis (0.0-1.0)
    confidence: float = 0.5

    # Detected keywords
    detected_keywords: List[str] = field(default_factory=list)

    @property
    def recommended_lead(self) -> str:
        """Recommend lead agent based on fit scores"""
        if self.gemini_fit_score > self.claude_fit_score + 0.1:
            return "gemini"
        elif self.claude_fit_score > self.gemini_fit_score + 0.1:
            return "claude"
        return "equal"  # No clear leader

    @property
    def should_skip_negotiation(self) -> bool:
        """Whether task is too trivial for negotiation"""
        return self.complexity == TaskComplexity.TRIVIAL

    @property
    def needs_adversarial_mode(self) -> bool:
        """Whether task should use RED_BLUE mode"""
        return (
            self.complexity == TaskComplexity.EXPERT
            or TaskDomain.SECURITY in self.domains
        )

    def to_dict(self) -> Dict:
        return {
            "complexity": self.complexity.name,
            "complexity_value": self.complexity.value,
            "domains": [d.value for d in self.domains],
            "primary_domain": self.primary_domain.value,
            "requires_web": self.requires_web,
            "requires_code_execution": self.requires_code_execution,
            "requires_deep_reasoning": self.requires_deep_reasoning,
            "requires_iteration": self.requires_iteration,
            "gemini_fit_score": round(self.gemini_fit_score, 3),
            "claude_fit_score": round(self.claude_fit_score, 3),
            "recommended_lead": self.recommended_lead,
            "should_skip_negotiation": self.should_skip_negotiation,
            "needs_adversarial_mode": self.needs_adversarial_mode,
            "confidence": round(self.confidence, 3),
            "detected_keywords": self.detected_keywords
        }


class TaskAnalyzer:
    """
    Analyzes user input to determine task characteristics.

    Uses keyword matching and heuristics to classify tasks
    for optimal mode selection.
    """

    def __init__(self):
        self._domain_patterns = self._compile_patterns()
        self._trivial_patterns = self._compile_trivial_patterns()

    def _compile_trivial_patterns(self) -> list:
        """Compile regex patterns for trivial conversational inputs"""
        return [re.compile(p, re.IGNORECASE) for p in CONVERSATIONAL_TRIVIAL_PATTERNS]

    def is_conversational_trivial(self, text: str) -> bool:
        """
        V7 FIX: Detect trivial conversational inputs that don't need multi-agent.

        Examples: "hello", "bonjour", "test", "ok", etc.

        Returns:
            True if input is a simple greeting/acknowledgment
        """
        text_stripped = text.strip()
        for pattern in self._trivial_patterns:
            if pattern.match(text_stripped):
                return True
        return False

    def _compile_patterns(self) -> Dict[TaskDomain, re.Pattern]:
        """Compile regex patterns for domain detection"""
        patterns = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            # Create case-insensitive pattern
            pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
            patterns[domain] = re.compile(pattern, re.IGNORECASE)
        return patterns

    def analyze(self, user_input: str) -> TaskAnalysis:
        """
        Analyze user input and return TaskAnalysis.

        Args:
            user_input: Raw user request text

        Returns:
            TaskAnalysis with complexity, domains, and agent fit scores
        """
        input_lower = user_input.lower()

        # V7 FIX: Check for trivial conversational inputs FIRST
        if self.is_conversational_trivial(user_input):
            return TaskAnalysis(
                complexity=TaskComplexity.TRIVIAL,
                domains=[],  # No specific domain
                primary_domain=TaskDomain.CREATIVE,  # Fallback
                requires_web=False,
                requires_code_execution=False,
                requires_deep_reasoning=False,
                requires_iteration=False,
                gemini_fit_score=0.5,
                claude_fit_score=0.5,
                raw_input=user_input,
                confidence=1.0,  # High confidence it's trivial
                detected_keywords=["[TRIVIAL_CONVERSATIONAL]"]
            )

        # Detect domains
        domains, detected_keywords = self._detect_domains(user_input)

        # Determine primary domain
        primary_domain = domains[0] if domains else TaskDomain.CODING

        # Calculate complexity
        complexity = self._calculate_complexity(input_lower, domains)

        # Detect requirements
        requires_web = self._detect_web_requirement(input_lower)
        requires_code = self._detect_code_requirement(input_lower, domains)
        requires_reasoning = self._detect_reasoning_requirement(
            input_lower, complexity
        )
        requires_iteration = self._detect_iteration_requirement(
            input_lower, domains
        )

        # Calculate agent fit scores
        gemini_score, claude_score = self._calculate_agent_fit(
            domains, requires_web, requires_code, requires_reasoning
        )

        # Estimate confidence
        confidence = self._estimate_confidence(
            domains, detected_keywords, user_input
        )

        return TaskAnalysis(
            complexity=complexity,
            domains=domains if domains else [TaskDomain.CODING],
            primary_domain=primary_domain,
            requires_web=requires_web,
            requires_code_execution=requires_code,
            requires_deep_reasoning=requires_reasoning,
            requires_iteration=requires_iteration,
            gemini_fit_score=gemini_score,
            claude_fit_score=claude_score,
            raw_input=user_input,
            confidence=confidence,
            detected_keywords=detected_keywords
        )

    def _detect_domains(
        self, text: str
    ) -> Tuple[List[TaskDomain], List[str]]:
        """
        Detect task domains from text.

        Returns:
            Tuple of (domains list sorted by relevance, detected keywords)
        """
        domain_scores: Dict[TaskDomain, int] = {}
        detected_keywords: List[str] = []

        for domain, pattern in self._domain_patterns.items():
            matches = pattern.findall(text)
            if matches:
                domain_scores[domain] = len(matches)
                detected_keywords.extend(matches)

        # Sort by score descending
        sorted_domains = sorted(
            domain_scores.keys(),
            key=lambda d: domain_scores[d],
            reverse=True
        )

        return sorted_domains, list(set(detected_keywords))

    def _calculate_complexity(
        self, text: str, domains: List[TaskDomain]
    ) -> TaskComplexity:
        """Calculate task complexity based on indicators"""
        score = 3  # Start at MODERATE

        # Apply keyword modifiers
        for keyword, modifier in COMPLEXITY_INDICATORS.items():
            if keyword in text:
                score += modifier

        # Domain-based modifiers
        if TaskDomain.SECURITY in domains:
            score += 1
        if TaskDomain.ARCHITECTURE in domains:
            score += 1
        if len(domains) > 2:  # Multi-domain tasks are more complex
            score += 1

        # Text length heuristic (longer = more complex)
        if len(text) > 500:
            score += 1
        elif len(text) < 50:
            score -= 1

        # Clamp to valid range
        score = max(1, min(5, score))

        return TaskComplexity(score)

    def _detect_web_requirement(self, text: str) -> bool:
        """Detect if task requires web access"""
        web_indicators = [
            "search", "latest", "recent", "news", "web",
            "url", "http", "fetch", "api", "online",
            "documentation", "look up", "find out"
        ]
        return any(indicator in text for indicator in web_indicators)

    def _detect_code_requirement(
        self, text: str, domains: List[TaskDomain]
    ) -> bool:
        """Detect if task requires code execution"""
        code_indicators = [
            "run", "execute", "test", "pytest", "build",
            "compile", "bash", "terminal", "command"
        ]
        has_indicators = any(ind in text for ind in code_indicators)
        has_code_domain = any(
            d in [TaskDomain.CODING, TaskDomain.TESTING, TaskDomain.DEBUGGING]
            for d in domains
        )
        return has_indicators or has_code_domain

    def _detect_reasoning_requirement(
        self, text: str, complexity: TaskComplexity
    ) -> bool:
        """Detect if task requires deep reasoning"""
        reasoning_indicators = [
            "why", "analyze", "understand", "explain how",
            "design", "architecture", "complex", "trade-off"
        ]
        return (
            any(ind in text for ind in reasoning_indicators)
            or complexity >= TaskComplexity.COMPLEX
        )

    def _detect_iteration_requirement(
        self, text: str, domains: List[TaskDomain]
    ) -> bool:
        """Detect if task requires iteration/refinement"""
        iteration_indicators = [
            "improve", "refine", "iterate", "brainstorm",
            "creative", "enhance", "optimize"
        ]
        has_indicators = any(ind in text for ind in iteration_indicators)
        has_creative = TaskDomain.CREATIVE in domains
        return has_indicators or has_creative

    def _calculate_agent_fit(
        self,
        domains: List[TaskDomain],
        requires_web: bool,
        requires_code: bool,
        requires_reasoning: bool
    ) -> Tuple[float, float]:
        """
        Calculate fit scores for Gemini and Claude.

        Returns:
            Tuple of (gemini_score, claude_score)
        """
        gemini_total = 0.0
        claude_total = 0.0
        weight_total = 0.0

        # Weight domains by position (first domain = most important)
        for i, domain in enumerate(domains[:3]):
            weight = 1.0 / (i + 1)  # 1.0, 0.5, 0.33
            gemini_total += AGENT_DOMAIN_STRENGTHS["gemini"][domain] * weight
            claude_total += AGENT_DOMAIN_STRENGTHS["claude"][domain] * weight
            weight_total += weight

        # Normalize
        if weight_total > 0:
            gemini_score = gemini_total / weight_total
            claude_score = claude_total / weight_total
        else:
            gemini_score = 0.5
            claude_score = 0.5

        # Apply requirement modifiers
        if requires_web:
            gemini_score += 0.1  # Gemini has native web search
            claude_score -= 0.05

        if requires_code:
            claude_score += 0.05  # Claude excels at SWE tasks

        if requires_reasoning:
            claude_score += 0.05  # Claude for complex reasoning

        # Clamp to 0-1
        gemini_score = max(0.0, min(1.0, gemini_score))
        claude_score = max(0.0, min(1.0, claude_score))

        return gemini_score, claude_score

    def _estimate_confidence(
        self,
        domains: List[TaskDomain],
        keywords: List[str],
        text: str
    ) -> float:
        """Estimate confidence in the analysis"""
        confidence = 0.5  # Base confidence

        # More keywords = higher confidence
        confidence += min(0.3, len(keywords) * 0.05)

        # Domains detected = higher confidence
        confidence += min(0.2, len(domains) * 0.1)

        # Reasonable length = higher confidence
        if 50 < len(text) < 1000:
            confidence += 0.1

        return min(1.0, confidence)
