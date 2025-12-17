# NEXUS Documentation Generator - CLI Entry Point
"""
Command-line interface for the documentation generator.

Usage:
    python -m tools.doc_generator generate --all
    python -m tools.doc_generator generate --path core/swarm/
    python -m tools.doc_generator audit --output audit/
    python -m tools.doc_generator check --fail-on critical --fail-on high
    python -m tools.doc_generator drift --fail-if-outdated
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .config import DocGeneratorConfig, Severity


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="nexus-doc-generator",
        description="NEXUS Documentation Generator - Automated docs with Mermaid diagrams",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate documentation")
    gen_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    gen_parser.add_argument(
        "--all",
        action="store_true",
        help="Generate documentation for entire repository",
    )
    gen_parser.add_argument(
        "--path",
        type=Path,
        help="Generate documentation for specific path",
    )
    gen_parser.add_argument(
        "--output-readmes",
        action="store_true",
        default=True,
        help="Generate README.md files",
    )
    gen_parser.add_argument(
        "--output-mermaid",
        type=Path,
        help="Output directory for Mermaid diagrams",
    )
    gen_parser.add_argument(
        "--detect-new",
        action="store_true",
        help="Detect and document new folders since last commit",
    )

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Run audit and detect issues")
    audit_parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for audit reports",
    )
    audit_parser.add_argument(
        "--json-output",
        type=Path,
        help="Output path for JSON issues file",
    )

    # Check command
    check_parser = subparsers.add_parser("check", help="Check for issues (CI mode)")
    check_parser.add_argument(
        "--fail-on",
        action="append",
        choices=["critical", "high", "medium", "low"],
        help="Fail if issues of this severity are found (can be repeated)",
    )

    # Drift command
    drift_parser = subparsers.add_parser("drift", help="Check documentation drift")
    drift_parser.add_argument(
        "--fail-if-outdated",
        action="store_true",
        help="Fail if documentation is outdated",
    )

    return parser


def cmd_generate(args: argparse.Namespace, config: DocGeneratorConfig) -> int:
    """Execute the generate command."""
    from .scanner.repo_scanner import RepoScanner
    from .analyzer.python_analyzer import PythonAnalyzer
    from .analyzer.dependency_graph import DependencyGraphBuilder
    from .generators.readme_generator import ReadmeGenerator
    from .generators.mermaid_generator import MermaidGenerator
    from .generators.aggregator import DocumentAggregator
    from .generators.global_views import GlobalViewGenerator

    print(f"[nexus-doc-generator] Generating documentation...")
    print(f"  Repository: {config.repo_root}")

    # Phase 1: Scan repository
    print("\n[Phase 1] Scanning repository...")
    scanner = RepoScanner(config)
    folders = scanner.scan()
    print(f"  Found {len(folders)} folders")

    if args.detect_new:
        new_folders = scanner.detect_new_folders()
        if new_folders:
            print(f"  Detected {len(new_folders)} new folders since last commit")

    # Phase 2: Analyze code
    print("\n[Phase 2] Analyzing code...")
    analyzer = PythonAnalyzer(config)
    modules = []
    for folder in folders:
        for py_file in folder.python_files:
            try:
                module_info = analyzer.analyze_file(py_file)
                modules.append(module_info)
            except Exception as e:
                if config.verbose:
                    print(f"  Warning: Could not analyze {py_file}: {e}")

    print(f"  Analyzed {len(modules)} Python modules")

    # Build dependency graph
    graph_builder = DependencyGraphBuilder(config)
    dep_graph = graph_builder.build(modules)
    print(f"  Built dependency graph: {dep_graph.number_of_nodes()} nodes, {dep_graph.number_of_edges()} edges")

    # Phase 3: Generate documentation
    print("\n[Phase 3] Generating documentation...")

    if config.generate_readmes:
        readme_gen = ReadmeGenerator(config)
        readme_count = 0

        # V13.0: Bottom-up traversal (deepest directories first)
        # This ensures child READMEs are generated before parents
        sorted_folders = sorted(
            folders,
            key=lambda f: len(f.path.parts),
            reverse=True  # Deepest first
        )

        if config.verbose:
            print("  [V13.0] Using bottom-up traversal (leaves -> root)")

        for folder in sorted_folders:
            if folder.is_python_package or folder.python_files:
                try:
                    readme_gen.generate_for_folder(folder, modules, dep_graph)
                    readme_count += 1
                except Exception as e:
                    if config.verbose:
                        print(f"  Warning: Could not generate README for {folder.path}: {e}")
        print(f"  Generated {readme_count} README files")

    if config.generate_mermaid:
        mermaid_gen = MermaidGenerator(config)
        mermaid_gen.generate_all(modules, dep_graph)
        print(f"  Generated Mermaid diagrams in {config.mermaid_output_dir}")

    # Phase 4: Aggregate documentation
    print("\n[Phase 4] Aggregating documentation...")
    aggregator = DocumentAggregator(config)
    aggregator.aggregate(folders, modules)

    # Phase 5: Generate global views
    if config.generate_global_views:
        print("\n[Phase 5] Generating global views...")
        global_gen = GlobalViewGenerator(config)
        global_gen.generate(modules, dep_graph, folders)
        print(f"  Generated global architecture views")

    print("\n[nexus-doc-generator] Documentation generation complete!")
    return 0


def cmd_audit(args: argparse.Namespace, config: DocGeneratorConfig) -> int:
    """Execute the audit command."""
    from .scanner.repo_scanner import RepoScanner
    from .analyzer.python_analyzer import PythonAnalyzer
    from .validators.consistency_checker import ConsistencyChecker
    from .validators.dead_code_detector import DeadCodeDetector
    from .validators.bug_pattern_detector import BugPatternDetector
    from .reporters.audit_reporter import AuditReporter

    print(f"[nexus-doc-generator] Running audit...")

    # Scan and analyze
    scanner = RepoScanner(config)
    folders = scanner.scan()

    analyzer = PythonAnalyzer(config)
    modules = []
    for folder in folders:
        for py_file in folder.python_files:
            try:
                module_info = analyzer.analyze_file(py_file)
                modules.append(module_info)
            except Exception:
                pass

    # Run validators
    all_issues = []

    print("  Checking consistency...")
    consistency = ConsistencyChecker(config)
    all_issues.extend(consistency.check(modules))

    print("  Detecting dead code...")
    dead_code = DeadCodeDetector(config)
    all_issues.extend(dead_code.detect(modules))

    print("  Detecting bug patterns...")
    bug_patterns = BugPatternDetector(config)
    for folder in folders:
        for py_file in folder.python_files:
            try:
                code = py_file.read_text(encoding="utf-8")
                all_issues.extend(bug_patterns.scan(str(py_file), code))
            except Exception:
                pass

    # Generate report
    output_dir = args.output or config.audit_output_dir
    reporter = AuditReporter(config)
    reporter.generate(all_issues, output_dir)

    # JSON output
    if args.json_output:
        json_path = args.json_output
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([issue.to_dict() for issue in all_issues], f, indent=2)
        print(f"  JSON output: {json_path}")

    # Summary
    critical = len([i for i in all_issues if i.severity == Severity.CRITICAL])
    high = len([i for i in all_issues if i.severity == Severity.HIGH])
    medium = len([i for i in all_issues if i.severity == Severity.MEDIUM])
    low = len([i for i in all_issues if i.severity == Severity.LOW])

    print(f"\n  Issues found:")
    print(f"    Critical: {critical}")
    print(f"    High: {high}")
    print(f"    Medium: {medium}")
    print(f"    Low: {low}")
    print(f"  Total: {len(all_issues)}")

    return 0


def cmd_check(args: argparse.Namespace, config: DocGeneratorConfig) -> int:
    """Execute the check command (CI mode)."""
    from .scanner.repo_scanner import RepoScanner
    from .analyzer.python_analyzer import PythonAnalyzer
    from .validators.consistency_checker import ConsistencyChecker
    from .validators.dead_code_detector import DeadCodeDetector
    from .validators.bug_pattern_detector import BugPatternDetector

    print(f"[nexus-doc-generator] Running CI checks...")

    # Scan and analyze
    scanner = RepoScanner(config)
    folders = scanner.scan()

    analyzer = PythonAnalyzer(config)
    modules = []
    for folder in folders:
        for py_file in folder.python_files:
            try:
                module_info = analyzer.analyze_file(py_file)
                modules.append(module_info)
            except Exception:
                pass

    # Run validators
    all_issues = []

    consistency = ConsistencyChecker(config)
    all_issues.extend(consistency.check(modules))

    dead_code = DeadCodeDetector(config)
    all_issues.extend(dead_code.detect(modules))

    bug_patterns = BugPatternDetector(config)
    for folder in folders:
        for py_file in folder.python_files:
            try:
                code = py_file.read_text(encoding="utf-8")
                all_issues.extend(bug_patterns.scan(str(py_file), code))
            except Exception:
                pass

    # Check thresholds
    fail_levels = args.fail_on or []

    failed = False
    for level in fail_levels:
        count = len([i for i in all_issues if i.severity == level])
        if count > 0:
            print(f"  FAIL: {count} {level} issues found")
            failed = True

    if failed:
        print("\n[nexus-doc-generator] CI check FAILED")
        return 1

    print("\n[nexus-doc-generator] CI check PASSED")
    return 0


def cmd_drift(args: argparse.Namespace, config: DocGeneratorConfig) -> int:
    """Execute the drift command."""
    from .validators.doc_drift_detector import DocDriftDetector

    print(f"[nexus-doc-generator] Checking documentation drift...")

    detector = DocDriftDetector(config)
    drift_issues = detector.detect()

    if drift_issues:
        print(f"  Found {len(drift_issues)} outdated documentation files:")
        for issue in drift_issues[:10]:  # Show first 10
            print(f"    - {issue.file}: {issue.message}")

        if args.fail_if_outdated:
            print("\n[nexus-doc-generator] Drift check FAILED")
            return 1
    else:
        print("  All documentation is up to date!")

    print("\n[nexus-doc-generator] Drift check PASSED")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    # Create configuration
    config = DocGeneratorConfig.from_repo(args.repo_root)
    config.verbose = getattr(args, 'verbose', False)

    # Execute command
    if args.command == "generate":
        return cmd_generate(args, config)
    elif args.command == "audit":
        return cmd_audit(args, config)
    elif args.command == "check":
        return cmd_check(args, config)
    elif args.command == "drift":
        return cmd_drift(args, config)

    return 1


if __name__ == "__main__":
    sys.exit(main())
