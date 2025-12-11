"""
Miscellaneous Commands for NEXUS V7.

Handles /clear, /doctor, /reset, /mode, /pool-stats, /bootstrap, /specialize, /tutorial, /quickstart, /chat.
"""

from typing import Any
from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class ClearCommand(Command):
    """Clear console screen."""

    @property
    def name(self) -> str:
        return "/clear"

    @property
    def description(self) -> str:
        return "Clear console screen"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        context.console.clear()
        return CommandResult(CommandStatus.SUCCESS, "")



class DoctorCommand(Command):
    """Run system diagnostics."""

    @property
    def name(self) -> str:
        return "/doctor"

    @property
    def description(self) -> str:
        return "Run system diagnostics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        from core.meta.cli_inspector import CLIInspector

        context.console.print("🔍 Running diagnostics...")

        inspector = CLIInspector()
        gemini = inspector.inspect_gemini()
        claude = inspector.inspect_claude()

        results = {
            "gemini": gemini,
            "claude": claude,
            "workspace": context.config.workspace_path.exists(),
            "io_buffer": (context.config.workspace_path / "_IO_BUFFER").exists()
        }

        context.console.print_doctor_results(results)
        return CommandResult(CommandStatus.SUCCESS, "")


class ResetCommand(Command):
    """Reset orchestrator to IDLE."""

    @property
    def name(self) -> str:
        return "/reset"

    @property
    def description(self) -> str:
        return "Reset orchestrator to IDLE state"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        context.orchestrator.reset_to_idle()
        return CommandResult(CommandStatus.SUCCESS, "✓ Orchestrator reset to IDLE")


class ModeCommand(Command):
    """Change orchestrator mode."""

    @property
    def name(self) -> str:
        return "/mode"

    @property
    def description(self) -> str:
        return "Change orchestrator mode"

    @property
    def usage(self) -> str:
        return "/mode <mode_name>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        if args:
            context.orchestrator.blackboard["mode"] = args
            return CommandResult(CommandStatus.SUCCESS, f"✓ Mode changed to: {args}")
        else:
            return CommandResult(CommandStatus.INVALID_ARGS, "Usage: /mode <mode_name>")


class PoolStatsCommand(Command):
    """Show agent pool statistics."""

    @property
    def name(self) -> str:
        return "/pool-stats"

    @property
    def description(self) -> str:
        return "Show agent pool statistics"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        # Check if agent pool is available
        if not hasattr(context.orchestrator, 'agent_pool') or not context.orchestrator.agent_pool:
            context.console.print("\n⚠️  AgentMetrics disabled")
            context.console.print("   Set AGENT_METRICS=True in .env to enable")
            return CommandResult(CommandStatus.SUCCESS, "")

        pool = context.orchestrator.agent_pool
        stats = pool.get_pool_stats()

        context.console.print("\n" + "="*60)
        context.console.print("📊 AGENT POOL STATISTICS (DyLAN Metrics)")
        context.console.print("="*60)

        # Pool summary
        context.console.print(f"\nTotal Agents: {stats['agents']}")
        context.console.print(f"Total Invocations: {stats['total_invocations']}")
        context.console.print(f"Average Pool Importance: {stats['average_pool_importance']:.4f}")

        # Per-agent details
        agents_detail = stats.get('agents_detail', {})
        for agent_id, agent_data in agents_detail.items():
            context.console.print(f"\n{'─'*60}")
            context.console.print(f"🤖 Agent: {agent_id}")
            context.console.print(f"{'─'*60}")
            context.console.print(f"  Provider:       {agent_data['provider']}")
            context.console.print(f"  Model:          {agent_data['model']}")
            context.console.print(f"  Capabilities:   {', '.join(agent_data.get('capabilities', []))}")
            context.console.print(f"  Invocations:    {agent_data['invocation_count']}")
            context.console.print(f"  Avg Importance: {agent_data['average_importance']:.4f}")
            context.console.print(f"  Success Rate:   {agent_data['success_rate']:.1%}")

        # DyLAN formula explanation
        context.console.print(f"\n{'─'*60}")
        context.console.print("ℹ️  DyLAN Formula: importance = quality / (tokens/1000 + time)")
        context.console.print("   Higher importance = better quality/cost ratio")
        context.console.print("="*60 + "\n")
            
        return CommandResult(CommandStatus.SUCCESS, "")


class BootstrapCommand(Command):
    """Run AutoBootstrap to generate NEXUS.md."""

    @property
    def name(self) -> str:
        return "/bootstrap"

    @property
    def description(self) -> str:
        return "Run AutoBootstrap to generate NEXUS.md"

    @property
    def usage(self) -> str:
        return "/bootstrap [path]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        from core.bootstrap import AutoBootstrap
        from pathlib import Path

        # Parse path argument (default: current directory)
        if args.strip():
            project_path = Path(args.strip()).resolve()
        else:
            project_path = Path.cwd()

        if not project_path.exists():
            return CommandResult(CommandStatus.ERROR, f"Path does not exist: {project_path}")

        if not project_path.is_dir():
            return CommandResult(CommandStatus.ERROR, f"Path is not a directory: {project_path}")

        context.console.print(f"🔍 Analyzing project: {project_path}")

        try:
            # Run analysis
            bootstrap = AutoBootstrap(project_path)
            analysis = bootstrap.analyze()

            # Display results
            context.console.print("\n📊 Analysis Results:")
            context.console.print(f"   Project: {analysis.project_name}")
            context.console.print(f"   Languages: {', '.join(analysis.languages) or 'None detected'}")
            context.console.print(f"   Frameworks: {', '.join(analysis.frameworks) or 'None detected'}")
            context.console.print(f"   Databases: {', '.join(analysis.databases) or 'None detected'}")
            context.console.print(f"   Tools: {', '.join(analysis.tools) or 'None detected'}")
            context.console.print(f"   Has tests: {'Yes' if analysis.has_tests else 'No'}")
            context.console.print(f"   Has docs: {'Yes' if analysis.has_docs else 'No'}")
            context.console.print(f"   Has CI: {'Yes' if analysis.has_ci else 'No'}")

            if analysis.commands:
                context.console.print(f"\n📝 Commands discovered:")
                for cmd, desc in list(analysis.commands.items())[:5]:
                    context.console.print(f"   {cmd}: {desc}")

            # Generate NEXUS.md
            nexus_md = bootstrap.generate_nexus_md(analysis)

            # Check if NEXUS.md already exists
            nexus_path = project_path / "NEXUS.md"
            if nexus_path.exists():
                existing_size = len(nexus_path.read_text(encoding='utf-8'))
                context.console.print(f"\n⚠️  NEXUS.md already exists at {nexus_path}")
                context.console.print(f"   Existing file size: {existing_size} characters")
                context.console.print(f"   New file size: {len(nexus_md)} characters")

                if existing_size > len(nexus_md) * 2:
                    context.console.print(f"\n   [bold red]WARNING: Existing file is much larger![/bold red]")
                    context.console.print(f"   The existing NEXUS.md may contain important documentation.")

                response = input("   Create backup and overwrite? (y/N): ").strip().lower()
                if response != 'y':
                    return CommandResult(CommandStatus.SUCCESS, "Cancelled.")

                # Create backup before overwriting
                backup_path = project_path / "NEXUS.md.bak"
                import shutil
                shutil.copy2(nexus_path, backup_path)
                context.console.print(f"   📦 Backup created: {backup_path}")

            # Save
            bootstrap.save(nexus_md)
            context.console.print(f"\n✅ Generated: {nexus_path}")
            context.console.print(f"   Size: {len(nexus_md)} characters")
            
            return CommandResult(CommandStatus.SUCCESS, "")

        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Bootstrap failed: {e}")


class SpecializeCommand(Command):
    """Create specialized NEXUS spinoff."""

    @property
    def name(self) -> str:
        return "/specialize"

    @property
    def description(self) -> str:
        return "Create specialized NEXUS spinoff"

    @property
    def usage(self) -> str:
        return "/specialize <mission_description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not args:
            return CommandResult(CommandStatus.INVALID_ARGS, "Usage: /specialize <mission_description>")

        from core.evolution.lineage import load_lineage, get_current_parent
        import shutil
        from datetime import datetime
        import json
        from pathlib import Path

        context.console.print("\n" + "="*60)
        context.console.print("🧬 SPECIALIZATION CYCLE STARTED")
        context.console.print("="*60)
        
        try:
            # We need nexus_root. In repl it was self.nexus_root.
            # Here we can infer it from workspace_path.
            # Assuming workspace_path is .../NEXUS_V7_CHRYSALIS/workspace
            # nexus_root should be .../NEXUS_V7_CHRYSALIS
            nexus_root = context.config.workspace_path.parent
            
            lineage = load_lineage(context.config.workspace_path)
            parent = get_current_parent(lineage)
            parent_id = parent["id"]
            
            parent_path = nexus_root

            # 1. Brainstorm mutations
            mutations = self._brainstorm_spinoff_with_ais(context, parent_id, parent_path, args)
            
            # 2. Create Spinoff ID
            # Sanitize mission string for folder name
            mission_slug = "".join(c if c.isalnum() else "_" for c in args)[:30].upper()
            spinoff_id = f"NEXUS_SPECIALIST_{mission_slug}_{datetime.now().strftime('%Y%m%d')}"
            
            context.console.print(f"\n{'─'*60}")
            context.console.print(f"Creating Specialist: {spinoff_id}")
            context.console.print(f"{'─'*60}")

            # 3. Create Directory
            child_dir = parent_path.parent / "GENERATION_ACTIVE" / spinoff_id
            if child_dir.exists():
                shutil.rmtree(child_dir)
            child_dir.mkdir(parents=True, exist_ok=True)

            # 4. Copy Parent
            shutil.copytree(
                parent_path,
                child_dir,
                ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '.nexus', 'workspace', '.git'
                ),
                dirs_exist_ok=True
            )
            context.console.print(f"✓ Copied parent base")

            # FIX: Copy KERNEL.py from project root (alignment file)
            project_root = parent_path.parent
            kernel_path = project_root / "KERNEL.py"
            kernel_hash_path = project_root / "KERNEL_HASH.txt"
            if kernel_path.exists():
                shutil.copy2(kernel_path, child_dir / "KERNEL.py")
                if kernel_hash_path.exists():
                    shutil.copy2(kernel_hash_path, child_dir / "KERNEL_HASH.txt")
                context.console.print(f"✓ Copied KERNEL.py (alignment file)")

            # FIX: Create workspace directories required by drivers
            child_workspace = child_dir / "workspace"
            child_workspace.mkdir(exist_ok=True)
            (child_workspace / "_IO_BUFFER").mkdir(exist_ok=True)
            (child_workspace / ".nexus").mkdir(exist_ok=True)
            (child_workspace / "logs").mkdir(exist_ok=True)
            context.console.print(f"✓ Created workspace directories")

            # 5. Apply Mutations
            for mutation in mutations:
                target_file = child_dir / mutation['file']
                if target_file.exists():
                    original = target_file.read_text(encoding='utf-8')
                    updated = original + "\n\n" + mutation['change']
                    target_file.write_text(updated, encoding='utf-8')
                    context.console.print(f"✓ Applied mutation to {mutation['file']}")
                else:
                    context.console.print(f"⚠️ File not found: {mutation['file']}")

            # 6. Spinoff Certificate
            cert = {
                "id": spinoff_id,
                "type": "SPECIALIST",
                "mission": args,
                "parent": parent_id,
                "created_at": datetime.now().isoformat(),
                "mutations": mutations
            }
            (child_dir / "SPINOFF_CERTIFICATE.json").write_text(json.dumps(cert, indent=2), encoding='utf-8')
            
            context.console.print("\n" + "="*60)
            context.console.print(f"✅ SPECIALIST CREATED: {spinoff_id}")
            context.console.print(f"Location: GENERATION_ACTIVE/{spinoff_id}")
            context.console.print("To use: cd into directory and run nexus7.py")
            context.console.print("="*60 + "\n")
            
            return CommandResult(CommandStatus.SUCCESS, "")

        except Exception as e:
            import traceback
            traceback.print_exc()
            return CommandResult(CommandStatus.ERROR, f"Specialization failed: {e}")

    def _brainstorm_spinoff_with_ais(self, context: CommandContext, parent_id: str, parent_path: Any, mission: str) -> list:
        """
        Collaborative brainstorming for SPECIALIZATION.
        Gemini+Claude design a specific child optimized for a mission.
        """
        from core.fsm.states import OrchestratorState
        from core.utils.json_extractor import extract_json_safe as robust_extract_json
        from core.prompts import load_prompt

        context.console.print("\n" + "="*60)
        context.console.print(f"🚀 MISSION SPECIALIZATION: {mission}")
        context.console.print("="*60)
        context.console.print(f"Gemini + Claude will now design a Specialist NEXUS\n")

        # CLEAR HISTORY
        context.console.print("🧹 Clearing short-term memory for focused brainstorming...")
        context.orchestrator.blackboard["recent_history"] = []
        context.orchestrator.memory.save_to_disk()

        # V7.5 HIVE MIND: Load prompt with includes resolved
        try:
            brainstorm_task = load_prompt("specialization_mission", {
                "mission": mission
            })
        except FileNotFoundError as e:
            context.console.print_error(f"Missing prompt file: {e}")
            return []

        # Switch to EVOLUTION_BRAINSTORM mode (reused for debate)
        context.orchestrator._transition_to(OrchestratorState.EVOLUTION_BRAINSTORM)
        context.console.print(f"[FSM] Mode: MISSION_SPECIALIZATION (via EVOLUTION_BRAINSTORM)\n")

        # Start brainstorming
        result = context.orchestrator.process_turn(brainstorm_task)
        context.console.display_result(result)

        # Loop
        max_iterations = 30
        iterations = 0

        while result["state"] not in ["IDLE", "ERROR", "PANIC"] and iterations < max_iterations:
            result = context.orchestrator.process_turn()
            context.console.display_result(result)
            iterations += 1
            if result.get("finished"):
                break

        context.orchestrator._transition_to(OrchestratorState.IDLE)

        # Extract JSON
        final_content = result.get('output') or ''
        
        # V7.5 HIVE MIND: Use robust extractor
        proposals, _ = robust_extract_json(final_content, verbose=True)
        
        if not proposals:
             # Fallback retry logic could be added here, for now we raise
             raise ValueError("Failed to extract specialization plan")

        return proposals


class TutorialCommand(Command):
    """Run interactive tutorial."""

    @property
    def name(self) -> str:
        return "/tutorial"

    @property
    def description(self) -> str:
        return "Run interactive tutorial"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        from core.interface.tutorial import InteractiveTutorial

        tutorial = InteractiveTutorial()
        tutorial.run(context.console.console.print)
        return CommandResult(CommandStatus.SUCCESS, "")


class QuickstartCommand(Command):
    """Show quickstart guide."""

    @property
    def name(self) -> str:
        return "/quickstart"

    @property
    def description(self) -> str:
        return "Show quickstart guide"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        from core.interface.tutorial import InteractiveTutorial

        tutorial = InteractiveTutorial()
        context.console.console.print(tutorial.get_quick_start())
        return CommandResult(CommandStatus.SUCCESS, "")


class ChatCommand(Command):
    """Toggle chat mode."""

    @property
    def name(self) -> str:
        return "/chat"

    @property
    def description(self) -> str:
        return "Toggle chat mode"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        current = context.orchestrator.blackboard.get("chat_mode", False)
        new_mode = not current
        context.orchestrator.blackboard["chat_mode"] = new_mode

        if new_mode:
            context.console.print("\n💬 [cyan]Chat mode ENABLED[/cyan]")
            context.console.print("   Tools are disabled. Use /chat to re-enable.\n")
        else:
            context.console.print("\n🔧 [green]Chat mode DISABLED[/green]")
            context.console.print("   Full agent capabilities restored.\n")
            
        return CommandResult(CommandStatus.SUCCESS, "")

