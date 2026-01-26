#!/usr/bin/env python
"""
NCM Deep Analysis using Meta GraphRAG - Generate detailed task list.

Objectif: Utiliser meta GraphRAG pour produire une analyse profonde avec:
- Liste de tâches (fichier par fichier, ligne par ligne)
- Raisons pour chaque tâche
- Impacts croisés
- Boucle de vérification agentique

Usage:
    python scripts/ncm/ncm_deep_analysis.py
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

# Add NEXUS root to path
NEXUS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(NEXUS_ROOT))

from core.mcp.server import (
    build_meta_graphrag_query,
    build_meta_graphrag_status,
    build_meta_graphrag_reports,
)


@dataclass
class Task:
    """Représente une tâche NCM détaillée."""
    task_id: str
    file_path: str
    line_numbers: str  # "L42-L56" or "L42"
    issue_type: str  # "missing_docstring", "type_hint", "security", etc.
    description: str
    reason: str
    cross_impacts: List[str]  # Files/modules impacted by this change
    priority: str  # "P0", "P1", "P2"
    verification_method: str  # How to verify this task


@dataclass
class AnalysisResult:
    """Résultat de l'analyse profonde."""
    meta_graphrag_status: Dict[str, Any]
    queries_performed: List[Dict[str, Any]]
    tasks: List[Task]
    total_files: int
    total_tasks: int
    summary: str


def query_meta_graphrag(query: str, **kwargs) -> Dict[str, Any]:
    """Query Meta GraphRAG index."""
    print(f"\n[META_GRAPHRAG] Query: {query}")

    result = build_meta_graphrag_query(
        query=query,
        seed_limit=kwargs.get("seed_limit", 10),
        expansion_depth=kwargs.get("expansion_depth", 2),
        expansion_limit=kwargs.get("expansion_limit", 20),
        include_text=kwargs.get("include_text", False),
    )

    print(f"  > Found {result['seed_count']} seed chunks, {result['expanded_count']} expanded")
    return result


def extract_tasks_from_chunks(
    chunks: List[Dict[str, Any]],
    issue_type: str,
    priority: str
) -> List[Task]:
    """Extract NCM tasks from Meta GraphRAG chunks."""
    tasks = []
    task_counter = 1

    for chunk in chunks:
        file_path = chunk.get("path", "")
        start_line = chunk.get("start_line", 0)
        end_line = chunk.get("end_line", 0)
        kind = chunk.get("kind", "")
        node_id = chunk.get("node_id", "")

        # Skip non-actionable chunks
        if not file_path or file_path.startswith("tests/"):
            continue

        # Generate task based on issue type
        line_range = f"L{start_line}-L{end_line}" if end_line > start_line else f"L{start_line}"

        task = Task(
            task_id=f"DEEP-{issue_type.upper()}-{task_counter:03d}",
            file_path=file_path,
            line_numbers=line_range,
            issue_type=issue_type,
            description=f"{issue_type.replace('_', ' ').title()} in {kind} at {file_path}:{line_range}",
            reason=_generate_reason(issue_type, kind),
            cross_impacts=_identify_cross_impacts(node_id, file_path),
            priority=priority,
            verification_method=_get_verification_method(issue_type),
        )

        tasks.append(task)
        task_counter += 1

    return tasks


def _generate_reason(issue_type: str, kind: str) -> str:
    """Generate reason for task based on issue type."""
    reasons = {
        "missing_docstring": f"Documentation manquante pour {kind}. Améliore maintenabilité et compréhension du code.",
        "missing_type_hint": f"Type hints manquants pour {kind}. Améliore sécurité des types et autocomplétion IDE.",
        "dead_import": f"Import inutilisé dans {kind}. Réduit la surface d'attaque et améliore performances.",
        "security_issue": f"Problème de sécurité détecté dans {kind}. CRITIQUE pour production.",
        "complexity": f"Complexité élevée dans {kind}. Refactoring nécessaire pour maintenabilité.",
        "test_coverage": f"Couverture de tests insuffisante pour {kind}. Augmente fiabilité.",
    }
    return reasons.get(issue_type, f"Issue détectée: {issue_type} dans {kind}")


def _identify_cross_impacts(node_id: str, file_path: str) -> List[str]:
    """Identify files/modules impacted by changes to this node."""
    # Simplified - in reality would use graph traversal
    impacts = []

    # Check if this is a core module (high impact)
    if "core/orchestration" in file_path:
        impacts.extend([
            "core/interface/repl.py",
            "nexus7.py",
            "tests/test_orchestration_v7.py",
        ])
    elif "core/drivers" in file_path:
        impacts.extend([
            "core/orchestration_v7.py",
            "core/execution/tool_executor.py",
        ])
    elif "core/execution" in file_path:
        impacts.extend([
            "core/orchestration_v7.py",
            "core/fsm/fsm_handlers.py",
        ])

    return impacts


def _get_verification_method(issue_type: str) -> str:
    """Get verification method for task type."""
    methods = {
        "missing_docstring": "Verify docstring exists via AST analysis or pytest --docstring-coverage",
        "missing_type_hint": "Run mypy --strict on modified file",
        "dead_import": "Run autoflake --check on modified file",
        "security_issue": "Run bandit security scan + manual security review",
        "complexity": "Run radon cc (cyclomatic complexity) to verify reduction",
        "test_coverage": "Run pytest --cov and verify coverage increased",
    }
    return methods.get(issue_type, "Manual code review + full test suite")


def run_deep_analysis() -> AnalysisResult:
    """Run comprehensive deep analysis using Meta GraphRAG."""
    print("=" * 80)
    print("NCM DEEP ANALYSIS - Meta GraphRAG Powered")
    print("=" * 80)

    # 1. Check Meta GraphRAG status
    print("\n[STEP 1] Checking Meta GraphRAG index status...")
    status = build_meta_graphrag_status()
    print(f"  Index status: {json.dumps(status, indent=2)}")

    # 2. Run multiple targeted queries
    print("\n[STEP 2] Running targeted Meta GraphRAG queries...")
    queries = []
    all_tasks = []

    # Query 1: Missing docstrings
    print("\n--- Query 1: Missing Docstrings ---")
    docstring_result = query_meta_graphrag(
        "functions and classes without docstrings",
        seed_limit=20,
        expansion_depth=1,
        expansion_limit=30,
    )
    queries.append(docstring_result)
    docstring_tasks = extract_tasks_from_chunks(
        docstring_result["seed_chunks"],
        issue_type="missing_docstring",
        priority="P2",
    )
    all_tasks.extend(docstring_tasks)
    print(f"  > Generated {len(docstring_tasks)} docstring tasks")

    # Query 2: Type hints missing
    print("\n--- Query 2: Missing Type Hints ---")
    typehint_result = query_meta_graphrag(
        "function parameters without type annotations",
        seed_limit=20,
        expansion_depth=1,
        expansion_limit=30,
    )
    queries.append(typehint_result)
    typehint_tasks = extract_tasks_from_chunks(
        typehint_result["seed_chunks"],
        issue_type="missing_type_hint",
        priority="P2",
    )
    all_tasks.extend(typehint_tasks)
    print(f"  > Generated {len(typehint_tasks)} type hint tasks")

    # Query 3: Security issues
    print("\n--- Query 3: Security Issues ---")
    security_result = query_meta_graphrag(
        "security vulnerabilities hardcoded secrets authentication authorization",
        seed_limit=15,
        expansion_depth=2,
        expansion_limit=20,
    )
    queries.append(security_result)
    security_tasks = extract_tasks_from_chunks(
        security_result["seed_chunks"],
        issue_type="security_issue",
        priority="P0",
    )
    all_tasks.extend(security_tasks)
    print(f"  > Generated {len(security_tasks)} security tasks")

    # Query 4: Complex functions (god functions)
    print("\n--- Query 4: High Complexity Functions ---")
    complexity_result = query_meta_graphrag(
        "large functions high complexity cyclomatic",
        seed_limit=10,
        expansion_depth=2,
        expansion_limit=15,
    )
    queries.append(complexity_result)
    complexity_tasks = extract_tasks_from_chunks(
        complexity_result["seed_chunks"],
        issue_type="complexity",
        priority="P1",
    )
    all_tasks.extend(complexity_tasks)
    print(f"  > Generated {len(complexity_tasks)} complexity tasks")

    # Query 5: Test coverage gaps
    print("\n--- Query 5: Test Coverage Gaps ---")
    test_result = query_meta_graphrag(
        "functions without test coverage untested code",
        seed_limit=15,
        expansion_depth=1,
        expansion_limit=20,
    )
    queries.append(test_result)
    test_tasks = extract_tasks_from_chunks(
        test_result["seed_chunks"],
        issue_type="test_coverage",
        priority="P1",
    )
    all_tasks.extend(test_tasks)
    print(f"  > Generated {len(test_tasks)} test coverage tasks")

    # 3. Generate reports
    print("\n[STEP 3] Generating Meta GraphRAG reports...")
    reports = build_meta_graphrag_reports(
        entrypoints=["core/orchestration_v7.py", "core/hive_mind/pipeline.py"],
        include_content=False,
    )
    print(f"  Reports generated:")
    for report_name, report_path in reports.get("paths", {}).items():
        print(f"    - {report_name}: {report_path}")

    # 4. Count unique files
    unique_files = set(task.file_path for task in all_tasks)

    # 5. Generate summary
    summary = f"""
NEXUS Deep Analysis Summary
============================

Meta GraphRAG Index Status:
- Total chunks: {status.get('chunks', 0)}
- Total nodes: {status.get('nodes', 0)}
- Vector entries: {status.get('vector_entries', 0)}

Analysis Results:
- Total files analyzed: {len(unique_files)}
- Total tasks generated: {len(all_tasks)}

Task Breakdown by Priority:
- P0 (Critical): {sum(1 for t in all_tasks if t.priority == 'P0')} tasks
- P1 (High): {sum(1 for t in all_tasks if t.priority == 'P1')} tasks
- P2 (Medium): {sum(1 for t in all_tasks if t.priority == 'P2')} tasks

Task Breakdown by Type:
- Missing docstrings: {len(docstring_tasks)} tasks
- Missing type hints: {len(typehint_tasks)} tasks
- Security issues: {len(security_tasks)} tasks
- High complexity: {len(complexity_tasks)} tasks
- Test coverage gaps: {len(test_tasks)} tasks

Queries Performed: {len(queries)}

Next Steps:
1. Review generated task list in ncm_deep_analysis_output.json
2. Prioritize P0 tasks (security) for immediate action
3. Use NCM pilot to execute tasks in batches
4. Implement verification loop for each completed task
"""

    return AnalysisResult(
        meta_graphrag_status=status,
        queries_performed=queries,
        tasks=all_tasks,
        total_files=len(unique_files),
        total_tasks=len(all_tasks),
        summary=summary,
    )


def save_analysis_results(result: AnalysisResult, output_file: Path):
    """Save analysis results to JSON file."""
    output = {
        "meta_graphrag_status": result.meta_graphrag_status,
        "queries_performed": result.queries_performed,
        "tasks": [asdict(task) for task in result.tasks],
        "total_files": result.total_files,
        "total_tasks": result.total_tasks,
        "summary": result.summary,
    }

    output_file.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OUTPUT] Analysis results saved to: {output_file}")


def generate_verification_loop_report(tasks: List[Task], output_file: Path):
    """
    Generate verification loop report (boucle de vérification agentique).

    This report provides a systematic approach to verify each task's completion.
    """
    lines = [
        "# NEXUS NCM - Boucle de Vérification Agentique",
        "",
        "Ce rapport décrit la procédure de vérification pour chaque tâche NCM.",
        "",
        "## Principe",
        "",
        "Chaque tâche doit passer par 3 étapes de vérification:",
        "1. **Vérification Syntaxique** - Le code est syntaxiquement correct",
        "2. **Vérification Sémantique** - Le code fait ce qu'il est censé faire",
        "3. **Vérification d'Impact** - Les changements n'ont pas cassé d'autres parties",
        "",
        "## Méthode de Vérification par Type de Tâche",
        "",
    ]

    # Group tasks by type
    tasks_by_type = {}
    for task in tasks:
        if task.issue_type not in tasks_by_type:
            tasks_by_type[task.issue_type] = []
        tasks_by_type[task.issue_type].append(task)

    for issue_type, type_tasks in tasks_by_type.items():
        lines.append(f"### {issue_type.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Tâches concernées:** {len(type_tasks)}")
        lines.append("")
        lines.append(f"**Méthode de vérification:** {type_tasks[0].verification_method}")
        lines.append("")
        lines.append("**Étapes de vérification:**")
        lines.append("")

        if issue_type == "missing_docstring":
            lines.extend([
                "1. Exécuter `python -c \"import ast; tree = ast.parse(open('FILE').read()); print(ast.get_docstring(tree))\"`",
                "2. Vérifier que la docstring existe et suit le format Google Style",
                "3. Vérifier que tous les paramètres sont documentés",
                "4. Exécuter les tests du module: `pytest tests/test_MODULE.py -v`",
                "",
            ])
        elif issue_type == "missing_type_hint":
            lines.extend([
                "1. Exécuter `mypy FILE --strict`",
                "2. Vérifier qu'il n'y a pas d'erreurs de type",
                "3. Vérifier que l'IDE (VSCode/PyCharm) n'affiche pas d'avertissements",
                "4. Exécuter les tests: `pytest tests/test_MODULE.py -v`",
                "",
            ])
        elif issue_type == "security_issue":
            lines.extend([
                "1. Exécuter `bandit -r FILE` pour scan de sécurité",
                "2. Revue manuelle du code par un expert sécurité",
                "3. Vérifier que les secrets ne sont plus hardcodés",
                "4. Exécuter tous les tests de sécurité: `pytest tests/test_security.py -v`",
                "5. Vérifier les impacts croisés (voir section ci-dessous)",
                "",
            ])
        elif issue_type == "complexity":
            lines.extend([
                "1. Exécuter `radon cc FILE` pour mesurer la complexité cyclomatique",
                "2. Vérifier que la complexité a diminué (< 10 idéalement)",
                "3. Exécuter les tests du module: `pytest tests/test_MODULE.py -v`",
                "4. Revue de code pour vérifier la lisibilité",
                "",
            ])
        elif issue_type == "test_coverage":
            lines.extend([
                "1. Exécuter `pytest --cov=MODULE --cov-report=term-missing`",
                "2. Vérifier que la couverture a augmenté",
                "3. Vérifier que les nouveaux tests passent",
                "4. Exécuter l'ensemble de la suite de tests: `pytest tests/ -v`",
                "",
            ])
        else:
            lines.extend([
                "1. Vérifier manuellement le changement",
                "2. Exécuter les tests concernés",
                "3. Vérifier les impacts croisés",
                "",
            ])

        # Sample tasks
        lines.append(f"**Exemples de tâches (3 premières):**")
        lines.append("")
        for task in type_tasks[:3]:
            lines.append(f"- `{task.task_id}`: {task.file_path}:{task.line_numbers}")
            lines.append(f"  - Raison: {task.reason}")
            if task.cross_impacts:
                lines.append(f"  - Impacts: {', '.join(task.cross_impacts[:3])}")
            lines.append("")

    # Cross-impact verification section
    lines.extend([
        "## Vérification des Impacts Croisés",
        "",
        "Pour chaque tâche, vérifier que les modules suivants ne sont pas cassés:",
        "",
    ])

    # Collect all cross-impacts
    all_impacts = set()
    for task in tasks:
        all_impacts.update(task.cross_impacts)

    for impact in sorted(all_impacts):
        lines.append(f"- `{impact}`")

    lines.extend([
        "",
        "**Méthode:**",
        "1. Après chaque modification, exécuter: `pytest tests/test_[MODULE].py -v`",
        "2. Si tests échouent, analyser la cause racine",
        "3. Si nécessaire, ajuster les tests ou la modification",
        "",
    ])

    # Final verification
    lines.extend([
        "## Vérification Globale Finale",
        "",
        "Après avoir complété toutes les tâches:",
        "",
        "1. **Test Suite Complète:**",
        "   ```bash",
        "   pytest tests/ -v --cov=core --cov-report=html",
        "   ```",
        "",
        "2. **Analyse Statique:**",
        "   ```bash",
        "   mypy core/ --strict",
        "   bandit -r core/",
        "   pylint core/ --rcfile=.pylintrc",
        "   ```",
        "",
        "3. **Vérification Manuelle:**",
        "   - Lancer NEXUS en mode interactif: `python nexus7.py`",
        "   - Exécuter quelques commandes de test",
        "   - Vérifier qu'il n'y a pas de régression",
        "",
        "4. **Documentation:**",
        "   - Vérifier que toute la documentation est à jour",
        "   - Générer les rapports finaux",
        "",
    ])

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OUTPUT] Verification loop report saved to: {output_file}")


def main():
    """Main entry point."""
    print("\n" + "=" * 80)
    print("NCM DEEP ANALYSIS - Starting...")
    print("=" * 80)

    try:
        # Run deep analysis
        result = run_deep_analysis()

        # Save results
        output_dir = NEXUS_ROOT / "workspace" / "ncm_analysis"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "ncm_deep_analysis_output.json"
        save_analysis_results(result, output_file)

        # Generate verification loop report
        verification_file = output_dir / "ncm_verification_loop.md"
        generate_verification_loop_report(result.tasks, verification_file)

        # Print summary
        print("\n" + "=" * 80)
        print(result.summary)
        print("=" * 80)

        print(f"\n[SUCCESS] Analysis complete!")
        print(f"  - Tasks JSON: {output_file}")
        print(f"  - Verification Report: {verification_file}")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Error during analysis: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
