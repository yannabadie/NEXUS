"""
NEXUS V7 Model Routing Module

Routes tasks to appropriate models based on complexity and task type.
Supports Opus/Sonnet selection for Claude and model variants for Gemini.
"""

from .model_router import (
    ModelRouter,
    TaskType,
    RoutingDecision,
    RoutingPolicy,
    ModelTier,
    CascadeRoute,
)

# V12.4: Resource Optimizer
from .resource_optimizer import (
    ResourceOptimizer,
    ModelSpec,
    OptimizationDecision,
    OptimizationReport,
    UsageRecord,
    get_resource_optimizer,
    reset_resource_optimizer,
)

# V12.4: Decision Cache
from .decision_cache import (
    RoutingDecisionCache,
    CachedDecision,
    DecisionOutcome,
    DecisionCacheStats,
    get_decision_cache,
    reset_decision_cache,
)

# V12.4 COGNITIVE BOOST: Routing Effectiveness Analyzer
from .routing_effectiveness_analyzer import (
    RoutingEffectivenessAnalyzer,
    RoutingDecisionRecord,
    PolicyMetrics,
    AnalyzerStats as RoutingAnalyzerStats,
    get_routing_analyzer,
    reset_routing_analyzer,
)

__all__ = [
    "ModelRouter",
    "TaskType",
    "RoutingDecision",
    "RoutingPolicy",
    "ModelTier",
    "CascadeRoute",
    # V12.4: Resource Optimizer
    "ResourceOptimizer",
    "ModelSpec",
    "OptimizationDecision",
    "OptimizationReport",
    "UsageRecord",
    "get_resource_optimizer",
    "reset_resource_optimizer",
    # V12.4: Decision Cache
    "RoutingDecisionCache",
    "CachedDecision",
    "DecisionOutcome",
    "DecisionCacheStats",
    "get_decision_cache",
    "reset_decision_cache",
    # V12.4 COGNITIVE BOOST: Routing Effectiveness Analyzer
    "RoutingEffectivenessAnalyzer",
    "RoutingDecisionRecord",
    "PolicyMetrics",
    "RoutingAnalyzerStats",
    "get_routing_analyzer",
    "reset_routing_analyzer",
]
