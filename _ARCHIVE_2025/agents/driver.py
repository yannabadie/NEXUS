import json
import re
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

# Imports absolus depuis la racine du projet
from core.bridge import AIBridge
from core.logger import NexusLogger
from core.store import NexusStore
from core.contracts import (
    NexusState, TaskRequest, TaskResult, AgentRole, 
    TaskStatus, TaskPriority, FeedbackItem
)

class GeminiDriver:
    def __init__(self):
        self.logger = NexusLogger()
        self.bridge = AIBridge(self.logger)
        self.store = NexusStore()
        self.logger.system("NEXUS DRIVER (Gemini 3.0) Initialized [State-Aware + Visible]")

    def plan_and_execute(self, user_request: str) -> str:
        """
        Orchestration principale avec gestion d'état persistante.
        """
        # 1. Charger l'état
        state = self.store.load_state()
        
        # 2. Routing & Priority Analysis
        target_role = AgentRole.EXECUTOR # Default to Sonnet
        priority = TaskPriority.MEDIUM
        
        if self._is_critical_request(user_request):
            target_role = AgentRole.SAGE
            priority = TaskPriority.HIGH
            self.logger.log("DRIVER", "SAGE", "Routing critical request to Opus", "🧠")
        else:
            self.logger.log("DRIVER", "WORKER", "Routing execution request to Sonnet", "🛠️")

        # 3. Créer la TaskRequest
        task = TaskRequest(
            title="User Request Processing",
            description=user_request,
            priority=priority,
            role=target_role,
            created_by=AgentRole.DRIVER,
            input_data={"context": state.model_dump(mode='json')}
        )
        
        # 4. Log initial (Status Pending)
        self.store.log_task(task)
        
        # 5. Appel à Claude (Symbiose Persistante)
        claude_response_text = self._call_claude_with_state(task, state)
        
        # 6. Parsing "Best Effort"
        # Si c'est du JSON, tant mieux. Sinon, on encapsule le texte.
        result = self._parse_claude_response_loose(claude_response_text, task)
        
        # 7. Mise à jour du State & Store
        self.store.log_task(task, result)
        
        state.last_driver_message = user_request
        state.last_executor_response = result.summary
        state.turn_count += 1
        self.store.save_state(state)
        
        # 8. Retour utilisateur visible
        # On ne logue pas ici car le Logger a déjà affiché l'interaction via _call_claude
        # On retourne juste pour le script main
        return result.summary

    def _call_claude_with_state(self, task: TaskRequest, state: NexusState) -> str:
        """
        Prépare le prompt système complexe et appelle Claude via Persistent Bridge.
        """
        model = "opus" if task.role == AgentRole.SAGE else "sonnet"
        
        # On allège le prompt JSON strict pour laisser Claude parler
        system_prompt = f"""
        [ROLE: {task.role.value.upper()}]
        [SESSION: {state.context.session_id}]
        
        TASK: {task.description}
        
        INSTRUCTION:
        Act as an autonomous agent.
        If you write code, present it clearly.
        If you analyze, be concise.
        
        (Optional: You may return a JSON object matching TaskResult schema if structured data is needed, otherwise just text).
        """
        
        # L'appel Bridge va utiliser le Logger pour afficher la réponse en temps réel
        response = self.bridge.call_claude(system_prompt, model=model, persistent=True)
        
        # On logue explicitement la réponse reçue pour être sûr qu'elle s'affiche
        self.logger.log(f"CLAUDE-{model.upper()}", "DRIVER", response, "🤖")
        
        return response

    def _parse_claude_response_loose(self, text: str, task: TaskRequest) -> TaskResult:
        """
        Tente de parser le JSON, sinon fallback sur texte brut.
        """
        try:
            # Tentative JSON
            json_str = self._extract_json(text)
            if json_str and json_str.strip().startswith("{"):
                data = json.loads(json_str)
                # Injection metrics
                if "metrics" not in data:
                    data["metrics"] = {"start_time": datetime.now().isoformat()}
                if "task_id" not in data:
                    data["task_id"] = str(task.id)
                if "status" not in data:
                     data["status"] = TaskStatus.COMPLETED
                if "completed_by" not in data:
                     data["completed_by"] = task.role
                     
                return TaskResult(**data)
        except:
            pass # Fallback silencieux
            
        # Fallback Texte
        summary = text[:100] + "..." if len(text) > 100 else text
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            summary=summary,
            detailed_output=text,
            metrics={"start_time": datetime.now(), "duration_seconds": 0},
            completed_by=task.role
        )

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON if present."""
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return None

    def _is_critical_request(self, text: str) -> bool:
        keywords = ["critique", "architecture", "strategy", "risk", "audit", "security", "vision", "débat", "question"]
        return any(k in text.lower() for k in keywords)
