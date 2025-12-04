"""
Evolution Manager - V7.5 Phase 0a

Central orchestrator for evolution operations.
Extracted from repl.py to decouple evolution from UI.

This manager coordinates:
- Brainstorming: AI-driven mutation proposals (Gemini + Claude debate)
- Child Creation: Applying mutations to create new instances
- Validation: Tiered validation (syntax → smoke → benchmark → redteam)
- Evaluation: Fitness scoring and parent comparison
- Promotion: Winner selection and parent replacement

Usage:
    manager = EvolutionManager(workspace_path, config, orchestrator)
    result = manager.run_evolution_cycle(child_count=3)
    if result.success:
        print(f"Winner: {result.winner_id} (score: {result.winner_score})")
"""
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import json
import time

from core.evolution.models import (
    MutationProposal,
    BrainstormResult,
    ChildCreationResult,
    ValidationResult,
    EvaluationResult,
    PromotionResult,
    ArchiveResult,
    EvolutionResult,
    SpecializationResult,
    EvolutionStatus,
    EvolutionContext,
    EvolutionPhaseStatus,
)
from core.evolution.rate_limiter import EvolutionRateLimiter
from core.evolution.lineage import load_lineage, add_child, sign_birth_certificate
from core.evolution.tiered_validator import TieredValidator, ValidationTier
from core.evolution.evaluator import run_benchmarks, compare_to_parent
from core.evolution.phases.brainstorm import BrainstormPhase
from core.evolution.phases.create import CreatePhase
from core.evolution.phases.promote import PromotePhase


# Type alias for progress callback
ProgressCallback = Callable[[str, float], None]


class EvolutionManager:
    """
    Central orchestrator for evolution operations.

    V7.5 Phase 0a: Extracted from repl.py to enable:
    - Scriptable evolution (no REPL required)
    - Independent testing
    - Clear separation of concerns
    """

    def __init__(
        self,
        workspace_path: Path,
        nexus_root: Path,
        config: Any,
        orchestrator: Any,
        rate_limiter: Optional[EvolutionRateLimiter] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        Initialize EvolutionManager.

        Args:
            workspace_path: Path to workspace directory
            nexus_root: Path to NEXUS installation root
            config: NEXUS configuration object
            orchestrator: OrchestratorV7 instance for AI interactions
            rate_limiter: Optional rate limiter (creates default if None)
            progress_callback: Optional callback for progress updates
        """
        self.workspace_path = workspace_path
        self.nexus_root = nexus_root
        self.config = config
        self.orchestrator = orchestrator
        self.rate_limiter = rate_limiter or EvolutionRateLimiter(workspace_path, config)
        self.progress_callback = progress_callback

        # Paths
        self.children_path = workspace_path / "children"
        self.archive_path = nexus_root / "ARCHIVE"
        self.lineage_path = workspace_path / "LINEAGE.json"

        # Validator
        self.validator = TieredValidator(workspace_path, config)

        # Phase executors
        self._brainstorm_phase = BrainstormPhase(
            orchestrator=orchestrator,
            workspace_path=workspace_path,
            progress_callback=progress_callback,
        )
        self._create_phase = CreatePhase(
            workspace_path=workspace_path,
            nexus_root=nexus_root,
            progress_callback=progress_callback,
        )
        self._promote_phase = PromotePhase(
            workspace_path=workspace_path,
            nexus_root=nexus_root,
            progress_callback=progress_callback,
        )

    def _report_progress(self, message: str, progress: float = 0.0):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    # =========================================================================
    # Phase 1: Brainstorming
    # =========================================================================

    def brainstorm_mutations(
        self,
        parent_id: str,
        child_count: int = 3,
        focus_areas: Optional[List[str]] = None,
    ) -> BrainstormResult:
        """
        Generate mutation proposals via AI debate.

        V7.5: Uses Gemini + Claude EVOLUTION_BRAINSTORM mode.
        Mutations are emergent from AI debate, not hardcoded templates.

        Args:
            parent_id: ID of parent to mutate
            child_count: Number of mutations to propose
            focus_areas: Optional focus areas for mutations

        Returns:
            BrainstormResult with proposed mutations
        """
        self._report_progress("Starting brainstorming phase...", 0.1)

        # Get parent path from nexus_root
        parent_path = self.nexus_root

        # Use BrainstormPhase for actual implementation
        return self._brainstorm_phase.run(
            parent_id=parent_id,
            parent_path=parent_path,
            child_count=child_count,
            focus_areas=focus_areas,
        )

    def brainstorm_specialist(
        self,
        parent_id: str,
        mission: str,
    ) -> BrainstormResult:
        """
        Generate specialist/spinoff mutation proposals.

        V7.5: Creates specialized agent focused on specific mission.

        Args:
            parent_id: ID of parent to specialize
            mission: Specialization mission description

        Returns:
            BrainstormResult with specialist mutation
        """
        self._report_progress(f"Brainstorming specialist: {mission}", 0.1)
        start_time = time.time()

        # TODO: Extract from repl.py:brainstorm_spinoff_with_ais()

        return BrainstormResult(
            mutations=[],
            debate_turns=0,
            consensus_reached=False,
            duration_seconds=time.time() - start_time,
            errors=["Not yet implemented - will extract from repl.py"],
        )

    # =========================================================================
    # Phase 2: Child Creation
    # =========================================================================

    def create_children(
        self,
        mutations: List[MutationProposal],
        parent_id: Optional[str] = None,
        generation: Optional[int] = None,
    ) -> ChildCreationResult:
        """
        Create child instances from mutation proposals.

        Args:
            mutations: List of mutation proposals to apply
            parent_id: Parent ID (auto-detected from lineage if None)
            generation: Current generation (auto-detected if None)

        Returns:
            ChildCreationResult with created child IDs
        """
        self._report_progress(f"Creating {len(mutations)} children...", 0.3)

        # Get parent_id and generation from lineage if not provided
        if parent_id is None or generation is None:
            lineage = load_lineage(self.lineage_path)
            if parent_id is None:
                parent_id = lineage.get("current_parent", "nexus_v7")
            if generation is None:
                generation = lineage.get("generation", 1) + 1

        # Delegate to CreatePhase
        return self._create_phase.run(
            mutations=mutations,
            parent_id=parent_id,
            generation=generation,
        )

    # =========================================================================
    # Phase 3: Validation
    # =========================================================================

    def validate_children(
        self,
        children: List[str],
        tier: ValidationTier = ValidationTier.REDTEAM,
    ) -> List[ValidationResult]:
        """
        Validate children through tiered validation.

        Args:
            children: List of child IDs to validate
            tier: Maximum validation tier to reach

        Returns:
            List of ValidationResult for each child
        """
        self._report_progress(f"Validating {len(children)} children...", 0.5)
        results = []

        for i, child_id in enumerate(children):
            child_path = self.children_path / child_id
            progress = 0.5 + (0.2 * (i / len(children)))
            self._report_progress(f"Validating {child_id}...", progress)

            # Use tiered validator
            tier_result = self.validator.validate_child(child_path, tier)

            results.append(
                ValidationResult(
                    child_id=child_id,
                    passed=tier_result.passed,
                    tier_reached=tier_result.tier_reached.value if hasattr(tier_result.tier_reached, 'value') else tier_result.tier_reached,
                    errors=tier_result.errors if hasattr(tier_result, 'errors') else [],
                    details=tier_result.details if hasattr(tier_result, 'details') else {},
                )
            )

        return results

    # =========================================================================
    # Phase 4: Evaluation
    # =========================================================================

    def evaluate_fitness(
        self,
        children: List[str],
        parent_id: str,
    ) -> List[EvaluationResult]:
        """
        Evaluate fitness of validated children.

        Args:
            children: List of child IDs to evaluate
            parent_id: Parent ID for comparison

        Returns:
            List of EvaluationResult for each child
        """
        self._report_progress(f"Evaluating fitness of {len(children)} children...", 0.7)
        results = []

        for child_id in children:
            child_path = self.children_path / child_id

            # Run benchmarks (from evaluator.py)
            benchmark_result = run_benchmarks(child_path)
            parent_comparison = compare_to_parent(benchmark_result, parent_id)

            results.append(
                EvaluationResult(
                    child_id=child_id,
                    fitness_score=benchmark_result.get("fitness_score", 0.0),
                    parent_score=parent_comparison.get("parent_score", 0.0),
                    improvement_pct=parent_comparison.get("improvement_pct", 0.0),
                    metrics=benchmark_result.get("metrics", {}),
                    passed_threshold=parent_comparison.get("passed_threshold", False),
                )
            )

        return results

    # =========================================================================
    # Phase 5: Promotion
    # =========================================================================

    def promote_child(
        self,
        child_id: str,
        fitness_score: float,
        generation: Optional[int] = None,
        child_metadata: Optional[Dict] = None,
    ) -> PromotionResult:
        """
        Promote a child to become the new parent.

        Args:
            child_id: ID of child to promote
            fitness_score: Final fitness score
            generation: Current generation (auto-detected if None)
            child_metadata: Optional additional metadata

        Returns:
            PromotionResult with promotion details
        """
        self._report_progress(f"Promoting {child_id}...", 0.9)

        # Get generation from lineage if not provided
        if generation is None:
            lineage = load_lineage(self.lineage_path)
            generation = lineage.get("generation", 1) + 1

        return self._promote_phase.promote_child(
            child_id=child_id,
            fitness_score=fitness_score,
            generation=generation,
            child_metadata=child_metadata,
        )

    def archive_child(
        self,
        child_id: str,
        reason: str,
        generation: Optional[int] = None,
        fitness_score: float = 0.0,
    ) -> ArchiveResult:
        """
        Archive a rejected child.

        Args:
            child_id: ID of child to archive
            reason: Reason for rejection
            generation: Current generation (auto-detected if None)
            fitness_score: Final fitness score

        Returns:
            ArchiveResult with archive details
        """
        self._report_progress(f"Archiving {child_id}...", 0.95)

        # Get generation from lineage if not provided
        if generation is None:
            lineage = load_lineage(self.lineage_path)
            generation = lineage.get("generation", 1)

        return self._promote_phase.archive_rejected_child(
            child_id=child_id,
            generation=generation,
            reason=reason,
            fitness_score=fitness_score,
        )

    # =========================================================================
    # Orchestration
    # =========================================================================

    def run_evolution_cycle(
        self,
        child_count: int = 3,
        focus_areas: Optional[List[str]] = None,
    ) -> EvolutionResult:
        """
        Run a complete evolution cycle.

        Phases:
        1. Rate limiting check
        2. Brainstorming (AI debate for mutations)
        3. Child creation (apply mutations)
        4. Validation (tiered fast-fail)
        5. Evaluation (fitness scoring)
        6. Promotion (winner becomes parent)

        Args:
            child_count: Number of children to create
            focus_areas: Optional focus areas for mutations

        Returns:
            EvolutionResult with complete cycle results
        """
        start_time = time.time()
        result = EvolutionResult(
            success=False,
            phase_reached="init",
            started_at=datetime.now(),
        )

        # Check rate limits
        can_evolve, reason = self.rate_limiter.can_evolve()
        if not can_evolve:
            result.errors.append(f"Rate limited: {reason}")
            return result

        # Get current parent ID from lineage
        lineage = load_lineage(self.lineage_path)
        parent_id = lineage.get("current_parent", "nexus_v7")

        try:
            # Phase 1: Brainstorming
            result.phase_reached = "brainstorm"
            brainstorm_result = self.brainstorm_mutations(parent_id, child_count, focus_areas)
            if not brainstorm_result.mutations:
                result.errors.extend(brainstorm_result.errors)
                return result
            result.mutations_proposed = len(brainstorm_result.mutations)

            # Phase 2: Child Creation
            result.phase_reached = "create"
            creation_result = self.create_children(brainstorm_result.mutations)
            if not creation_result.success:
                result.errors.extend(creation_result.errors)
                return result
            result.children_created = len(creation_result.children_created)

            # Phase 3: Validation
            result.phase_reached = "validate"
            validation_results = self.validate_children(creation_result.children_created)
            passed_children = [v.child_id for v in validation_results if v.passed]
            result.children_validated = len(passed_children)

            if not passed_children:
                result.errors.append("No children passed validation")
                return result

            # Phase 4: Evaluation
            result.phase_reached = "evaluate"
            evaluation_results = self.evaluate_fitness(passed_children, parent_id)

            # Find winner
            winner = max(evaluation_results, key=lambda e: e.fitness_score, default=None)
            if not winner or not winner.passed_threshold:
                result.errors.append("No children exceeded parent fitness")
                return result

            result.winner_id = winner.child_id
            result.winner_score = winner.fitness_score

            # Phase 5: Promotion
            result.phase_reached = "promote"
            promotion_result = self.promote_child(winner.child_id, winner.fitness_score)
            result.promoted = promotion_result.success

            if promotion_result.success:
                result.success = True
                # Archive non-winners
                for eval_result in evaluation_results:
                    if eval_result.child_id != winner.child_id:
                        self.archive_child(eval_result.child_id, "Not selected as winner")

        except Exception as e:
            result.errors.append(f"Evolution error: {str(e)}")

        result.completed_at = datetime.now()
        result.duration_seconds = time.time() - start_time
        return result

    def run_specialization(
        self,
        mission: str,
    ) -> SpecializationResult:
        """
        Run a specialization/spinoff cycle.

        Creates a specialized agent focused on a specific mission.

        Args:
            mission: Specialization mission description

        Returns:
            SpecializationResult with created agent details
        """
        self._report_progress(f"Running specialization: {mission}", 0.0)

        # Get current parent ID from lineage
        lineage = load_lineage(self.lineage_path)
        parent_id = lineage.get("current_parent", "nexus_v7")

        # Brainstorm specialist mutations
        brainstorm_result = self.brainstorm_specialist(parent_id, mission)
        if not brainstorm_result.mutations:
            return SpecializationResult(
                success=False,
                mission=mission,
                errors=brainstorm_result.errors,
            )

        # TODO: Create specialist agent in workspace/agents/
        # Extract from repl.py:run_specialization()

        return SpecializationResult(
            success=False,
            mission=mission,
            errors=["Not yet implemented - will extract from repl.py"],
        )

    # =========================================================================
    # Status & Queries
    # =========================================================================

    def get_status(self) -> EvolutionStatus:
        """
        Get current evolution system status.

        Returns:
            EvolutionStatus with current state
        """
        lineage = load_lineage(self.lineage_path)
        can_evolve, block_reason = self.rate_limiter.can_evolve()

        # Count children
        total_children = 0
        pending_children = 0
        if self.children_path.exists():
            for child_dir in self.children_path.iterdir():
                if child_dir.is_dir():
                    total_children += 1
                    status_file = child_dir / "status.json"
                    if status_file.exists():
                        status = json.loads(status_file.read_text())
                        if status.get("status") == "pending":
                            pending_children += 1

        return EvolutionStatus(
            current_generation=lineage.get("generation", 1),
            total_children=total_children,
            pending_children=pending_children,
            last_evolution=None,  # TODO: Track from rate limiter
            rate_limit_remaining=self.rate_limiter.remaining_today() if hasattr(self.rate_limiter, 'remaining_today') else 0,
            can_evolve=can_evolve,
            block_reason=block_reason if not can_evolve else None,
        )
