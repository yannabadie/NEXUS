"""
NEXUS V5.1 - Interactive Mode (REPL)
Claude Code-like conversational interface with session persistence.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
    from prompt_toolkit.completion import WordCompleter
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

from core.config import Config
from core.orchestration import Orchestrator
from core.synapse import MemoryManager


class SessionManager:
    """Manages interactive session persistence."""

    def __init__(self, workspace_path: Path):
        self.sessions_dir = workspace_path / ".nexus" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.conversation_history: List[Dict[str, Any]] = []

    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "turn_count": 0
        }

        with open(session_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        self.current_session_id = session_id
        return session_id

    def save_turn(self, user_input: str, result: str):
        """Save a conversation turn."""
        if not self.current_session_id:
            self.create_session()

        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_input,
            "result": result
        }

        self.conversation_history.append(turn)

        # Append to history file (JSONL format)
        session_dir = self.sessions_dir / self.current_session_id
        with open(session_dir / "history.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(turn, ensure_ascii=False) + "\n")

        # Update metadata
        metadata_file = session_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["turn_count"] = len(self.conversation_history)
            metadata["last_activity"] = datetime.now().isoformat()
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

    def get_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history."""
        return self.conversation_history

    def list_sessions(self) -> List[str]:
        """List all available sessions."""
        if not self.sessions_dir.exists():
            return []
        return [d.name for d in self.sessions_dir.iterdir() if d.is_dir()]


class InteractiveNexus:
    """Interactive REPL for NEXUS V5.1"""

    def __init__(self, workspace_path: Path, config: Config, mode: str = "Normal"):
        self.workspace_path = workspace_path
        self.config = config
        self.mode = mode
        self.session_manager = SessionManager(workspace_path)
        self.orchestrator: Optional[Orchestrator] = None

        # Command completer
        commands = [
            '/help', '/exit', '/quit', '/status', '/history', '/plan',
            '/clear', '/mode', '/save', '/load', '/reset', '/sessions'
        ]
        self.command_completer = WordCompleter(commands, ignore_case=True)

        # Setup prompt session
        if PROMPT_TOOLKIT_AVAILABLE:
            history_file = workspace_path / ".nexus" / "command_history"
            history_file.parent.mkdir(parents=True, exist_ok=True)
            self.session = PromptSession(
                history=FileHistory(str(history_file)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.command_completer
            )
        else:
            self.session = None

    def print_welcome(self):
        """Display welcome message."""
        print("\n" + "="*60)
        print("  NEXUS V5.1 - Interactive Orchestrator")
        print("  Gemini 3 Pro + Claude Sonnet 4.5")
        print("="*60)
        print("\nType /help for commands, or enter a task to begin.")
        print("Use Ctrl+C to interrupt, Ctrl+D or 'exit' to quit.\n")

    def print_help(self):
        """Display help information."""
        help_text = """
NEXUS Interactive Commands:

  /help              Show this help message
  /exit, /quit       Exit interactive mode
  /status            Show current orchestration state
  /history           Show conversation history
  /plan              Display current strategic plan
  /clear             Clear screen (preserves history)
  /mode <mode>       Switch mode (Normal/InProjectImprovement/CoreEvolution)
  /sessions          List all saved sessions
  /reset             Reset orchestration state

Task Execution:
  Just type your task naturally (no command prefix needed)
  Example: Create a test file named hello.txt

Keyboard Shortcuts:
  Ctrl+C             Interrupt current operation
  Ctrl+D             Exit (same as /exit)
  Up/Down Arrow      Browse command history
  Tab                Command completion
"""
        print(help_text)

    def show_status(self):
        """Show current orchestration status."""
        if not self.orchestrator:
            print("\n[Status] No active orchestration")
            return

        memory = MemoryManager(self.workspace_path, self.config.compression_threshold_tokens)
        blackboard = memory.get_blackboard()

        print("\n" + "="*60)
        print("  NEXUS Status")
        print("="*60)
        print(f"Mode:            {self.mode}")
        print(f"Session:         {self.session_manager.current_session_id or 'N/A'}")
        print(f"Turns:           {len(self.session_manager.get_history())}")
        print(f"Active Agent:    {getattr(self.orchestrator, 'active_agent', 'N/A')}")
        print(f"Objective:       {blackboard.get('objective', 'N/A')}")

        current_state = blackboard.get("current_state", {})
        print(f"Iteration:       {current_state.get('iteration', 0)}")
        print(f"Status:          {current_state.get('status', 'IDLE')}")
        print("="*60 + "\n")

    def show_history(self):
        """Show conversation history."""
        history = self.session_manager.get_history()

        if not history:
            print("\n[History] No conversation history yet\n")
            return

        print("\n" + "="*60)
        print(f"  Conversation History ({len(history)} turns)")
        print("="*60)

        for i, turn in enumerate(history, 1):
            print(f"\n[Turn {i}] {turn.get('timestamp', 'N/A')}")
            print(f"User:   {turn['user'][:100]}{'...' if len(turn['user']) > 100 else ''}")
            print(f"Result: {turn['result'][:100]}{'...' if len(turn['result']) > 100 else ''}")

        print("\n" + "="*60 + "\n")

    def show_plan(self):
        """Display current strategic plan."""
        memory = MemoryManager(self.workspace_path, self.config.compression_threshold_tokens)
        blackboard = memory.get_blackboard()

        strategic_plan = blackboard.get("strategic_plan", {})

        if not strategic_plan or not strategic_plan.get("steps"):
            print("\n[Plan] No strategic plan available yet\n")
            return

        print("\n" + "="*60)
        print("  Strategic Plan")
        print("="*60)

        for step in strategic_plan.get("steps", []):
            status_symbol = "✓" if step.get("status") == "completed" else "○"
            print(f"{status_symbol} {step.get('description', 'N/A')}")

        print("="*60 + "\n")

    def list_sessions(self):
        """List all available sessions."""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            print("\n[Sessions] No saved sessions found\n")
            return

        print("\n" + "="*60)
        print(f"  Saved Sessions ({len(sessions)})")
        print("="*60)

        for session_id in sorted(sessions, reverse=True):
            session_dir = self.session_manager.sessions_dir / session_id
            metadata_file = session_dir / "metadata.json"

            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                turns = metadata.get("turn_count", 0)
                created = metadata.get("created_at", "N/A")
                print(f"  {session_id} - {turns} turns - Created: {created}")
            else:
                print(f"  {session_id}")

        print("="*60 + "\n")

    def is_simple_conversation(self, text: str) -> bool:
        """Detect if text is a simple conversation/greeting (not a task)."""
        text_lower = text.lower().strip()

        # Task keywords that indicate technical work
        task_keywords = [
            'create', 'make', 'build', 'write', 'read', 'analyze',
            'fix', 'update', 'delete', 'list', 'show', 'install', 'run',
            'crée', 'créé', 'fais', 'écris', 'lis', 'analyse', 'corrige',
            'supprime', 'affiche', 'installe', 'lance', 'génère', 'modifie'
        ]

        # Common greetings
        greetings = [
            'hello', 'hi', 'hey', 'bonjour', 'salut', 'coucou',
            'good morning', 'good afternoon', 'good evening',
            'bonsoir', 'bonne journée', 'comment ça va', 'comment vas-tu',
            'how are you', 'what\'s up', 'sup', 'yo'
        ]

        # Simple questions about NEXUS itself
        self_questions = [
            'what are you', 'who are you', 'what can you do', 'what is your',
            'qu\'es-tu', 'qui es-tu', 'que peux-tu faire', 'quelles sont tes',
            'quel sont tes', 'c\'est quoi', 'explique moi', 'parle moi'
        ]

        # Check exact matches first
        for phrase in greetings + self_questions:
            if text_lower == phrase:
                return True

        # Check if starts with self-question (any length)
        for question in self_questions:
            if text_lower.startswith(question):
                return True  # Questions about NEXUS itself

        # Check if starts with greeting BUT contains task keywords
        for greeting in greetings:
            if text_lower.startswith(greeting + ' ') or text_lower.startswith(greeting + ','):
                # Extract text after greeting
                # Handle both space and comma separators
                if ',' in text_lower:
                    rest = text_lower.split(',', 1)[1].strip()
                else:
                    rest = text_lower[len(greeting):].strip()

                # If rest contains task keywords, it's a task, not conversation
                if any(kw in rest for kw in task_keywords):
                    return False  # It's a task!
                else:
                    return True  # Just a greeting with filler

        # Very short inputs without clear task indicators
        if len(text.split()) <= 3:  # 3 words or less
            has_task_keyword = any(kw in text_lower for kw in task_keywords)
            if not has_task_keyword:
                return True

        return False

    def respond_to_conversation(self, text: str):
        """Respond to simple conversations without orchestration."""
        text_lower = text.lower().strip()

        # Greetings
        if any(greet in text_lower for greet in ['hello', 'hi', 'hey', 'bonjour', 'salut']):
            print("\n[NEXUS] Hello! I'm NEXUS V5.1, an AI orchestrator.")
            print("I coordinate Gemini (strategy) and Claude (execution) to help you with tasks.")
            print("Type /help to see available commands, or describe a task to begin.\n")

        # About NEXUS
        elif any(q in text_lower for q in ['what are you', 'who are you', 'qu\'es-tu', 'qui es-tu']):
            print("\n[NEXUS] I'm NEXUS V5.1 - Interactive Cognitive Orchestrator")
            print("• Gemini 3 Pro handles strategic planning")
            print("• Claude Sonnet 4.5 handles precise execution")
            print("• I coordinate them in a symbiotic workflow")
            print("\nDescribe a technical task and I'll orchestrate the best approach!\n")

        # What can you do / Capabilities
        elif any(q in text_lower for q in ['what can you do', 'que peux-tu faire', 'quel sont tes', 'quelles sont tes', 'compétence', 'capacité']):
            print("\n[NEXUS] My capabilities:")
            print("• Code analysis and debugging")
            print("• File creation and editing (text, code, SVG, etc.)")
            print("• Running tests and builds")
            print("• Git operations")
            print("• Complex multi-step technical tasks")
            print("\nI coordinate Gemini (strategy) + Claude (execution) for optimal results!")
            print("Just describe what you need in natural language!\n")

        # Default
        else:
            print("\n[NEXUS] I'm here to help with technical tasks.")
            print("Describe what you'd like to accomplish, and I'll coordinate the work.\n")

    def handle_command(self, cmd: str) -> bool:
        """Handle slash commands. Returns False if should exit."""
        cmd = cmd.strip().lower()

        if cmd in ['/exit', '/quit']:
            return False

        elif cmd == '/help':
            self.print_help()

        elif cmd == '/status':
            self.show_status()

        elif cmd == '/history':
            self.show_history()

        elif cmd == '/plan':
            self.show_plan()

        elif cmd == '/clear':
            os.system('cls' if os.name == 'nt' else 'clear')

        elif cmd == '/sessions':
            self.list_sessions()

        elif cmd == '/reset':
            print("[Reset] Orchestration state reset")
            self.orchestrator = None

        elif cmd.startswith('/mode '):
            new_mode = cmd.split(' ', 1)[1].strip()
            if new_mode in ["Normal", "InProjectImprovement", "CoreEvolution"]:
                self.mode = new_mode
                print(f"[Mode] Switched to {new_mode}")
            else:
                print(f"[Error] Invalid mode. Use: Normal, InProjectImprovement, or CoreEvolution")

        else:
            print(f"[Error] Unknown command: {cmd}")
            print("Type /help for available commands")

        return True

    def handle_task(self, task: str):
        """Execute a task via orchestrator."""
        if not task.strip():
            return

        # Check if it's simple conversation (not a technical task)
        if self.is_simple_conversation(task):
            self.respond_to_conversation(task)
            self.session_manager.save_turn(task, "Conversation")
            return

        print(f"\n[NEXUS] Processing: {task}\n")

        try:
            # Create orchestrator for this task
            self.orchestrator = Orchestrator(
                workspace_path=self.workspace_path,
                config=self.config,
                objective=task,
                mode=self.mode
            )

            # Run orchestration
            self.orchestrator.run()

            # Check if ended due to panic (stagnation, etc.)
            panic_reason = self.orchestrator.panic_handler.check_panic()
            if panic_reason:
                print(f"\n[NEXUS] Task stopped: {panic_reason}")
                print("This often happens when the task isn't clear or is too conversational.")
                print("Try describing a specific technical task (e.g., 'create a file test.txt').\n")
                self.orchestrator.panic_handler.clear_panic()
                self.session_manager.save_turn(task, f"Stopped: {panic_reason}")
            else:
                # Normal completion
                self.session_manager.save_turn(task, "Completed")
                print(f"\n[NEXUS] Task completed\n")

        except KeyboardInterrupt:
            print("\n[NEXUS] Task interrupted by user\n")
            self.session_manager.save_turn(task, "Interrupted")
            # Clean up panic files if any
            if self.orchestrator:
                self.orchestrator.panic_handler.clear_panic()

        except Exception as e:
            print(f"\n[NEXUS ERROR] {e}\n")
            self.session_manager.save_turn(task, f"Error: {e}")
            # Clean up panic files if any
            if self.orchestrator:
                self.orchestrator.panic_handler.clear_panic()

    def run(self):
        """Main REPL loop."""
        # Force UTF-8 on Windows
        if sys.platform == 'win32':
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            try:
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                if hasattr(sys.stderr, 'reconfigure'):
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass

        # Create session
        self.session_manager.create_session()

        # Welcome message
        self.print_welcome()

        # Main loop
        while True:
            try:
                # Get user input
                if self.session and PROMPT_TOOLKIT_AVAILABLE:
                    user_input = self.session.prompt("nexus> ")
                else:
                    user_input = input("nexus> ")

                # Skip empty input
                if not user_input.strip():
                    continue

                # Handle commands
                if user_input.startswith('/'):
                    should_continue = self.handle_command(user_input)
                    if not should_continue:
                        break

                # Handle exit words
                elif user_input.lower() in ['exit', 'quit']:
                    break

                # Execute task
                else:
                    self.handle_task(user_input)

            except KeyboardInterrupt:
                print("\n(Use /exit or Ctrl+D to quit)")
                continue

            except EOFError:
                break

        # Goodbye message
        print("\n[NEXUS] Session saved. Goodbye!\n")


def detect_workspace_path() -> Path:
    """Auto-detect workspace path based on script location."""
    script_dir = Path(__file__).parent

    # Workspace is always in same directory as script
    workspace = script_dir / "workspace"

    # Detect mode based on path (more reliable than checking for core/ directory)
    if "AppData" in str(script_dir) or "Program Files" in str(script_dir):
        mode = "Installed"
    else:
        mode = "Development"

    print(f"[NEXUS] Mode: {mode}")
    print(f"[NEXUS] Script: {script_dir}")
    print(f"[NEXUS] Workspace: {workspace}")

    return workspace


def main():
    """Entry point for interactive mode."""
    # Auto-detect workspace path
    workspace_path = detect_workspace_path()
    workspace_path.mkdir(exist_ok=True)

    # Configuration
    env_path = Path(__file__).parent / ".env"
    config = Config(env_path if env_path.exists() else None)

    if not config.validate():
        print("[NEXUS ERROR] Configuration invalide. Vérifiez .env")
        sys.exit(1)

    # Check prompt_toolkit
    if not PROMPT_TOOLKIT_AVAILABLE:
        print("[Warning] prompt_toolkit not installed. Using basic input()")
        print("Install with: pip install prompt_toolkit>=3.0.43")
        print()

    # Create necessary directories
    (workspace_path / ".nexus").mkdir(exist_ok=True)
    (workspace_path / "_IO_BUFFER").mkdir(exist_ok=True)

    # Launch interactive mode
    try:
        interactive = InteractiveNexus(workspace_path, config)
        interactive.run()

    except Exception as e:
        print(f"[NEXUS ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
