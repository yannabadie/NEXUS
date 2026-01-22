"""
NCM (NEXUS Code Modernization) Commands

Commands:
    /ncm status - Show NCM orchestrator status
    /ncm pilot [--count=N] - Run pilot with N stories (default: 10)
    /ncm execute --batch=N - Execute N stories from queue
    /ncm stories - List available stories
"""

from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

from core.interface.commands.registry import Command, CommandContext, CommandResult, CommandStatus
from core.ncm.models import Story, StoryPriority, IssueDomain, StoryStatus, NCMConfig
from core.ncm.orchestrator import NCMOrchestrator


@dataclass
class NCMService:
    """NCM service wrapper for REPL integration."""

    orchestrator: NCMOrchestrator
    stories: list[Story]

    @classmethod
    def create(cls, context: CommandContext) -> "NCMService":
        """Create NCM service from command context."""
        workspace_path = context.extras["repl"].workspace_path

        # Create NCM config
        config = NCMConfig(
            story_batch_size=50,
            token_limit=100_000_000,  # 100M tokens
            parallel_execution=False,  # Sequential for pilot
        )

        # Create NCM orchestrator
        ncm = NCMOrchestrator(
            orchestrator=context.orchestrator,
            workspace_path=workspace_path,
            config=config,
        )

        # Generate pilot stories
        stories = generate_pilot_stories()

        return cls(orchestrator=ncm, stories=stories)


def generate_pilot_stories(count: int = 10) -> list[Story]:
    """
    Generate pilot stories for testing.

    For now, generates synthetic dead import stories that SimpleExecutor can handle.
    This avoids the Windows subprocess hang issue with process_turn() collaborative modes.

    Args:
        count: Number of stories to generate

    Returns:
        List of Story objects
    """
    stories = []

    # Generate dead import removal stories (SimpleExecutor-compatible)
    # These target a test file with intentional dead imports
    test_file = "core/ncm/test_pilot_target.py"

    dead_import_targets = [
        (
            f"Remove dead import 'Dict' from {test_file}\n\nIssue:\nImport 'Dict' from 'typing' may be unused on line 7",
            test_file,
            ["Dict"]
        ),
        (
            f"Remove dead import 'List' from {test_file}\n\nIssue:\nImport 'List' from 'typing' may be unused on line 7",
            test_file,
            ["List"]
        ),
        (
            f"Remove dead import 'Set' from {test_file}\n\nIssue:\nImport 'Set' from 'typing' may be unused on line 7",
            test_file,
            ["Set"]
        ),
        (
            f"Remove dead import 'Tuple' from {test_file}\n\nIssue:\nImport 'Tuple' from 'typing' may be unused on line 7",
            test_file,
            ["Tuple"]
        ),
        (
            f"Remove dead import 'Union' from {test_file}\n\nIssue:\nImport 'Union' from 'typing' may be unused on line 7",
            test_file,
            ["Union"]
        ),
        (
            f"Remove dead import 'cast' from {test_file}\n\nIssue:\nImport 'cast' from 'typing' may be unused on line 7",
            test_file,
            ["cast"]
        ),
        (
            f"Remove dead import 'Optional' from {test_file}\n\nIssue:\nImport 'Optional' from 'typing' may be unused on line 7",
            test_file,
            ["Optional"]
        ),
        (
            f"Remove dead import 'sys' from {test_file}\n\nIssue:\nImport 'sys' may be unused on line 8",
            test_file,
            ["sys"]
        ),
    ]

    for i, (description, file_path, imports) in enumerate(dead_import_targets[:count], 1):
        story = Story(
            story_id=f"PILOT-{i:03d}",
            priority=StoryPriority.P2,
            domains={IssueDomain.CLEANUP},
            description=description,
            target_files=[Path(file_path)],
            test_files=[],
        )
        stories.append(story)

    return stories


class NCMCommand(Command):
    """
    NCM (NEXUS Code Modernization) orchestration command.

    Subcommands:
        status - Show NCM orchestrator status
        pilot [--count=N] - Run pilot with N stories
        execute --batch=N - Execute N stories from queue
        stories - List available stories
    """

    @property
    def name(self) -> str:
        return "/ncm"

    @property
    def aliases(self) -> List[str]:
        return []

    @property
    def description(self) -> str:
        return "NCM (NEXUS Code Modernization) orchestration"

    @property
    def usage(self) -> str:
        return "/ncm <subcommand> [options]"

    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """
        Execute NCM command (async).

        This is an async command - CommandRegistry.dispatch() will handle
        running it in an appropriate event loop context.

        Args:
            args: Command arguments (subcommand + options)
            context: Command execution context

        Returns:
            CommandResult with execution status
        """
        console = context.console

        # Parse subcommand
        parts = args.strip().split() if args.strip() else []
        subcommand = parts[0] if parts else "help"

        # Get or create NCM service
        repl = context.extras["repl"]
        if not hasattr(repl, "_ncm_service"):
            console.print("\n[cyan]Initializing NCM...[/cyan]")
            repl._ncm_service = NCMService.create(context)
            console.print("[green]✓[/green] NCM initialized\n")

        ncm_service = repl._ncm_service

        # Route subcommand
        if subcommand == "help" or subcommand == "--help":
            return self._ncm_help(console)

        elif subcommand == "status":
            return await self._ncm_status(console, ncm_service)

        elif subcommand == "pilot":
            # Parse --count flag
            count = 10  # default
            for part in parts[1:]:
                if part.startswith("--count="):
                    count = int(part.split("=")[1])

            return await self._ncm_pilot(console, ncm_service, count)

        elif subcommand == "stories":
            return self._ncm_stories(console, ncm_service)

        elif subcommand == "execute":
            # Parse --batch flag
            batch_size = 10  # default
            for part in parts[1:]:
                if part.startswith("--batch="):
                    batch_size = int(part.split("=")[1])

            return await self._ncm_execute(console, ncm_service, batch_size)

        else:
            console.print(f"[red]Unknown subcommand: {subcommand}[/red]")
            return self._ncm_help(console)

    def _ncm_help(self, console) -> CommandResult:
        """Show NCM help."""
        console.print("""
[bold cyan]NCM (NEXUS Code Modernization) Commands[/bold cyan]

[bold]Subcommands:[/bold]
  [cyan]status[/cyan]              - Show NCM orchestrator status
  [cyan]pilot[/cyan] [--count=N]  - Run pilot with N stories (default: 10)
  [cyan]stories[/cyan]             - List available stories
  [cyan]execute[/cyan] --batch=N  - Execute N stories from queue

[bold]Examples:[/bold]
  /ncm status
  /ncm pilot
  /ncm pilot --count=5
  /ncm stories
  /ncm execute --batch=10

[bold]Note:[/bold] NCM is in Phase 1 Pilot. Use with caution!
""")
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message="NCM help displayed"
        )

    async def _ncm_status(self, console, ncm_service: NCMService) -> CommandResult:
        """Show NCM status."""
        ncm = ncm_service.orchestrator

        console.print("\n[bold cyan]NCM Orchestrator Status[/bold cyan]\n")
        console.print(f"  Stories in Queue:  {len(ncm.story_queue)}")
        console.print(f"  Completed:         {len(ncm.completed)}")
        console.print(f"  Failed:            {len(ncm.failed)}")
        console.print(f"  Partial:           {len(ncm.partial)}")
        console.print(f"  Current Phase:     {ncm.current_phase}")
        console.print(f"  Tokens Used:       {ncm.tokens_used:,} / {ncm.token_limit:,}")
        console.print(f"  Token %:           {ncm.tokens_used / ncm.token_limit * 100:.1f}%")
        console.print("")

        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=f"NCM status: {len(ncm.completed)} completed"
        )

    async def _ncm_pilot(self, console, ncm_service: NCMService, count: int) -> CommandResult:
        """Run NCM pilot with N stories."""
        console.print(f"\n[bold cyan]NCM Pilot - {count} Stories[/bold cyan]\n")

        # Load stories
        stories = ncm_service.stories[:count]
        await ncm_service.orchestrator.load_story_queue(stories)

        console.print(f"[green]✓[/green] Loaded {len(stories)} stories")
        console.print("")

        # Execute stories
        console.print("[bold]Executing stories...[/bold]\n")

        for i, story in enumerate(stories, 1):
            console.print(f"  [{i}/{count}] {story.story_id}: {story.description[:60]}...")

            try:
                status = await ncm_service.orchestrator.execute_story(story)

                if status == StoryStatus.SUCCESS:
                    console.print(f"        [green]✓ SUCCESS[/green]")
                elif status == StoryStatus.FAILED:
                    console.print(f"        [red]✗ FAILED[/red] - {story.error_message}")
                elif status == StoryStatus.PARTIAL:
                    console.print(f"        [yellow]⚠ PARTIAL[/yellow]")

            except Exception as e:
                console.print(f"        [red]✗ ERROR: {str(e)}[/red]")
                story.status = StoryStatus.FAILED
                story.error_message = str(e)

            console.print("")

        # Summary
        completed = sum(1 for s in stories if s.status == StoryStatus.SUCCESS)
        failed = sum(1 for s in stories if s.status == StoryStatus.FAILED)

        console.print("[bold]Pilot Results:[/bold]")
        console.print(f"  Completed: {completed}/{count} ({completed/count*100:.1f}%)")
        console.print(f"  Failed:    {failed}/{count}")
        console.print("")

        if completed / count >= 0.80:
            console.print("[green]✓ Pilot PASSED (≥80% success)[/green]\n")
        else:
            console.print("[yellow]⚠ Pilot NEEDS REVIEW (<80% success)[/yellow]\n")

        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=f"Pilot complete: {completed}/{count} success"
        )

    def _ncm_stories(self, console, ncm_service: NCMService) -> CommandResult:
        """List available stories."""
        console.print("\n[bold cyan]Available Stories[/bold cyan]\n")

        for i, story in enumerate(ncm_service.stories, 1):
            console.print(f"  {story.story_id}: {story.description}")
            console.print(f"    Priority: {story.priority.value} | Domain: {', '.join(d.value for d in story.domains)}")
            console.print(f"    Target: {', '.join(str(f) for f in story.target_files)}")
            console.print("")

        return CommandResult(
            status=CommandStatus.SUCCESS,
            message=f"{len(ncm_service.stories)} stories available"
        )

    async def _ncm_execute(self, console, ncm_service: NCMService, batch_size: int) -> CommandResult:
        """Execute N stories from queue."""
        console.print(f"\n[bold cyan]NCM Execute - Batch of {batch_size}[/bold cyan]\n")

        # Load stories if not already loaded
        if not ncm_service.orchestrator.story_queue:
            stories = ncm_service.stories[:batch_size]
            await ncm_service.orchestrator.load_story_queue(stories)

        # Execute batch
        return await self._ncm_pilot(console, ncm_service, batch_size)


def register_ncm_commands(registry) -> None:
    """
    Register NCM commands with the command registry.

    Args:
        registry: CommandRegistry instance to register commands with
    """
    registry.register(NCMCommand())
