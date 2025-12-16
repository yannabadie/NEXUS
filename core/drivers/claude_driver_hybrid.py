"""
Claude Hybrid Driver V7 - Mode Hybride avec Dynamic Model Selection

Architecture:
- Claude répond en TEXTE NATUREL
- Utilise des balises XML pour les outils: <tool_use name="read">...</tool_use>
- Parser intelligent extrait content + tool_use
- V7: Dynamic model selection (Opus for brainstorm, Sonnet for validation)

Example Input Prompt:
    "Lis le fichier auth.py et identifie le bug"

Example Claude Response:
    "Je vais d'abord lire le fichier pour comprendre la structure.

    <tool_use name="read">
    {
      "file_path": "src/auth.py"
    }
    </tool_use>

    Ensuite j'analyserai le code pour trouver le bug."

Parser Output:
    {
        "sender": "Claude",
        "action_type": "TOOL_USE",
        "content": "Je vais d'abord lire... Ensuite j'analyserai...",
        "tool_use": {
            "tool_name": "read",
            "arguments": {"file_path": "src/auth.py"}
        }
    }
"""
import asyncio
import re
import json
import subprocess
import sys
import time
import atexit
import uuid
from pathlib import Path
from typing import Dict, Optional, Callable

# V7.7 Phase 15: Stream parser for real-time response display
from core.utils.stream_parser import parse_stream_chunk, is_result_message, extract_stats, extract_final_result

# V8.4.0: Unified agent registry
from core.agents.unified_registry import get_registry

# V8.8: Output Guard - System prompt leak prevention (OWASP LLM01:2025)
from core.security import get_output_guard
# V8.4.5: Structured driver logging
from core.logging.driver_logger import get_driver_logger

# Initialize driver logger
_logger = get_driver_logger("claude")


# Global reference for cleanup at exit
# V8.4.6: Thread-safe access for PARALLEL swarm mode
import threading
_active_claude_processes = []
_claude_processes_lock = threading.Lock()


def _cleanup_claude_processes():
    """Kill any remaining Claude processes at exit."""
    with _claude_processes_lock:
        for proc in _active_claude_processes:
            try:
                if proc.poll() is None:  # Still running
                    proc.terminate()
                    proc.wait(timeout=2)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        _active_claude_processes.clear()


# Register cleanup handler
atexit.register(_cleanup_claude_processes)


class ClaudeDriverHybrid:
    """
    Driver hybride pour Claude CLI

    Mode: Natural Language + XML Tool Blocks
    NO JSON enforcement - Claude parle naturellement

    V7: Supports model selection (Opus vs Sonnet) via routing
    """

    def __init__(
        self,
        config,
        workspace_path: Path,
        model: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        self.cli_path = config.claude_cli_path
        self.workspace_path = workspace_path
        self.io_buffer = workspace_path / "_IO_BUFFER"
        self.timeout = config.timeout if hasattr(config, 'timeout') else 120

        # V7: Model routing support
        self.model = model or getattr(config, 'claude_sonnet_model', None)
        self.agent_id = agent_id or "claude_primary"

    def _validate_output(self, response: Dict) -> Dict:
        """
        V8.8: Validate LLM output for system prompt leaks (OWASP LLM01:2025).

        Checks response content for potential information leakage and logs warnings.

        Args:
            response: Parsed LLM response dict

        Returns:
            Response dict (unchanged, or with sanitized content if leak detected)
        """
        output_guard = get_output_guard()

        # Extract content to validate
        content = response.get("content", "")
        if not content or not isinstance(content, str):
            return response

        validation = output_guard.validate(content)

        if validation.leak_type.value != "none":
            _logger.warning(
                f"[OUTPUT GUARD] Claude leak detected: {validation.leak_type.value} "
                f"(severity: {validation.leak_severity.value}) - {validation.reason}"
            )
            # Use sanitized output if available
            if validation.sanitized_output:
                response = response.copy()
                response["content"] = validation.sanitized_output
                response["_output_sanitized"] = True
                response["_leak_type"] = validation.leak_type.value

        return response

    def invoke(self, context: str, session_uuid: Optional[str] = None) -> Dict:
        """
        Invoke Claude CLI avec contexte markdown

        Args:
            context: Contexte markdown avec system prompt
            session_uuid: Optional unique ID for file isolation (V8.1.6)

        Returns:
            Dict structuré NEXUS (content, action_type, tool_use, etc.)

        Raises:
            RuntimeError: Si Claude CLI échoue
            TimeoutError: Si timeout dépassé
        """
        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid.uuid4())[:8]
        context_file = self.io_buffer / f"claude_context_{unique_id}.md"
        context_file.write_text(context, encoding="utf-8")
        # V8.4.6 SECURITY: Restrict context file to owner-only (may contain sensitive prompts)
        try:
            import os
            os.chmod(context_file, 0o600)
        except OSError:
            pass  # Windows may not support chmod, but file is in user-owned temp dir

        # Invoke Claude (mode naturel, PAS de flag JSON!)
        # @file syntax reads prompt from file
        # V12.4 SECURITY FIX: Add tool restrictions (parity with Gemini driver)
        # Allowed tools for NEXUS operations:
        # - File: Read, Write, Edit, Glob, Grep
        # - Shell: Bash (with NEXUS security layer)
        # - Web: WebFetch, WebSearch
        # - Task: TodoWrite, Task (subagents)
        # - Notebooks: NotebookEdit
        # NOTE: AskUserQuestion excluded - NEXUS has its own user interaction layer
        allowed_tools = "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch,TodoWrite,Task,NotebookEdit"
        command = f'"{self.cli_path}" -p @"{context_file}" --dangerously-skip-permissions --allowed-tools "{allowed_tools}"'

        try:
            # Use Popen with polling loop to allow CTRL+C interruption
            proc = subprocess.Popen(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # Track for cleanup at exit
            # V8.4.6: Thread-safe access
            with _claude_processes_lock:
                _active_claude_processes.append(proc)

            try:
                import queue  # threading already imported at module level

                start_time = time.time()
                stdout_data = []
                stderr_data = []
                output_queue = queue.Queue()

                def read_stream(stream, stream_name, data_list):
                    """Read stream in thread and queue lines for display."""
                    try:
                        for line in iter(stream.readline, ''):
                            if line:
                                data_list.append(line)
                                output_queue.put((stream_name, line.strip()))
                    except Exception:
                        pass

                # Start reader threads
                stdout_thread = threading.Thread(target=read_stream, args=(proc.stdout, 'stdout', stdout_data))
                stderr_thread = threading.Thread(target=read_stream, args=(proc.stderr, 'stderr', stderr_data))
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                stdout_thread.start()
                stderr_thread.start()

                # Poll loop - shows real activity
                last_activity = ""
                while proc.poll() is None:
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        print("\r" + " " * 80 + "\r", end="", file=sys.stderr)
                        # Capture any pending stderr before killing
                        current_stderr = ''.join(stderr_data)
                        print(f"[ERROR] Claude CLI Timeout. Partial stderr: {current_stderr[-500:]}", file=sys.stderr)

                        try:
                            proc.kill()
                            proc.wait(timeout=5)
                        except Exception as e:
                            print(f"[ERROR] Failed to kill Claude process: {e}", file=sys.stderr)

                        raise TimeoutError(f"Claude CLI timed out after {self.timeout}s. Stderr: {current_stderr[-200:]}")

                    # Check for new output
                    try:
                        while True:
                            stream_name, line = output_queue.get_nowait()
                            if line and len(line) > 3:
                                # Show real activity from Claude
                                last_activity = line[:60] + "..." if len(line) > 60 else line
                    except queue.Empty:
                        pass

                    # Show status with real activity or waiting message
                    status = f"🧠 Claude [{int(elapsed)}s]"
                    if last_activity:
                        print(f"\r{status}: {last_activity[:50]}", end="", file=sys.stderr)
                    else:
                        print(f"\r{status}: Processing...", end="", file=sys.stderr)

                    time.sleep(0.2)

                # Wait for threads to finish
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)

                # Clear status line
                print("\r" + " " * 80 + "\r", end="", file=sys.stderr)

                # Combine outputs
                stdout = ''.join(stdout_data)
                stderr = ''.join(stderr_data)

            except KeyboardInterrupt:
                print("\n[DEBUG] Interrupt received, killing Claude process...", file=sys.stderr)
                proc.kill()
                proc.wait()
                raise
            finally:
                # Remove from tracking once done
                # V8.4.6: Thread-safe access
                with _claude_processes_lock:
                    if proc in _active_claude_processes:
                        _active_claude_processes.remove(proc)

            if proc.returncode != 0:
                raise RuntimeError(f"Claude CLI failed: {stderr}")

            raw_response = stdout

            # Parse hybrid response
            parsed = self._parse_hybrid_response(raw_response)
            # V8.8: Validate output for system prompt leaks
            return self._validate_output(parsed)

        except TimeoutError:
            raise
        finally:
            # V8.1.6: Cleanup unique context file
            try:
                if context_file.exists():
                    context_file.unlink()
            except Exception:
                pass  # Best effort cleanup

    def invoke_stream(
        self,
        context: str,
        on_token: Callable[[str], None],
        session_uuid: Optional[str] = None
    ) -> Dict:
        """
        Invoke Claude CLI with streaming output (V7.7 Phase 15).

        Uses --output-format stream-json for JSONL streaming,
        parses each line, and calls on_token for text deltas.

        Args:
            context: Contexte markdown avec system prompt
            on_token: Callback called with each text chunk
            session_uuid: Optional unique ID for file isolation (V8.1.6)

        Returns:
            Dict structuré NEXUS (content, action_type, tool_use, etc.)

        Raises:
            RuntimeError: Si Claude CLI échoue
            TimeoutError: Si timeout dépassé
        """
        # V8.1.6: Generate unique ID for thread-safe file access
        unique_id = session_uuid or str(uuid.uuid4())[:8]
        context_file = self.io_buffer / f"claude_context_{unique_id}.md"
        context_file.write_text(context, encoding="utf-8")
        # V8.4.6 SECURITY: Restrict context file to owner-only (may contain sensitive prompts)
        try:
            import os
            os.chmod(context_file, 0o600)
        except OSError:
            pass  # Windows may not support chmod, but file is in user-owned temp dir

        # Claude streaming requires: --verbose --output-format stream-json --include-partial-messages
        # V12.4 SECURITY FIX: Add tool restrictions (same as invoke)
        # NOTE: AskUserQuestion excluded - NEXUS has its own user interaction layer
        allowed_tools = "Read,Write,Edit,Bash,Glob,Grep,WebFetch,WebSearch,TodoWrite,Task,NotebookEdit"
        command = f'"{self.cli_path}" -p @"{context_file}" --dangerously-skip-permissions --allowed-tools "{allowed_tools}" --verbose --output-format stream-json --include-partial-messages'

        try:
            print(f"[DEBUG] Invoking Claude (streaming)", file=sys.stderr)

            proc = subprocess.Popen(
                command,
                cwd=str(self.workspace_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            # V8.4.6: Thread-safe access
            with _claude_processes_lock:
                _active_claude_processes.append(proc)

            try:
                accumulated_text = []
                final_stats = {}
                final_result_text = None
                start_time = time.time()

                # Read JSONL lines from stdout in real-time
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break

                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > self.timeout:
                        proc.kill()
                        proc.wait()
                        raise TimeoutError(f"Claude CLI timed out after {self.timeout}s")

                    # Parse stream chunk
                    text_chunk, data = parse_stream_chunk(line, "claude")

                    if text_chunk is not None:
                        accumulated_text.append(text_chunk)
                        on_token(text_chunk)  # Stream to UI

                    if data and is_result_message(data, "claude"):
                        final_stats = extract_stats(data, "claude")
                        final_result_text = extract_final_result(data, "claude")

                # Wait for process to complete
                proc.wait(timeout=5)

                # Read any remaining stderr
                stderr = proc.stderr.read()

                if proc.returncode != 0:
                    error_msg = stderr or "Unknown error"
                    raise RuntimeError(f"Claude CLI failed (code {proc.returncode}): {error_msg}")

                # Final newline after streaming
                on_token("\n")

                # Build response from accumulated text or final result
                full_response = "".join(accumulated_text) if accumulated_text else (final_result_text or "")

                # Parse hybrid response (handles XML tool_use blocks)
                parsed_response = self._parse_hybrid_response(full_response)

                # Attach streaming stats if available
                if final_stats:
                    parsed_response["_stream_stats"] = final_stats

                # V8.8: Validate output for system prompt leaks
                return self._validate_output(parsed_response)

            except KeyboardInterrupt:
                print("\n[DEBUG] Interrupt received, killing Claude process...", file=sys.stderr)
                proc.kill()
                proc.wait()
                raise
            finally:
                # V8.4.6: Thread-safe access
                with _claude_processes_lock:
                    if proc in _active_claude_processes:
                        _active_claude_processes.remove(proc)

        except TimeoutError:
            raise
        finally:
            # V8.1.6: Cleanup unique context file
            try:
                if context_file.exists():
                    context_file.unlink()
            except Exception:
                pass  # Best effort cleanup

    async def send_message_async(self, prompt: str, session_uuid: Optional[str] = None) -> Dict:
        """
        Async bridge method for HiveMind phases compatibility (V8.4.5).

        Wraps sync invoke() in asyncio.to_thread() for non-blocking execution.
        This allows HiveMind phases to call driver methods without blocking
        the event loop, enabling true concurrent execution.

        Args:
            prompt: Context markdown with system prompt
            session_uuid: Optional unique ID for file isolation

        Returns:
            Dict structured NEXUS response (same as invoke())

        Note:
            This is a bridge method for backward compatibility with async HiveMind
            phases. New code should use AsyncClaudeDriver for full async support.
        """
        return await asyncio.to_thread(self.invoke, prompt, session_uuid)

    def _parse_hybrid_response(self, raw_text: str) -> Dict:
        """
        Parse Claude's natural language response avec balises XML

        Extrait:
        - content: Tout le texte HORS balises XML
        - tool_use: Contenu des balises <tool_use>
        - action_type: TOOL_USE si balise trouvée, sinon TALK

        Example Input:
            "Je vais lire le fichier.

            <tool_use name="read">
            {"file_path": "auth.py"}
            </tool_use>

            Puis je chercherai le bug."

        Example Output:
            {
                "sender": "Claude",
                "action_type": "TOOL_USE",
                "content": "Je vais lire le fichier. Puis je chercherai le bug.",
                "tool_use": {
                    "tool_name": "read",
                    "arguments": {"file_path": "auth.py"},
                    "expected_outcome": "Execute read successfully"
                }
            }
        """
        # Extract tool use blocks (XML pattern)
        tool_pattern = r'<tool_use\s+name="(\w+)">(.*?)</tool_use>'
        tool_matches = list(re.finditer(tool_pattern, raw_text, re.DOTALL))

        # Extract content (everything OUTSIDE tool blocks)
        content = raw_text
        for match in tool_matches:
            content = content.replace(match.group(0), '')
        content = content.strip()

        # Parse tool use if present
        tool_use = None
        action_type = "TALK"

        if tool_matches:
            # Use first tool block found
            match = tool_matches[0]
            tool_name = match.group(1)
            tool_args_raw = match.group(2).strip()

            # Parse arguments (JSON or key=value)
            try:
                arguments = json.loads(tool_args_raw)
            except json.JSONDecodeError:
                # Fallback: parse key=value format
                arguments = self._parse_keyvalue_args(tool_args_raw)

            tool_use = {
                "tool_name": tool_name,
                "arguments": arguments,
                "expected_outcome": f"Execute {tool_name} successfully"
            }
            action_type = "TOOL_USE"

        # Detect status from content
        status = "CONTINUE"
        finish_keywords = ["task complete", "finished", "done", "terminé", "fini"]
        if any(keyword in content.lower() for keyword in finish_keywords):
            status = "FINISHED"

        # V7 FIX: Alterner par défaut (l'orchestrateur force aussi)
        # V8.4.0: Use registry for alternation
        registry = get_registry()
        next_agent = registry.get_alternate("claude")  # → "gemini"

        # Construct structured message
        return {
            "sender": registry.get_display_name("claude"),  # V8.4.0
            "action_type": action_type,
            "content": content,
            "tool_use": tool_use,
            "status": status,
            "next_agent": next_agent
        }

    def _parse_keyvalue_args(self, args_text: str) -> Dict:
        """
        Parse arguments au format key=value (fallback si pas JSON)

        Example:
            file_path=src/auth.py
            line_number=42

        Returns:
            {"file_path": "src/auth.py", "line_number": "42"}
        """
        args = {}
        for line in args_text.split('\n'):
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                args[key.strip()] = value.strip()
        return args

    def invoke_with_retry(self, context: str, max_retries: int = 3) -> Dict:
        """
        Invoke avec retry sur erreur

        Si Claude échoue (timeout, subprocess error), retry avec:
        - Exponential backoff
        - Context augmenté avec reminder si parse error

        Args:
            context: Contexte markdown
            max_retries: Nombre de tentatives max

        Returns:
            Dict structuré

        Raises:
            RuntimeError: Si toutes les tentatives échouent
        """
        import time

        last_error = None

        for attempt in range(max_retries):
            try:
                return self.invoke(context)

            except Exception as e:
                last_error = e

                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

                    # If parse error, inject stronger reminder
                    if "parse" in str(e).lower() or "json" in str(e).lower():
                        context += "\n\n🚨 IMPORTANT: Use <tool_use> XML tags for tools."

        # All retries failed
        raise RuntimeError(f"Claude invocation failed after {max_retries} attempts: {last_error}")
