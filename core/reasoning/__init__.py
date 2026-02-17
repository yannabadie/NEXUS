"""
NEXUS V7 - Reasoning Module

Advanced reasoning patterns for complex problem-solving:
- Graph of Thought (GoT): Non-linear exploration with branching and merging
- Chain of Thought (CoT): Linear step-by-step reasoning
- Tree of Thought (ToT): Tree-based exploration with pruning

NOTE: GoT implementation is optional and loaded lazily by HybridSwarmEngine.
This module currently exports nothing - implementations pending.
To use GoT, create core/reasoning/graph_of_thought.py with the required classes.
"""

# V7 FIX: Make imports optional to avoid blocking the entire system
# GoT is a future enhancement, not required for core functionality

__all__ = []

# Lazy loading pattern - consumers should check availability:
# from core.reasoning import GOT_AVAILABLE
# if GOT_AVAILABLE:
#     from core.reasoning import GraphOfThought

GOT_AVAILABLE = False

try:
    from .graph_of_thought import (
        GraphOfThought,
        ThoughtNode,
        ThoughtGraph,
        ThoughtStatus,
        ThoughtType
    )
    GOT_AVAILABLE = True
    __all__ = [
        'GraphOfThought',
        'ThoughtNode',
        'ThoughtGraph',
        'ThoughtStatus',
        'ThoughtType',
        'GOT_AVAILABLE'
    ]
except ImportError:
    # GoT not implemented yet - this is OK
    GraphOfThought = None
    ThoughtNode = None
    ThoughtGraph = None
    ThoughtStatus = None
    ThoughtType = None
    __all__ = ['GOT_AVAILABLE']

# V12.4 COGNITIVE BOOST: Thought Evaluator
from .thought_evaluator import (
    ThoughtEvaluator,
    ThoughtScore,
    EvaluationResult,
    EvaluatorStats,
    get_thought_evaluator,
    reset_thought_evaluator,
)

__all__ += [
    'ThoughtEvaluator',
    'ThoughtScore',
    'EvaluationResult',
    'EvaluatorStats',
    'get_thought_evaluator',
    'reset_thought_evaluator',
]

# V12.4 COGNITIVE BOOST: Reasoning Quality Scorer
from .reasoning_quality_scorer import (
    ReasoningQualityScorer,
    ReasoningEvaluation,
    AgentReasoningProfile,
    ScorerStats,
    get_quality_scorer,
    reset_quality_scorer,
)

__all__ += [
    'ReasoningQualityScorer',
    'ReasoningEvaluation',
    'AgentReasoningProfile',
    'ScorerStats',
    'get_quality_scorer',
    'reset_quality_scorer',
]

# V12.4 COGNITIVE BOOST: Cognitive Degradation Detector
from .cognitive_degradation import (
    CognitiveDegradationDetector,
    DegradationSignal,
    DegradationReason,
    Mitigation,
    DetectorStats,
    get_degradation_detector,
    reset_degradation_detector,
)

__all__ += [
    'CognitiveDegradationDetector',
    'DegradationSignal',
    'DegradationReason',
    'Mitigation',
    'DetectorStats',
    'get_degradation_detector',
    'reset_degradation_detector',
]

# V12.4 COGNITIVE BOOST: Evaluation Panel (CRM-inspired)
from .evaluation_panel import (
    EvaluationPanel,
    EvalDimension,
    DimensionScore,
    PanelResult,
    get_evaluation_panel,
    reset_evaluation_panel,
)

__all__ += [
    'EvaluationPanel',
    'EvalDimension',
    'DimensionScore',
    'PanelResult',
    'get_evaluation_panel',
    'reset_evaluation_panel',
]

# V12.4 COGNITIVE BOOST: Consensus Verifier (Six Sigma-inspired)
from .consensus_verifier import (
    ConsensusVerifier,
    VerificationOutcome,
    VerificationResult,
    QualityGate,
    get_consensus_verifier,
    reset_consensus_verifier,
)

__all__ += [
    'ConsensusVerifier',
    'VerificationOutcome',
    'VerificationResult',
    'QualityGate',
    'get_consensus_verifier',
    'reset_consensus_verifier',
]

# V12.4 COGNITIVE BOOST: Meta-Policy Memory (MPR, arxiv:2509.03990)
from .meta_policy_memory import (
    MetaPolicyMemory,
    PolicyRule,
    RuleCategory,
    AdmissibilityResult,
    get_meta_policy_memory,
    reset_meta_policy_memory,
)

__all__ += [
    'MetaPolicyMemory',
    'PolicyRule',
    'RuleCategory',
    'AdmissibilityResult',
    'get_meta_policy_memory',
    'reset_meta_policy_memory',
]

# V12.4 COGNITIVE BOOST: Metacognitive Monitor (MASC, arxiv:2510.14319)
from .metacognitive_monitor import (
    MetacognitiveMonitor,
    AnomalyScore,
    get_metacognitive_monitor,
    reset_metacognitive_monitor,
)

__all__ += [
    'MetacognitiveMonitor',
    'AnomalyScore',
    'get_metacognitive_monitor',
    'reset_metacognitive_monitor',
]

# V12.4 COGNITIVE BOOST: Inspector Guard (arxiv:2408.00989)
from .inspector_guard import (
    InspectorGuard,
    InspectionResult,
    RiskLevel,
    IssuePattern,
    GuardStats,
    get_inspector_guard,
    reset_inspector_guard,
)

__all__ += [
    'InspectorGuard',
    'InspectionResult',
    'RiskLevel',
    'IssuePattern',
    'GuardStats',
    'get_inspector_guard',
    'reset_inspector_guard',
]

# V12.4 COGNITIVE BOOST: Confidence Calibrator (arxiv:2404.09127)
from .confidence_calibrator import (
    ConfidenceCalibrator,
    CalibratedConfidence,
    ConfidenceBias,
    AgentCalibrationProfile,
    CalibratorStats,
    get_confidence_calibrator,
    reset_confidence_calibrator,
)

__all__ += [
    'ConfidenceCalibrator',
    'CalibratedConfidence',
    'ConfidenceBias',
    'AgentCalibrationProfile',
    'CalibratorStats',
    'get_confidence_calibrator',
    'reset_confidence_calibrator',
]

# V12.4 COGNITIVE BOOST: Trajectory Scorer (FREE-MAD, arxiv:2509.11035)
from .trajectory_scorer import (
    TrajectoryScorer,
    TrajectoryResult,
    AgentTrajectory,
    ConformityAnalysis,
    get_trajectory_scorer,
    reset_trajectory_scorer,
)

__all__ += [
    'TrajectoryScorer',
    'TrajectoryResult',
    'AgentTrajectory',
    'ConformityAnalysis',
    'get_trajectory_scorer',
    'reset_trajectory_scorer',
]

# V12.4 COGNITIVE BOOST: Uncertainty Propagator (arxiv:2601.15703)
from .uncertainty_propagator import (
    UncertaintyPropagator,
    PropagationSignal,
    UncertaintyLevel,
    ChainSummary,
    PropagatorStats,
    get_uncertainty_propagator,
    reset_uncertainty_propagator,
)

__all__ += [
    'UncertaintyPropagator',
    'PropagationSignal',
    'UncertaintyLevel',
    'ChainSummary',
    'PropagatorStats',
    'get_uncertainty_propagator',
    'reset_uncertainty_propagator',
]
