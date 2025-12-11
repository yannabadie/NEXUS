"""
Evolution Commands for NEXUS V7.

Handles /evolve, /spawn, /agents, /review, /evolve-status.
"""

from typing import List
from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus

class EvolveCommand(Command):
    """Trigger evolution cycle."""

    @property
    def name(self) -> str:
        return "/evolve"

    @property
    def description(self) -> str:
        return "Trigger evolution cycle to generate child agents"

    @property
    def usage(self) -> str:
        return "/evolve [child_count]"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        # Parse child count
        child_count = int(args) if args and args.isdigit() else 3
        
        # Delegate to REPL's run_evolve for now (complex logic)
        # In a full refactor, run_evolve logic should move to EvolutionManager
        try:
            repl.run_evolve(child_count=child_count)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Evolution failed: {e}")


class EvolveStatusCommand(Command):
    """Show evolution status."""

    @property
    def name(self) -> str:
        return "/evolve-status"

    @property
    def description(self) -> str:
        return "Show status of current evolution cycle"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        repl = context.extras.get('repl')
        if not repl:
            return CommandResult(CommandStatus.ERROR, "REPL instance not found in context")

        try:
            repl.show_evolve_status()
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Failed to show status: {e}")


class SpawnCommand(Command):
    """Spawn a specialized agent."""

    @property
    def name(self) -> str:
        return "/spawn"

    @property
    def description(self) -> str:
        return "Spawn a specialized agent for a specific role"

    @property
    def usage(self) -> str:
        return "/spawn <role description>"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        if not args.strip():
            return CommandResult(CommandStatus.INVALID_ARGS, "Usage: /spawn <role>")

        try:
            self._spawn_agent(context, args)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Spawn failed: {e}")

    def _spawn_agent(self, context: CommandContext, role: str):
        """
        Spawn a specialized agent via EVOLUTION_BRAINSTORM (/spawn command).
        """
        import re
        import uuid as uuid_module
        from core.telemetry import BudgetExceededError

        # 0a. Budget check
        try:
            if context.orchestrator.telemetry:
                context.orchestrator.telemetry.enforce_budget()
        except BudgetExceededError as e:
            context.console.print_error(f"Cannot spawn: Budget exceeded (${e.spent:.2f}/${e.limit:.2f})")
            context.console.print("Use /budget reset to unlock.")
            return

        # Create agents directory
        agents_dir = context.config.workspace_path / "agents"
        agents_dir.mkdir(exist_ok=True)

        # Create slug from role
        role_slug = re.sub(r'[^a-z0-9]+', '_', role.lower()).strip('_')
        agent_dir = agents_dir / role_slug

        # 0b. Existence check
        if agent_dir.exists():
            context.console.print_error(f"Agent '{role_slug}' already exists!")
            context.console.print(f"Path: {agent_dir}")
            context.console.print("\nOptions:")
            context.console.print(f"  1. Delete existing and respawn: /spawn-force {role}")
            context.console.print(f"  2. Use different name: /spawn {role}_v2")
            return

        context.console.print("\n" + "="*60)
        context.console.print(f"🏭 SPAWNING AGENT: {role}")
        context.console.print("="*60)

        # STEP 2a: IDENTITY MANAGEMENT
        agent_uuid = str(uuid_module.uuid4())
        context.console.print(f"   UUID: {agent_uuid[:8]}...")

        # STEP 2c: DOMAIN DETECTION
        domains = self._detect_domains_from_role(role)
        context.console.print(f"   Domains: {domains if domains else ['general']}")

        try:
            # Create agent directory structure
            agent_dir.mkdir(parents=True)
            (agent_dir / "workspace").mkdir()

            # STEP 2b: BRAINSTORM SYSTEM PROMPT
            context.console.print("\n🧠 Brainstorming specialized prompt...")
            context.console.print("   (Gemini + Claude collaboration)")

            generated_prompt = self._brainstorm_agent_prompt(context, role, agent_uuid, domains)

            # STEP 2d: VALIDATION
            if generated_prompt:
                hallucinated_tools = self._validate_prompt_tools(generated_prompt)
                if hallucinated_tools:
                    context.console.print(f"   ⚠️ Warning: Prompt references unknown tools: {hallucinated_tools}")

            # REDTEAM PROMPT VALIDATION
            if generated_prompt and getattr(context.config, 'redteam_spawn_enabled', False):
                try:
                    from core.governance.red_team.prompt_validator import SpawnPromptValidator
                    validator = SpawnPromptValidator()
                    validation_result = validator.validate(generated_prompt)

                    if not validation_result.passed:
                        context.console.print(f"   ⚠️ RedTeam Check: FAILED (score: {validation_result.score:.2f})")
                        for warning in validation_result.warnings[:3]:
                            context.console.print(f"      - {warning}")

                        if getattr(context.config, 'redteam_spawn_block_on_fail', False):
                            context.console.print("   ❌ Spawn BLOCKED (REDTEAM_SPAWN_BLOCK=True)")
                            raise ValueError(f"RedTeam validation failed: {validation_result.risk_level.value}")
                        else:
                            context.console.print("   ⚠️ Proceeding despite warnings (REDTEAM_SPAWN_BLOCK=False)")
                    else:
                        context.console.print(f"   ✅ RedTeam Check: PASSED (score: {validation_result.score:.2f})")
                except ImportError:
                    context.console.print("   ⚠️ RedTeam validator not available")

            # Fallback
            if not generated_prompt:
                context.console.print("   ⚠️ Brainstorm failed, using static template")
                generated_prompt = self._static_agent_template(role, agent_uuid, domains)

            # EXTRACT INFERENCE CONFIG
            inference_config = self._extract_inference_config(context, generated_prompt)
            if inference_config:
                context.console.print(f"   Model: {inference_config['provider']}/{inference_config['model']}")
            else:
                # Default if missing
                inference_config = {
                    "provider": "claude",
                    "model": "claude-sonnet-4-5-20250929",  # Default V8.4
                    "reasoning": None
                }
                context.console.print("   ⚠️ Inference config not found, using default (Claude Sonnet)")

            # SAVE ARTIFACTS
            # 1. BIRTH_CERTIFICATE.json
            birth_cert = {
                "uuid": agent_uuid,
                "role": role,
                "created_at": __import__("datetime").datetime.now().isoformat(),
                "parent_version": "8.5.1",
                "inference": inference_config,
                "domains": domains,
                "prompt_hash": f"sha256:{hash(generated_prompt)}"
            }
            
            import json
            (agent_dir / "BIRTH_CERTIFICATE.json").write_text(json.dumps(birth_cert, indent=2), encoding='utf-8')

            # 2. system_prompt.md
            (agent_dir / "system_prompt.md").write_text(generated_prompt, encoding='utf-8')

            # 3. Register in AgentPool
            if context.orchestrator.agent_pool:
                from core.bootstrap.agent_loader import SpawnedAgentLoader
                loader = SpawnedAgentLoader(context.config.workspace_path)
                # We need to reload to find the new agent
                new_agents = loader.discover_spawned_agents()
                for profile in new_agents:
                    if profile.agent_id == role_slug:
                        context.orchestrator.agent_pool.register_agent(profile)
                        context.console.print(f"   ✓ Registered in AgentPool: {profile.agent_id}")
                        break

            context.console.print(f"\n✅ AGENT SPAWNED: {role_slug}")
            context.console.print(f"   Location: workspace/agents/{role_slug}")

        except Exception as e:
            # Cleanup on failure
            import shutil
            if agent_dir.exists():
                shutil.rmtree(agent_dir)
            raise e

    def _detect_domains_from_role(self, role: str) -> list:
        role_lower = role.lower()
        domains = []
        domain_keywords = {
            "coding": ["python", "java", "javascript", "typescript", "rust", "go", "c++", "code", "developer", "programmer"],
            "data": ["sql", "database", "data", "analytics", "pandas", "numpy"],
            "devops": ["docker", "kubernetes", "k8s", "aws", "azure", "gcp", "cloud", "devops", "ci/cd"],
            "security": ["security", "pentest", "vulnerability", "audit", "crypto"],
            "web": ["web", "frontend", "backend", "api", "rest", "graphql"],
            "ml": ["ml", "machine learning", "ai", "deep learning", "neural", "model"],
            "research": ["research", "analyst", "analysis"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in role_lower for kw in keywords):
                domains.append(domain)
        return domains

    def _brainstorm_agent_prompt(self, context: CommandContext, role: str, agent_uuid: str, domains: list) -> str | None:
        from core.evolution.phases.brainstorm import BrainstormPhase
        from core.prompts import load_prompt

        def on_progress(msg: str, progress: float):
            context.console.print(f"   [{int(progress*100):3d}%] {msg}")

        try:
            try:
                task_template = load_prompt("spawn_brainstorm", {
                    "role": role,
                    "agent_uuid": agent_uuid,
                    "domains": ", ".join(domains) if domains else "general"
                })
            except FileNotFoundError:
                task_template = f"""
DESIGN TASK: Create a comprehensive System Prompt for a new NEXUS agent.

Role: {role}
UUID: {agent_uuid}
Detected Domains: {", ".join(domains) if domains else "general"}

REQUIREMENTS:
1. Define specific expertise boundaries (not vague)
2. List concrete operational constraints (libraries, patterns, security)
3. Define exact output formats and tone
4. Total length: 50-100 lines
5. Format: Markdown starting with '# {role}'

VALID NEXUS TOOLS (only reference these):
- read, write, edit, list_dir, bash, git
- web_search, web_fetch, glob, grep, todo_write
- read_file, write_file, edit_file (aliases)

DO NOT reference: execute_code, run_python, browser (don't exist)

OUTPUT:
Provide ONLY the final System Prompt. Start with '# {role}'.
"""
            phase = BrainstormPhase(
                context.orchestrator,
                context.config.workspace_path,
                progress_callback=on_progress
            )
            
            # Use parent_id from config or default
            result = phase.run(
                parent_id="NEXUS_V8.5.1",
                parent_path=context.config.workspace_path,
                mode="prompt",
                custom_task=task_template
            )

            if result.generated_prompt:
                return result.generated_prompt

            if result.errors:
                context.console.print(f"   Brainstorm errors: {result.errors}")
            return None

        except Exception as e:
            context.console.print(f"   Brainstorm exception: {e}")
            return None

    def _validate_prompt_tools(self, prompt: str) -> list:
        import re
        valid_tools = {
            "read", "write", "edit", "list_dir", "bash", "git",
            "web_search", "web_fetch", "glob", "grep", "todo_write",
            "read_file", "write_file", "edit_file",
            "mcp",
        }
        potential_tools = re.findall(r'`([a-z_]+)`', prompt.lower())
        hallucinated = []
        for tool in potential_tools:
            if tool not in valid_tools and not tool.startswith("mcp_") and not tool.startswith("agent_"):
                if tool not in {"true", "false", "none", "null", "json", "yaml", "md", "py"}:
                    hallucinated.append(tool)
        return list(set(hallucinated))

    def _static_agent_template(self, role: str, agent_uuid: str, domains: list) -> str:
        from datetime import datetime
        domains_str = ", ".join(domains) if domains else "general"
        return f"""# {role} - Specialized NEXUS Agent

## Identity
- UUID: {agent_uuid}
- Specialization: {domains_str}
- Created: {datetime.now().strftime("%Y-%m-%d")}
- Parent: NEXUS V8.5.1 HIVE MIND

## Mission
You are a specialized agent created for: **{role}**

Your expertise focuses on {domains_str} tasks within the NEXUS ecosystem.
Collaborate with other agents via Hybrid Swarm when complex tasks require
multiple perspectives.

## Expertise Boundaries
- Primary focus: {role}
- Detected domains: {domains_str}
- Use your specialization to provide deep, actionable insights

## Operational Constraints
- Follow NEXUS tool protocols
- Validate inputs before processing
- Report errors clearly with context
- Maintain session isolation

## Output Format
- Use clear, structured responses
- Code blocks with language hints
- Step-by-step explanations when appropriate

## Tool Preferences
- read, write, edit for file operations
- glob, grep for code search
- bash for system commands
- web_search, web_fetch for research

## Collaboration Protocol
- Respond to Swarm task assignments
- Share insights via structured messages
- Escalate complex issues to lead agent

## Limitations
- Stay within your specialization
- Defer to other specialists for out-of-domain tasks
- Do not hallucinate capabilities

## Alignment
You inherit NEXUS KERNEL alignment principles.
Creator: Yann Abadie
"""

    def _extract_inference_config(self, context: CommandContext, prompt: str) -> dict | None:
        import re
        inference_pattern = r'##\s*Inference\s+Configuration\s*\n(?:.*?\n)*?provider:\s*(\w+)\s*\n(?:.*?\n)*?model:\s*([^\n]+)'
        match = re.search(inference_pattern, prompt, re.IGNORECASE)

        if match:
            provider = match.group(1).lower().strip()
            model = match.group(2).strip()
            
            reasoning_pattern = r'reasoning:\s*([^\n]+)'
            reasoning_match = re.search(reasoning_pattern, prompt, re.IGNORECASE)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else None

            # Validate provider using registry if available
            # We can't easily access get_registry() here without circular imports or context
            # But we can check context.orchestrator.agent_pool if needed, 
            # or just rely on basic validation.
            # For now, let's trust the extraction but default to claude if weird.
            if provider not in ["claude", "gemini", "openai"]: # Basic check
                 context.console.print(f"   ⚠️ Unknown provider '{provider}', defaulting to claude")
                 provider = "claude"

            return {
                "provider": provider,
                "model": model,
                "reasoning": reasoning
            }
        return None


class AgentsCommand(Command):
    """List available agents."""

    @property
    def name(self) -> str:
        return "/agents"

    @property
    def description(self) -> str:
        return "List all available agents in the registry"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        try:
            self._list_agents(context)
            return CommandResult(CommandStatus.SUCCESS, "")
        except Exception as e:
            return CommandResult(CommandStatus.ERROR, f"Failed to list agents: {e}")

    def _list_agents(self, context: CommandContext):
        """List all spawned agents in workspace/agents/ (/agents command)."""
        agents_dir = context.config.workspace_path / "agents"

        context.console.print("\n" + "="*60)
        context.console.print("🏭 SPAWNED AGENTS")
        context.console.print("="*60)

        if not agents_dir.exists() or not any(agents_dir.iterdir()):
            context.console.print("\nNo agents spawned yet.")
            context.console.print("Use /spawn <role> to create one.")
        else:
            for agent_path in sorted(agents_dir.iterdir()):
                if agent_path.is_dir():
                    cert_file = agent_path / "BIRTH_CERTIFICATE.json"
                    if cert_file.exists():
                        import json
                        try:
                            cert = json.loads(cert_file.read_text(encoding='utf-8'))
                            context.console.print(f"\n  📦 {cert.get('role', agent_path.name)}")
                            context.console.print(f"     ID: {agent_path.name}")
                            context.console.print(f"     Created: {cert.get('created_at', 'N/A')[:10]}")
                        except Exception:
                            context.console.print(f"\n  📦 {agent_path.name} (Invalid Certificate)")
                    else:
                         context.console.print(f"\n  📦 {agent_path.name} (No Certificate)")

        context.console.print("\n" + "="*60 + "\n")


class ReviewCommand(Command):
    """Review pending children."""

    @property
    def name(self) -> str:
        return "/review"

    @property
    def description(self) -> str:
        return "Interactive review of pending children"

    def execute(self, args: str, context: CommandContext) -> CommandResult:
        from core.notifications import check_pending_review
        
        # Check if there's a pending review
        pending_metadata = check_pending_review(context.config.workspace_path)

        if not pending_metadata:
            context.console.print("ℹ️  No pending reviews found.")
            context.console.print("   Pending reviews are created after evolution completes.")
            return CommandResult(CommandStatus.SUCCESS, "")

        generation = pending_metadata['generation']
        children = pending_metadata['children']
        hours_elapsed = pending_metadata['hours_elapsed']

        # Display review header
        context.console.print("\n" + "="*60)
        context.console.print(f"📋 REVIEW - Generation {generation}")
        context.console.print("="*60)
        context.console.print(f"Children: {len(children)}")
        context.console.print(f"Elapsed: {hours_elapsed:.1f}h")
        context.console.print("="*60 + "\n")

        # Interactive review loop
        for i, child in enumerate(children, 1):
            context.console.print(f"\n{'─'*60}")
            context.console.print(f"Child {i}/{len(children)}: {child['id']}")
            context.console.print(f"{'─'*60}")
            context.console.print(f"Fitness Score: {child['score']:.3f} ({child['improvement']:+.1%} vs parent)")

            # Show improvements if available
            if 'improvements_summary' in child:
                context.console.print(f"\nImprovements:\n{child['improvements_summary']}")

            context.console.print(f"\nBirth Certificate: {child.get('birth_cert_path', 'Not found')}")
            context.console.print(f"Evaluation Results: {child.get('eval_results_path', 'Not found')}")

            # V7: Check auto-promotion eligibility
            decision_result = self._check_auto_promotion(context, child)

            # Display safety gates status
            context.console.print(f"\n🔒 Safety Gates ({sum(1 for g in decision_result.gates if g.passed)}/{len(decision_result.gates)} passed):")
            for gate in decision_result.gates:
                status = "✅" if gate.passed else "❌"
                blocking = " [BLOCKING]" if gate.blocking else ""
                context.console.print(f"   {status} {gate.name}: {gate.score:.2f}/{gate.threshold:.2f}{blocking}")

            # Auto-promotion if enabled and approved
            if getattr(context.config, 'auto_promotion_enabled', False) and decision_result.approved:
                context.console.print(f"\n🚀 AUTO-PROMOTION: {child['id']} passes all gates!")
                context.console.print(f"   Confidence: {decision_result.confidence:.1%}")
                context.console.print(f"   Reason: {decision_result.reason}")
                try:
                    self._promote_child(context, child, generation)
                    context.console.print(f"✅ Auto-promotion complete: {child['id']} is now the active parent")
                except Exception as e:
                    context.console.print_error(f"Auto-promotion failed: {e}")
                    context.console.print("⚠️  Falling back to manual review...")
                else:
                    continue  # Move to next child (auto-promoted successfully)

            # Show reason if not auto-approved
            if not decision_result.approved:
                context.console.print(f"\n⚠️  Manual review required: {decision_result.reason}")

            # Get user decision (manual review)
            while True:
                context.console.print("\n[A]pprove | [R]eject | [T]est | [S]kip | [Q]uit review")
                try:
                    decision = self._get_input(context, "nexus7/review> ").strip().lower()
                except KeyboardInterrupt:
                    context.console.print("\nReview interrupted.")
                    return CommandResult(CommandStatus.SUCCESS, "Review interrupted")

                if decision in ['a', 'approve']:
                    context.console.print(f"✓ Approved: {child['id']} will become new parent")
                    # Execute promotion logic
                    try:
                        self._promote_child(context, child, generation)
                        context.console.print(f"✅ Promotion complete: {child['id']} is now the active parent")
                    except Exception as e:
                        context.console.print_error(f"Promotion failed: {e}")
                        context.console.print("⚠️  Manual promotion required")
                    break
                elif decision in ['r', 'reject']:
                    context.console.print(f"✗ Rejected: {child['id']} will be archived")
                    try:
                        self._archive_rejected_child(context, child, generation)
                        context.console.print(f"✅ Child archived: {child['id']}")
                    except Exception as e:
                        context.console.print_error(f"Archival failed: {e}")
                        context.console.print("⚠️  Manual cleanup required")
                    break
                elif decision in ['t', 'test']:
                    context.console.print(f"🧪 Opening test mode for {child['id']}")
                    context.console.print("⚠️  Manual testing required (auto-testing not implemented in CLI yet)")
                    # TODO: Implement test mode
                elif decision in ['s', 'skip']:
                    context.console.print("Skipping...")
                    break
                elif decision in ['q', 'quit']:
                    return CommandResult(CommandStatus.SUCCESS, "Review quit")
        
        return CommandResult(CommandStatus.SUCCESS, "")

    def _get_input(self, context: CommandContext, prompt: str = "nexus7> ") -> str:
        """Get user input."""
        # Check if session is available in extras (from REPL)
        session = context.extras.get('session')
        if session:
             return session.prompt(prompt)
        return input(prompt)

    def _check_auto_promotion(self, context: CommandContext, child: dict):
        """Check if child is eligible for auto-promotion."""
        import json
        from pathlib import Path
        from core.evolution.child_validator import ChildValidator

        # Build validation_result dict from child data
        validation_result = {
            "passed": True,  # If it's in pending review, it passed validation
            "fitness_score": child.get('score', 0),
            "red_team_score": child.get('validation', {}).get('red_team_score')
        }

        # Try to load full validation results if available
        eval_path = child.get('eval_results_path')
        if eval_path:
            try:
                eval_path = Path(eval_path)
                if eval_path.exists():
                    full_results = json.loads(eval_path.read_text(encoding='utf-8'))
                    # V7.5: Support both old and new field names
                    fitness = full_results.get("fitness_score") or full_results.get("asi_score", child.get('score', 0))
                    validation_result.update({
                        "passed": full_results.get("passed", True),
                        "red_team_score": full_results.get("red_team_score"),
                        "fitness_score": fitness
                    })
            except Exception:
                pass

        # Get parent score for comparison (simplified: assume 0 if not found for now, or load lineage)
        # Ideally we should get this from lineage
        parent_fitness = 0.0 # Placeholder

        # Use ChildValidator to check eligibility (create dummy instance)
        validator = ChildValidator(
            child_path=Path("."),  # Not used by check_auto_promotion_eligibility
            child_id="",
            parent_id=""
        )

        return validator.check_auto_promotion_eligibility(
            validation_result=validation_result,
            parent_fitness_score=parent_fitness,
            config=context.config
        )

    def _promote_child(self, context: CommandContext, child: dict, generation: int):
        """Promote approved child to become the new active parent."""
        import shutil
        import subprocess
        from core.evolution.lineage import (
            load_lineage, save_lineage,
            promote_child_to_parent, archive_generation
        )

        child_id = child['id']
        fitness_score = child['score']

        # Paths
        # Assuming workspace_path is .../NEXUS_V7_CHRYSALIS/workspace
        parent_path = context.config.workspace_path.parent # NEXUS_V7_CHRYSALIS
        project_root = parent_path.parent  # 20_NEXUS
        child_path = project_root / "GENERATION_ACTIVE" / child_id
        archive_dir = project_root / "ARCHIVE" / f"GEN_{generation-1:03d}"

        # Validate child exists
        if not child_path.exists():
            raise FileNotFoundError(f"Child not found: {child_path}")

        context.console.print(f"\n{'─'*60}")
        context.console.print("🔄 PROMOTION IN PROGRESS")
        context.console.print(f"{'─'*60}")

        # 1. Load lineage
        lineage = load_lineage(context.config.workspace_path)
        old_parent = lineage["current_parent"]
        old_parent_id = old_parent["id"]

        context.console.print(f"Old Parent: {old_parent_id}")
        context.console.print(f"New Parent: {child_id}")

        # 2. Archive old parent
        context.console.print(f"\n📦 Archiving {old_parent_id}...")
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Copy parent to archive (keep original for safety during transition)
        archive_parent_path = archive_dir / old_parent_id
        if not archive_parent_path.exists():
            shutil.copytree(
                parent_path,
                archive_parent_path,
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'workspace')
            )
            context.console.print(f"✓ Parent archived to {archive_dir}")
        else:
            context.console.print(f"⚠️  Archive already exists, skipping")

        # Update lineage with archive info
        lineage = archive_generation(
            lineage,
            old_parent_id,
            archive_parent_path,
            reason=f"Superseded by {child_id}"
        )

        # 3. Promote child - copy child files over parent
        context.console.print(f"\n🚀 Promoting {child_id}...")

        # Remove old parent files (except workspace and .git)
        for item in parent_path.iterdir():
            if item.name in ['workspace', '.git', '__pycache__']:
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        # Copy child files to parent location
        for item in child_path.iterdir():
            if item.name in ['__pycache__', 'workspace']:
                continue
            dest = parent_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        context.console.print(f"✓ Child files promoted to NEXUS_V7_CHRYSALIS/")

        # 4. Update LINEAGE.json
        birth_cert_path = child.get('birth_cert_path', f"GENERATION_ACTIVE/{child_id}/BIRTH_CERTIFICATE.json")
        notable_features = [child.get('improvements_summary', 'Emergent mutation')]

        lineage = promote_child_to_parent(
            lineage=lineage,
            child_id=child_id,
            child_path=parent_path,  # New location
            fitness_score=fitness_score,
            birth_cert_path=birth_cert_path,
            notable_features=notable_features
        )

        save_lineage(lineage, context.config.workspace_path)
        context.console.print(f"✓ LINEAGE.json updated")

        # 5. Clean up GENERATION_ACTIVE
        context.console.print(f"\n🧹 Cleaning up...")
        shutil.rmtree(child_path)
        context.console.print(f"✓ Removed {child_path}")

        # 6. Git commit
        context.console.print(f"\n📝 Git commit...")
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=project_root,
                check=True,
                capture_output=True
            )
            commit_msg = f"evolution(promote): {child_id} -> active parent (Gen {generation})\n\n" \
                        f"Fitness Score: {fitness_score:.3f}\n" \
                        f"Archived: {old_parent_id}\n\n" \
                        f"Generated with NEXUS Evolution Engine"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=project_root,
                check=True,
                capture_output=True
            )
            context.console.print(f"✓ Committed promotion to git")
        except subprocess.CalledProcessError:
            context.console.print(f"⚠️  Git commit failed (manual commit recommended)")

        context.console.print(f"\n{'─'*60}")
        context.console.print(f"✅ PROMOTION COMPLETE")

    def _archive_rejected_child(self, context: CommandContext, child: dict, generation: int):
        """Archive a rejected child."""
        import shutil
        from datetime import datetime
        from core.evolution.lineage import load_lineage, save_lineage

        child_id = child['id']

        # Paths
        parent_path = context.config.workspace_path.parent
        project_root = parent_path.parent
        child_path = project_root / "GENERATION_ACTIVE" / child_id
        archive_dir = project_root / "ARCHIVE" / "rejected" / f"GEN_{generation:03d}"

        # Validate child exists
        if not child_path.exists():
            raise FileNotFoundError(f"Child not found: {child_path}")

        context.console.print(f"Archiving rejected child: {child_id}")

        # 1. Create archive directory
        archive_dir.mkdir(parents=True, exist_ok=True)

        # 2. Move child to archive
        archive_child_path = archive_dir / child_id
        if archive_child_path.exists():
            # If already exists, add timestamp to avoid collision
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_child_path = archive_dir / f"{child_id}_rejected_{timestamp}"

        shutil.move(str(child_path), str(archive_child_path))
        context.console.print(f"✓ Moved to {archive_child_path}")

        # 3. Update lineage with rejection
        try:
            lineage = load_lineage(context.config.workspace_path)
            if "rejected_children" not in lineage:
                lineage["rejected_children"] = []

            lineage["rejected_children"].append({
                "id": child_id,
                "generation": generation,
                "rejected_at": datetime.now().isoformat(),
                "reason": "manual_review_rejection",
                "archive_path": str(archive_child_path),
                "fitness_score": child.get('score', 0.0)
            })

            save_lineage(lineage, context.config.workspace_path)
            context.console.print("✓ Updated lineage with rejection record")
        except Exception as e:
            context.console.print(f"⚠️  Lineage update failed: {e}")
