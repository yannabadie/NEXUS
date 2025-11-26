"""
Headless Evolution Test - Bypasses interactive REPL
Tests the evolution brainstorming with debiased prompt
"""
import sys
import os
from pathlib import Path

# Add project root to path AND change working directory
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Disable prompt_toolkit by mocking it BEFORE importing repl
class MockPromptSession:
    def __init__(self, *args, **kwargs):
        pass
    def prompt(self, message="", **kwargs):
        return ""

class MockFileHistory:
    def __init__(self, *args, **kwargs):
        pass

# Mock the imports
sys.modules['prompt_toolkit'] = type(sys)('prompt_toolkit')
sys.modules['prompt_toolkit'].PromptSession = MockPromptSession
sys.modules['prompt_toolkit.history'] = type(sys)('prompt_toolkit.history')
sys.modules['prompt_toolkit.history'].FileHistory = MockFileHistory

from core.config import load_config
from core.meta.cli_inspector import CLIInspector
from core.orchestration_v7 import OrchestratorV7, OrchestratorState

def test_evolution_brainstorm():
    """Test evolution brainstorming in headless mode"""
    print("=" * 60)
    print(" HEADLESS EVOLUTION TEST")
    print("=" * 60)

    # Setup
    workspace = Path(__file__).parent / "workspace"
    config = load_config()

    print("\n[INFO] Inspecting CLI tools...")
    inspector = CLIInspector()
    gemini_info = inspector.inspect_gemini()
    claude_info = inspector.inspect_claude()

    print(f"   Gemini: {gemini_info.get('model', 'N/A')}")
    print(f"   Claude: {claude_info.get('model', 'N/A')}")

    # Initialize orchestrator
    print("\n[INFO] Initializing orchestrator...")
    orchestrator = OrchestratorV7(workspace, config, gemini_info, claude_info)

    # Craft brainstorm task (same as repl.py but shortened for test)
    parent_path = Path(__file__).parent
    parent_id = "NEXUS_V6.0"
    child_count = 1

    brainstorm_task = f"""EVOLUTION EMERGENTE - DEBAT SYMBIOTIQUE

CONTEXTE CRITIQUE:
Vous entrez dans une phase de RECHERCHE PURE.
IGNOREZ tout contexte precedent (tests, roadmap, autonomie).
VOTRE SEUL BUT est l'evolution du code source.

MISSION CRITIQUE: Analyser NEXUS V6.0 et proposer EXACTEMENT {child_count} mutations pour creer des enfants superieurs.

CONTEXTE PARENT:
- ID: {parent_id}
- Architecture: FSM dual-agent (Gemini + Claude symbiose)
- Fichiers: prompts/system_*.md, core/*.py, core/drivers/*.py, core/synapse/*.py

INSTRUCTIONS:
1. **DEBATTEZ** 10-30 tours max sur les faiblesses actuelles
2. **ANALYSEZ** le code parent (utilisez outil read si besoin)
3. **PROPOSEZ** des mutations EMERGENTES (pas hardcodees!)
4. **JUSTIFIEZ** l'impact ASI attendu

FORMAT JSON FINAL (STRICT, PARSABLE, PAS DE COMMENTAIRES):

[
  {{
    "file": "<chemin/vers/fichier.py ou .md>",
    "change": "<code ou texte EXACT a ajouter - pas de description vague>",
    "reason": "<justification technique de l'amelioration>",
    "expected_asi_impact": <float entre 0.01 et 0.10>
  }}
]

IMPORTANT: L'exemple ci-dessus est un TEMPLATE, pas une suggestion!
Explorez TOUT le code (core/, prompts/, drivers/, synapse/) avant de proposer.
Ne vous limitez PAS aux fichiers mentionnes - soyez creatifs et rigoureux.

REGLES CRITIQUES:
- EXACTEMENT {child_count} mutations (ni plus, ni moins)
- Format JSON STRICT (liste de dicts avec 'file', 'change', 'reason', 'expected_asi_impact')
- Fichiers EXISTANTS uniquement (verifiez avec read!)
- 'change' = code/texte CONCRET a ajouter (pas "ameliorer prompt")
- 'expected_asi_impact' = float 0.01-0.10 (realiste!)
- PAS DE COMMENTAIRES dans le JSON final

COMMENCEZ LE DEBAT (limite 30 tours).
DES QUE VOUS AVEZ UN ACCORD, ARRETEZ DE DISCUTER ET DONNEZ LE JSON.
OUTPUT FINAL = JSON UNIQUEMENT (sans texte autour)."""

    # Switch to EVOLUTION_BRAINSTORM mode
    print("\n[INFO] Switching to EVOLUTION_BRAINSTORM mode...")
    orchestrator._transition_to(OrchestratorState.EVOLUTION_BRAINSTORM)

    # Start brainstorming
    print("\n[INFO] Starting brainstorm debate...\n")
    print("-" * 60)

    result = orchestrator.process_turn(brainstorm_task)

    # Display result
    print(f"\n[Turn 1] Agent: {result.get('active_agent', 'N/A')}")
    print(f"State: {result.get('state', 'N/A')}")
    output = (result.get('output') or '')[:1500]
    print(f"Output (truncated):\n{output}...")

    # Continue for a few turns
    max_turns = 10
    turn = 1
    all_outputs = [result.get('output') or '']

    while result["state"] not in ["IDLE", "ERROR", "PANIC"] and turn < max_turns:
        turn += 1
        print(f"\n{'=' * 60}")
        result = orchestrator.process_turn()

        print(f"\n[Turn {turn}] Agent: {result.get('active_agent', 'N/A')}")
        print(f"State: {result.get('state', 'N/A')}")
        output = result.get('output') or ''
        all_outputs.append(output)

        # Show first 1500 chars
        print(f"Output (truncated):\n{output[:1500]}...")

        # Check for JSON in output
        if '"file"' in output and '"change"' in output and '"reason"' in output:
            print("\n[OK] Potential JSON detected!")
            break

    print("\n" + "=" * 60)
    print(" BRAINSTORM COMPLETE")
    print("=" * 60)
    print(f"Total turns: {turn}")
    print(f"Final state: {result.get('state', 'N/A')}")

    # Try to find JSON in outputs
    import json
    import re

    combined = '\n'.join(all_outputs)

    # Look for JSON arrays
    for match in re.finditer(r'\[\s*\{[^]]+\}\s*\]', combined, re.DOTALL):
        try:
            proposals = json.loads(match.group(0))
            if isinstance(proposals, list) and len(proposals) > 0:
                print("\n[RESULT] MUTATIONS PROPOSEES:")
                print("-" * 60)
                for i, prop in enumerate(proposals):
                    print(f"\n{i+1}. File: {prop.get('file', 'N/A')}")
                    print(f"   Reason: {prop.get('reason', 'N/A')[:100]}...")
                    print(f"   ASI Impact: {prop.get('expected_asi_impact', 'N/A')}")
                break
        except json.JSONDecodeError:
            continue

    return result


if __name__ == "__main__":
    try:
        test_evolution_brainstorm()
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
