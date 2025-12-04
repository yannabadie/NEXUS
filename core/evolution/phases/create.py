"""
Create Phase - V7.5 Phase 0a

Child instance creation from mutation proposals.
Extracted from repl.py:run_evolve() child creation loop.

Creates sandboxed child instances by:
1. Copying parent to GENERATION_ACTIVE/<child_id>/
2. Applying mutations to target files
3. Signing birth certificates
"""
import shutil
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from core.evolution.models import (
    MutationProposal,
    ChildCreationResult,
)
from core.security import MutationValidator


# Type alias for progress callback
ProgressCallback = Callable[[str, float], None]


class CreatePhase:
    """
    Phase 2: Child instance creation.

    Creates sandboxed child instances from mutation proposals.
    Each child is a copy of parent with mutations applied.
    """

    def __init__(
        self,
        workspace_path: Path,
        nexus_root: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        """
        Initialize create phase.

        Args:
            workspace_path: Path to workspace directory
            nexus_root: Path to NEXUS installation root
            progress_callback: Optional callback for progress updates
        """
        self.workspace_path = workspace_path
        self.nexus_root = nexus_root
        self.project_root = nexus_root.parent
        self.generation_active = self.project_root / "GENERATION_ACTIVE"
        self.progress_callback = progress_callback
        self.mutation_validator = MutationValidator(workspace_path=workspace_path)

    def _report_progress(self, message: str, progress: float = 0.0):
        """Report progress to callback if available"""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def _validate_mutation_path(self, file_path: str) -> tuple[bool, str]:
        """Validate that mutation target path exists in parent"""
        target = self.nexus_root / file_path
        if not target.exists():
            return False, f"File not found: {file_path}"
        return True, "OK"

    def _apply_mutation(
        self,
        child_dir: Path,
        mutation: Dict[str, Any],
    ) -> tuple[bool, str]:
        """
        Apply a single mutation to child.

        Args:
            child_dir: Path to child directory
            mutation: Mutation dict with file, change, operation

        Returns:
            (success, message) tuple
        """
        target_file = child_dir / mutation['file']
        if not target_file.exists():
            return False, f"Target file not found: {mutation['file']}"

        try:
            original_content = target_file.read_text(encoding='utf-8')
            mutation_code = mutation['change']
            operation = mutation.get('operation', 'APPEND').upper()

            # Security validation (warn mode)
            warnings, _ = self.mutation_validator.validate(mutation_code, mutation['file'])

            if operation == 'REPLACE':
                # Use search_block for exact matching
                search_block = mutation.get('search_block', '')
                if search_block and search_block in original_content:
                    mutated_content = original_content.replace(search_block, mutation_code, 1)
                else:
                    # Fallback to target line matching
                    target_line = mutation.get('target', '')
                    if not target_line or target_line not in original_content:
                        return False, f"Target not found for REPLACE operation"
                    mutated_content = original_content.replace(target_line, mutation_code, 1)

            elif operation == 'APPEND':
                mutated_content = original_content + '\n' + mutation_code

            elif operation == 'PREPEND':
                mutated_content = mutation_code + '\n' + original_content

            elif operation == 'INSERT_AFTER':
                marker = mutation.get('marker', '')
                if marker and marker in original_content:
                    idx = original_content.find(marker) + len(marker)
                    mutated_content = original_content[:idx] + '\n' + mutation_code + original_content[idx:]
                else:
                    return False, f"Marker not found for INSERT_AFTER"

            else:
                return False, f"Unknown operation: {operation}"

            target_file.write_text(mutated_content, encoding='utf-8')
            return True, f"Applied {operation} mutation"

        except Exception as e:
            return False, f"Mutation error: {str(e)}"

    def _create_birth_certificate(
        self,
        child_dir: Path,
        child_id: str,
        parent_id: str,
        generation: int,
        mutation: Dict[str, Any],
    ) -> Path:
        """Create and sign birth certificate for child"""
        birth_cert = {
            "id": child_id,
            "parent_id": parent_id,
            "generation": generation,
            "birth_date": datetime.now().isoformat(),
            "creator": "Yann Abadie",
            "mutations": [{
                "file": mutation.get('file', ''),
                "change": mutation.get('change', ''),
                "reason": mutation.get('reason', ''),
                "expected_asi_impact": mutation.get('expected_asi_impact', 0),
            }],
            "source": "Gemini+Claude symbiotic debate (emergent)",
            "signature": "NEXUS_KERNEL_ALIGNED"
        }

        birth_cert_path = child_dir / "BIRTH_CERTIFICATE.json"
        birth_cert_path.write_text(
            json.dumps(birth_cert, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        return birth_cert_path

    def create_child(
        self,
        mutation: MutationProposal,
        parent_id: str,
        generation: int,
        child_index: int,
    ) -> tuple[Optional[str], Optional[Path], List[str]]:
        """
        Create a single child from mutation.

        Args:
            mutation: MutationProposal to apply
            parent_id: Parent ID
            generation: Current generation
            child_index: Index for naming

        Returns:
            (child_id, child_path, errors) tuple
        """
        errors = []

        # Generate child ID
        file_basename = Path(mutation.files_to_modify[0]).stem if mutation.files_to_modify else "unknown"
        child_id = f"NEXUS_V7.1_CHILD_{child_index:03d}_{file_basename.upper()}"

        # Validate mutation path
        if mutation.files_to_modify:
            valid, msg = self._validate_mutation_path(mutation.files_to_modify[0])
            if not valid:
                return None, None, [msg]

        # Create child directory
        child_dir = self.generation_active / child_id
        if child_dir.exists():
            shutil.rmtree(child_dir)

        try:
            # Copy parent to child
            self.generation_active.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                self.nexus_root,
                child_dir,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.nexus', 'workspace', 'workspace_archive', '.git'
                ),
                dirs_exist_ok=True
            )

            # Copy KERNEL.py (alignment file)
            kernel_path = self.project_root / "KERNEL.py"
            kernel_hash_path = self.project_root / "KERNEL_HASH.txt"
            if kernel_path.exists():
                shutil.copy2(kernel_path, child_dir / "KERNEL.py")
                if kernel_hash_path.exists():
                    shutil.copy2(kernel_hash_path, child_dir / "KERNEL_HASH.txt")

            # Create workspace directories
            child_workspace = child_dir / "workspace"
            child_workspace.mkdir(exist_ok=True)
            (child_workspace / "_IO_BUFFER").mkdir(exist_ok=True)
            (child_workspace / ".nexus").mkdir(exist_ok=True)
            (child_workspace / "logs").mkdir(exist_ok=True)

            # Apply mutation from metadata (original dict format)
            mutation_dict = mutation.metadata if mutation.metadata else {
                'file': mutation.files_to_modify[0] if mutation.files_to_modify else '',
                'change': mutation.patches[0].get('replace', '') if mutation.patches else '',
                'search_block': mutation.patches[0].get('search', '') if mutation.patches else '',
                'reason': mutation.rationale,
                'expected_asi_impact': mutation.confidence,
                'operation': 'REPLACE' if mutation.patches and mutation.patches[0].get('search') else 'APPEND',
            }

            success, msg = self._apply_mutation(child_dir, mutation_dict)
            if not success:
                shutil.rmtree(child_dir)
                return None, None, [msg]

            # Create birth certificate
            self._create_birth_certificate(
                child_dir, child_id, parent_id, generation, mutation_dict
            )

            return child_id, child_dir, []

        except Exception as e:
            if child_dir.exists():
                shutil.rmtree(child_dir)
            return None, None, [f"Creation failed: {str(e)}"]

    def run(
        self,
        mutations: List[MutationProposal],
        parent_id: str,
        generation: int,
    ) -> ChildCreationResult:
        """
        Create children from mutations.

        Args:
            mutations: List of mutation proposals
            parent_id: Parent ID
            generation: Current generation

        Returns:
            ChildCreationResult with created children
        """
        start_time = time.time()
        children_created = []
        all_errors = []
        all_warnings = []

        total = len(mutations)
        for i, mutation in enumerate(mutations):
            progress = i / total
            self._report_progress(f"Creating child {i+1}/{total}", progress)

            child_id, child_path, errors = self.create_child(
                mutation, parent_id, generation, i + 1
            )

            if child_id and child_path:
                children_created.append(child_id)
            else:
                all_errors.extend(errors)
                all_warnings.append(f"Skipped mutation {i+1}: {errors}")

        self._report_progress(f"Created {len(children_created)} children", 1.0)

        return ChildCreationResult(
            success=len(children_created) > 0,
            children_created=children_created,
            errors=all_errors,
            warnings=all_warnings,
            duration_seconds=time.time() - start_time,
        )


def create_children(
    workspace_path: Path,
    nexus_root: Path,
    mutations: List[MutationProposal],
    parent_id: str,
    generation: int,
    progress_callback: Optional[ProgressCallback] = None,
) -> ChildCreationResult:
    """
    Convenience function to create children from mutations.

    Args:
        workspace_path: Path to workspace directory
        nexus_root: Path to NEXUS installation root
        mutations: List of mutation proposals
        parent_id: Parent ID
        generation: Current generation
        progress_callback: Optional callback for progress updates

    Returns:
        ChildCreationResult with created children
    """
    phase = CreatePhase(workspace_path, nexus_root, progress_callback)
    return phase.run(mutations, parent_id, generation)
