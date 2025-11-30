#!/usr/bin/env python3
"""
NEXUS V7.0 Batch Mode - Execute commands non-interactively.

Usage:
    python nexus_batch.py evolve 1
    python nexus_batch.py status
"""
import sys
import os
from pathlib import Path

os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

def main():
    if len(sys.argv) < 2:
        print("Usage: python nexus_batch.py <command> [args]")
        print("Commands: evolve <count>, status, doctor")
        sys.exit(1)
    
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    print(f"[BATCH] Command: {command} {' '.join(args)}")
    print("=" * 60)
    
    from nexus7 import bootstrap
    gemini_info, claude_info = bootstrap()
    
    from core.orchestration_v7 import OrchestratorV7
    from core.ui.console_v7 import ConsoleV7
    from core.config import load_config
    from core.evolution.rate_limiter import EvolutionRateLimiter
    
    workspace_path = Path("workspace").resolve()
    workspace_path.mkdir(parents=True, exist_ok=True)
    
    config = load_config()
    console = ConsoleV7(verbose=config.ui_verbose)
    
    orchestrator = OrchestratorV7(
        workspace_path,
        config,
        gemini_info,
        claude_info
    )
    
    nexus_root = Path(__file__).parent.resolve()
    
    class BatchREPL:
        pass
    
    repl = BatchREPL()
    repl.workspace_path = workspace_path
    repl.config = config
    repl.console = console
    repl.orchestrator = orchestrator
    repl.nexus_root = nexus_root
    repl.rate_limiter = EvolutionRateLimiter(workspace_path, config)
    repl._abort_requested = False
    repl.successful_turns = 0
    repl.evolution_trigger_threshold = 50
    
    from core.interface.repl import InteractiveNexusV7
    import types
    
    repl.run_evolve = types.MethodType(InteractiveNexusV7.run_evolve, repl)
    repl.brainstorm_children_with_ais = types.MethodType(InteractiveNexusV7.brainstorm_children_with_ais, repl)
    repl._validate_mutation_path = types.MethodType(InteractiveNexusV7._validate_mutation_path, repl)
    
    if command == "evolve":
        count = int(args[0]) if args else 1
        print(f"\n[BATCH] Running evolution with {count} children...\n")
        repl.run_evolve(child_count=count, auto_triggered=False)
    else:
        print(f"Unknown command: {command}")
        print("Available: evolve <count>")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[BATCH] Command completed")
    
    gen_active = Path(__file__).parent.parent / "GENERATION_ACTIVE"
    if gen_active.exists():
        children = [d for d in gen_active.iterdir() if d.is_dir()]
        print(f"\nChildren in GENERATION_ACTIVE: {len(children)}")
        for child in children:
            print(f"  - {child.name}")
            print(f"    KERNEL.py: {(child / 'KERNEL.py').exists()}")
            print(f"    workspace/: {(child / 'workspace').exists()}")
            print(f"    _IO_BUFFER: {(child / 'workspace' / '_IO_BUFFER').exists()}")
            
            # Check if child can boot
            birth_cert = child / "BIRTH_CERTIFICATE.json"
            if birth_cert.exists():
                import json
                cert = json.loads(birth_cert.read_text(encoding='utf-8'))
                print(f"    Birth cert: {cert.get('id', 'unknown')}")
                print(f"    Mutation: {cert.get('mutation', {}).get('file', 'N/A')}")
    else:
        print("\nNo children created")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[BATCH] Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n[BATCH] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
