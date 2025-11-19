import os
import subprocess
from typing import Any, Dict

# Simulation simple de l'ADK pour le POC
# Note: L'API réelle de google-adk peut différer légèrement, 
# ce script sert de validation de concept pour l'orchestration.

class AgentContext:
    def __init__(self):
        self.state = {}

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def run(self, context: AgentContext):
        raise NotImplementedError

class GeminiAgent(BaseAgent):
    def run(self, context: AgentContext):
        print(f"[{self.name}] (Gemini) Thinking...")
        # Ici on simulerait l'appel API Gemini
        # Pour le POC, on fait une action simple
        poem = "Dans le code binaire, une lueur,\nNEXUS s'eveille, sans peur."
        context.state['poem'] = poem
        print(f"[{self.name}] Generated: {poem}")
        return context

class ClaudeWorkerAgent(BaseAgent):
    def run(self, context: AgentContext):
        print(f"[{self.name}] (Claude) Critiquing...")
        poem = context.state.get('poem', '')
        
        # Appel réel à Claude via CLI
        cmd = f'claude --print "Critique ce poème en une phrase : {poem}" --model sonnet'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            critique = result.stdout.strip()
        except Exception as e:
            critique = f"Error calling Claude: {e}"
            
        context.state['critique'] = critique
        print(f"[{self.name}] Critique: {critique}")
        return context

def run_pipeline():
    print("=== STARTING ADK POC PIPELINE ===")
    context = AgentContext()
    
    agents = [
        GeminiAgent("Poet"),
        ClaudeWorkerAgent("Critic")
    ]
    
    for agent in agents:
        agent.run(context)
        
    print("=== PIPELINE FINISHED ===")
    print("Final State:", context.state)

if __name__ == "__main__":
    run_pipeline()
