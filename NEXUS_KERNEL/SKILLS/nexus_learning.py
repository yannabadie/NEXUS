#!/usr/bin/env python3
"""
NEXUS Learning Engine - CLI Autonome
Système d'apprentissage automatique pour NEXUS basé sur ACE+COMPASS

USAGE:
    python nexus_learning.py --learn <history_file>
    python nexus_learning.py --suggest <context>
    python nexus_learning.py --stats

DESCRIPTION:
    Analyse les logs d'interaction DRIVER/WORKER pour extraire:
    - Patterns de succès (stratégies efficaces)
    - Patterns d'erreur (erreurs récurrentes)
    - Optimisations détectées
    - Insights domaine-spécifiques

    Génère/met à jour PLAYBOOK.md avec patterns structurés.

ARCHITECTURE:
    Basé sur Stanford ACE framework (arXiv:2510.04618):
    - Generator: Parse logs → traces d'exécution
    - Reflector: Analyse traces → patterns
    - Curator: Merge patterns → PLAYBOOK.md

AUTEUR: NEXUS Project - 2025
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class PatternType(Enum):
    """Types de patterns détectables"""
    SUCCESS_STRATEGY = "success_strategy"
    ERROR_PATTERN = "error_pattern"
    OPTIMIZATION = "optimization"
    DOMAIN_INSIGHT = "domain_insight"


@dataclass
class ExecutionTrace:
    """Trace d'une exécution DRIVER→WORKER"""
    timestamp: str
    agent: str  # scout, architect, coder, etc.
    driver_task: str  # Commande du DRIVER
    worker_action: str  # Action du WORKER
    status: str  # SUCCESS, FAILURE, PARTIAL
    details: str
    error_msg: Optional[str] = None
    duration: Optional[float] = None

    @classmethod
    def from_log_entry(cls, entry_text: str) -> Optional['ExecutionTrace']:
        """Parse une entrée DRIVER/WORKER du log"""
        try:
            # Format attendu:
            # ### 🧠 **DRIVER (Gemini)** - YYYY-MM-DD HH:MM
            # *Task:* ... OU *Dispatching to Agent...*
            # ### 🤖 **WORKER (agent)** - YYYY-MM-DD HH:MM
            # *Status: SUCCESS* OU *Result: SUCCESS*
            # *Details:* ... OU contenu direct

            # Extraire timestamp
            timestamp_match = re.search(r'- (\d{4}-\d{2}-\d{2} \d{2}:\d{2})', entry_text)
            timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()

            # Identifier agent (variantes: WORKER, CLAUDE, scout, etc.)
            agent_match = re.search(r'\*\*(?:WORKER|CLAUDE) \((\w+)\)\*\*', entry_text)
            if not agent_match:
                # Essayer format alternatif sans parenthèses
                agent_match = re.search(r'\*\*(\w+) \(Worker\)\*\*', entry_text, re.IGNORECASE)
            agent = agent_match.group(1).lower() if agent_match else "unknown"

            # Extraire task du DRIVER (variantes multiples)
            task_match = re.search(r'\*Task:\*\s*(.+?)(?:\n|$)', entry_text)
            if not task_match:
                task_match = re.search(r'\*Dispatching to Agent.*?\*\n\*Task:\*\s*(.+?)(?:\n|$)', entry_text)
            if not task_match:
                task_match = re.search(r'\*Dispatching to Agent.*?\*(.+?)(?:\n|$)', entry_text)
            driver_task = task_match.group(1).strip() if task_match else "Task not specified"

            # Extraire status (variantes: *Status: SUCCESS* ou *Result: SUCCESS* ou *Status SUCCESS*)
            status_match = re.search(r'\*(?:Status|Result):\s*(SUCCESS|FAILURE|PARTIAL)', entry_text, re.IGNORECASE)
            status = status_match.group(1).upper() if status_match else "UNKNOWN"

            # Extraire détails (tout le contenu après status ou result)
            details_match = re.search(r'\*(?:Status|Result|Details?):\s*[^\n]*\n(.+)', entry_text, re.DOTALL)
            if not details_match:
                # Si pas de format structuré, prendre tout le contenu
                details_match = re.search(r'\*\*(?:WORKER|CLAUDE).*?\n(.+)', entry_text, re.DOTALL)
            details = details_match.group(1).strip() if details_match else ""

            # Limiter détails à 500 chars pour éviter surcharge
            if len(details) > 500:
                details = details[:500] + "..."

            # Extraire action (si précisée)
            action_match = re.search(r'\*Action:\*\s*(.+?)(?:\n|$)', entry_text)
            worker_action = action_match.group(1).strip() if action_match else driver_task[:100]

            # Extraire erreur si présente
            error_match = re.search(r'\*Error:\*\s*(.+?)(?:\n|$)', entry_text)
            if not error_match and "FAILURE" in status:
                # Chercher mots-clés d'erreur dans les détails
                error_keywords = re.search(r'(error|exception|failed|échec|erreur)[^\n]*', details, re.IGNORECASE)
                error_msg = error_keywords.group(0) if error_keywords else None
            else:
                error_msg = error_match.group(1).strip() if error_match else None

            # Valider données minimales
            if agent == "unknown" and not driver_task:
                return None

            return cls(
                timestamp=timestamp,
                agent=agent,
                driver_task=driver_task,
                worker_action=worker_action,
                status=status,
                details=details,
                error_msg=error_msg
            )
        except Exception as e:
            print(f"⚠️ [PARSER] Erreur parsing entry: {e}", file=sys.stderr)
            return None


@dataclass
class LearnedPattern:
    """Pattern appris depuis l'historique"""
    pattern_id: str
    pattern_type: PatternType
    trigger_context: str  # Contexte déclencheur
    strategy: str  # Stratégie à appliquer
    confidence: float  # 0.0 à 1.0
    success_count: int
    failure_count: int
    last_seen: str
    examples: List[str]  # Exemples d'exécutions
    agents_affected: List[str]  # Agents concernés

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def to_markdown(self) -> str:
        """Convertit le pattern en Markdown pour PLAYBOOK"""
        emoji_map = {
            PatternType.SUCCESS_STRATEGY: "✅",
            PatternType.ERROR_PATTERN: "❌",
            PatternType.OPTIMIZATION: "⚡",
            PatternType.DOMAIN_INSIGHT: "💡"
        }
        emoji = emoji_map.get(self.pattern_type, "📌")

        md = f"#### {emoji} {self.pattern_id}\n\n"
        md += f"**Type**: {self.pattern_type.value.replace('_', ' ').title()}\n"
        md += f"**Confiance**: {self.confidence:.1%} | "
        md += f"**Taux succès**: {self.success_rate:.1%}\n"
        md += f"**Observations**: {self.success_count + self.failure_count} fois\n"
        md += f"**Dernière occurrence**: {self.last_seen}\n\n"

        md += f"**Contexte déclencheur**:\n{self.trigger_context}\n\n"
        md += f"**Stratégie recommandée**:\n{self.strategy}\n\n"

        if self.agents_affected:
            md += f"**Agents concernés**: {', '.join(self.agents_affected)}\n\n"

        if self.examples:
            md += "**Exemples**:\n"
            for i, ex in enumerate(self.examples[:3], 1):
                md += f"{i}. {ex[:150]}...\n"
            md += "\n"

        return md


class NexusLearningEngine:
    """
    Moteur d'apprentissage autonome pour NEXUS
    Implémente la boucle Generator → Reflector → Curator
    """

    def __init__(self,
                 history_path: str,
                 playbook_path: str = "20_NEXUS/NEXUS_KERNEL/MEMORY/PLAYBOOK.md"):
        self.history_path = Path(history_path)
        self.playbook_path = Path(playbook_path)

        # Stockage en mémoire
        self.traces: List[ExecutionTrace] = []
        self.patterns: Dict[str, LearnedPattern] = {}

        # Configuration apprentissage
        self.min_confidence_threshold = 0.60
        self.min_examples_for_pattern = 2  # Abaissé à 2 pour plus de sensibilité
        self.similarity_threshold = 0.7

        # Stats
        self.stats = {
            "traces_parsed": 0,
            "patterns_extracted": 0,
            "patterns_merged": 0,
            "playbook_updated": False
        }

    # ==================== GENERATOR PHASE ====================

    def parse_chat_history(self) -> List[ExecutionTrace]:
        """
        Phase Generator: Parse CHAT_HISTORY_MASTER.md
        Format attendu: entrées DRIVER → WORKER successives
        """
        if not self.history_path.exists():
            print(f"❌ [GENERATOR] Fichier non trouvé: {self.history_path}", file=sys.stderr)
            return []

        print(f"📖 [GENERATOR] Lecture {self.history_path}")

        with open(self.history_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split par section (### header)
        sections = re.split(r'(?=###\s+[🧠🤖])', content)

        traces = []
        driver_task = None
        driver_section = None

        for section in sections:
            if not section.strip():
                continue

            # Identifier type de section
            if '**DRIVER' in section or '**GEMINI' in section:
                # Stocker la task pour associer au worker suivant
                driver_section = section
                task_match = re.search(r'\*Task:\*\s*(.+?)(?:\n|$)', section)
                if task_match:
                    driver_task = task_match.group(1).strip()
                else:
                    # Essayer format alternatif
                    dispatch_match = re.search(r'\*Dispatching to Agent.*?\*Task:\*\s*(.+?)(?:\n|$)', section)
                    if dispatch_match:
                        driver_task = dispatch_match.group(1).strip()
                    else:
                        # Prendre première ligne de texte comme task
                        first_line = re.search(r'\*(.+?)\*', section)
                        driver_task = first_line.group(1).strip() if first_line else "Tâche non spécifiée"

            elif '**WORKER' in section or '**CLAUDE' in section:
                # Construire texte complet DRIVER+WORKER pour meilleur parsing
                full_context = (driver_section or "") + "\n" + section

                # Parser section WORKER avec contexte DRIVER
                trace = ExecutionTrace.from_log_entry(full_context)
                if trace:
                    # Assurer que la task est présente
                    if not trace.driver_task or trace.driver_task == "Task not specified":
                        trace.driver_task = driver_task or "Tâche non spécifiée"

                    traces.append(trace)
                    self.stats["traces_parsed"] += 1

        print(f"✅ [GENERATOR] {len(traces)} traces extraites")
        return traces

    # ==================== REFLECTOR PHASE ====================

    def extract_patterns(self, traces: List[ExecutionTrace]) -> Dict[str, LearnedPattern]:
        """
        Phase Reflector: Analyse traces pour extraire patterns
        """
        print(f"🔍 [REFLECTOR] Analyse de {len(traces)} traces")

        patterns = {}

        # Grouper par agent et type d'action
        grouped = defaultdict(list)
        for trace in traces:
            key = f"{trace.agent}:{trace.worker_action[:50]}"
            grouped[key].append(trace)

        # Analyser chaque groupe
        for group_key, group_traces in grouped.items():
            if len(group_traces) >= self.min_examples_for_pattern:
                pattern = self._analyze_trace_group(group_key, group_traces)
                if pattern and pattern.confidence >= self.min_confidence_threshold:
                    patterns[pattern.pattern_id] = pattern
                    self.stats["patterns_extracted"] += 1

        print(f"✅ [REFLECTOR] {len(patterns)} patterns extraits")
        return patterns

    def _analyze_trace_group(self, group_key: str, traces: List[ExecutionTrace]) -> Optional[LearnedPattern]:
        """Analyse un groupe de traces similaires"""
        success_traces = [t for t in traces if t.status == "SUCCESS"]
        failure_traces = [t for t in traces if t.status == "FAILURE"]

        if not success_traces and not failure_traces:
            return None

        # Déterminer type de pattern
        success_count = len(success_traces)
        failure_count = len(failure_traces)
        total = success_count + failure_count

        if success_count > failure_count:
            pattern_type = PatternType.SUCCESS_STRATEGY
            strategy = self._extract_success_strategy(success_traces)
        else:
            pattern_type = PatternType.ERROR_PATTERN
            strategy = self._extract_error_strategy(failure_traces)

        # Extraire contexte commun
        trigger_context = self._extract_common_context(traces)

        # Calculer confiance
        confidence = max(success_count, failure_count) / total

        # Identifier agents affectés
        agents = list(set(t.agent for t in traces))

        # Créer pattern
        pattern_id = f"PAT-{group_key.split(':')[0]}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        return LearnedPattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            trigger_context=trigger_context,
            strategy=strategy,
            confidence=confidence,
            success_count=success_count,
            failure_count=failure_count,
            last_seen=traces[-1].timestamp,
            examples=[t.details[:100] for t in traces[:3]],
            agents_affected=agents
        )

    def _extract_success_strategy(self, traces: List[ExecutionTrace]) -> str:
        """Extraire stratégie commune aux succès"""
        # Analyser les détails pour trouver patterns communs
        details_text = " ".join(t.details for t in traces)

        # Mots-clés de succès
        success_keywords = re.findall(r'\b(completed?|success|validated?|created?|deployed?|fixed?)\b',
                                      details_text, re.IGNORECASE)

        if success_keywords:
            common_action = max(set(success_keywords), key=success_keywords.count)
            return f"Stratégie validée: {common_action.capitalize()} l'opération de manière autonome"

        return "Exécution autonome réussie - reproduire l'approche"

    def _extract_error_strategy(self, traces: List[ExecutionTrace]) -> str:
        """Extraire pattern d'erreur commun"""
        errors = [t.error_msg or t.details for t in traces if t.error_msg or "error" in t.details.lower()]

        if errors:
            # Trouver substring commun
            common_error = errors[0][:100]
            for err in errors[1:]:
                # Simple heuristique: prendre premiers mots communs
                words_common = set(common_error.lower().split()) & set(err.lower().split())
                if words_common:
                    common_error = " ".join(sorted(words_common)[:5])

            return f"⚠️ Erreur récurrente détectée: {common_error}. Vérifier prérequis avant exécution."

        return "Pattern d'échec détecté - nécessite investigation"

    def _extract_common_context(self, traces: List[ExecutionTrace]) -> str:
        """Extraire contexte déclencheur commun"""
        # Prendre la première task commune
        tasks = [t.driver_task for t in traces]
        if tasks:
            return tasks[0][:150]
        return "Contexte non identifié"

    # ==================== CURATOR PHASE ====================

    def update_playbook(self, patterns: Dict[str, LearnedPattern]):
        """
        Phase Curator: Mise à jour PLAYBOOK.md
        """
        print(f"📝 [CURATOR] Mise à jour du PLAYBOOK avec {len(patterns)} patterns")

        # Charger playbook existant si présent
        existing_patterns = self._load_existing_playbook()

        # Merger nouveaux patterns avec existants
        merged_patterns = self._merge_patterns(existing_patterns, patterns)

        # Générer nouveau PLAYBOOK.md
        self._generate_playbook_markdown(merged_patterns)

        self.stats["playbook_updated"] = True
        print(f"✅ [CURATOR] PLAYBOOK.md mis à jour: {self.playbook_path}")

    def _load_existing_playbook(self) -> Dict[str, LearnedPattern]:
        """Charge patterns existants depuis PLAYBOOK.md"""
        if not self.playbook_path.exists():
            return {}

        # TODO: Parser le Markdown pour extraire patterns existants
        # Pour l'instant, retourner vide (écrasement complet)
        return {}

    def _merge_patterns(self, existing: Dict[str, LearnedPattern],
                       new: Dict[str, LearnedPattern]) -> Dict[str, LearnedPattern]:
        """Merge patterns nouveaux avec existants"""
        merged = existing.copy()

        for pattern_id, new_pattern in new.items():
            # Chercher pattern similaire
            similar_id = self._find_similar_pattern_id(new_pattern, merged)

            if similar_id:
                # Fusionner avec pattern existant
                self._merge_pattern_data(merged[similar_id], new_pattern)
                self.stats["patterns_merged"] += 1
            else:
                # Ajouter nouveau pattern
                merged[pattern_id] = new_pattern

        return merged

    def _find_similar_pattern_id(self, pattern: LearnedPattern,
                                  existing: Dict[str, LearnedPattern]) -> Optional[str]:
        """Trouve un pattern similaire existant"""
        for pid, existing_pattern in existing.items():
            if (existing_pattern.pattern_type == pattern.pattern_type and
                self._similarity_score(existing_pattern.trigger_context,
                                      pattern.trigger_context) > self.similarity_threshold):
                return pid
        return None

    def _similarity_score(self, text1: str, text2: str) -> float:
        """Calcul simple de similarité par mots communs"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0

    def _merge_pattern_data(self, existing: LearnedPattern, new: LearnedPattern):
        """Fusionne données de 2 patterns"""
        # Mise à jour compteurs
        existing.success_count += new.success_count
        existing.failure_count += new.failure_count

        # Mise à jour confiance (moyenne pondérée)
        total_old = existing.success_count + existing.failure_count - new.success_count - new.failure_count
        total_new = new.success_count + new.failure_count
        total = total_old + total_new

        existing.confidence = (existing.confidence * total_old + new.confidence * total_new) / total

        # Mise à jour timestamp
        existing.last_seen = new.last_seen

        # Ajouter nouveaux exemples
        existing.examples.extend(new.examples)
        existing.examples = existing.examples[-5:]  # Garder 5 derniers

        # Merge agents
        existing.agents_affected = list(set(existing.agents_affected + new.agents_affected))

    def _generate_playbook_markdown(self, patterns: Dict[str, LearnedPattern]):
        """Génère PLAYBOOK.md complet"""
        # Grouper par type
        by_type = defaultdict(list)
        for pattern in patterns.values():
            by_type[pattern.pattern_type].append(pattern)

        # Trier par confiance décroissante
        for ptype in by_type:
            by_type[ptype].sort(key=lambda p: p.confidence, reverse=True)

        # Générer Markdown
        md = f"""# 📖 NEXUS PLAYBOOK
## Stratégies Apprises Automatiquement

**Dernière mise à jour**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total patterns**: {len(patterns)}
**Source**: Analyse automatique des logs DRIVER/WORKER

---

## 📊 Statistiques Globales

| Métrique | Valeur |
|----------|--------|
| **Patterns SUCCESS** | {len(by_type[PatternType.SUCCESS_STRATEGY])} |
| **Patterns ERROR** | {len(by_type[PatternType.ERROR_PATTERN])} |
| **Optimisations** | {len(by_type[PatternType.OPTIMIZATION])} |
| **Insights Domaine** | {len(by_type[PatternType.DOMAIN_INSIGHT])} |
| **Traces analysées** | {self.stats['traces_parsed']} |

---

"""

        # Section par type
        type_titles = {
            PatternType.SUCCESS_STRATEGY: "✅ Stratégies de Succès",
            PatternType.ERROR_PATTERN: "❌ Patterns d'Erreur",
            PatternType.OPTIMIZATION: "⚡ Optimisations",
            PatternType.DOMAIN_INSIGHT: "💡 Insights Domaine"
        }

        for ptype, title in type_titles.items():
            if ptype not in by_type:
                continue

            md += f"## {title}\n\n"

            patterns_list = by_type[ptype]
            md += f"*{len(patterns_list)} pattern(s) détecté(s)*\n\n"

            for pattern in patterns_list:
                md += pattern.to_markdown()
                md += "---\n\n"

        # Footer
        md += f"""
---

## 🔄 Processus d'Apprentissage

Ce PLAYBOOK est généré automatiquement par le **NEXUS Learning Engine**.

**Pipeline**:
1. **Generator**: Parse logs CHAT_HISTORY_MASTER.md → Traces d'exécution
2. **Reflector**: Analyse traces → Extraction de patterns
3. **Curator**: Merge patterns → Mise à jour PLAYBOOK.md

**Configuration**:
- Confiance minimale: {self.min_confidence_threshold:.0%}
- Exemples minimum: {self.min_examples_for_pattern}
- Seuil similarité: {self.similarity_threshold:.0%}

**Usage**:
```bash
# Mettre à jour le PLAYBOOK
python nexus_learning.py --learn 20_NEXUS/NEXUS_KERNEL/MEMORY/ARCHIVES/CHAT_HISTORY_MASTER.md

# Obtenir suggestion pour contexte
python nexus_learning.py --suggest "deploy infrastructure"

# Voir statistiques
python nexus_learning.py --stats
```

---

*Généré par NEXUS Learning Engine - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        # Écrire fichier
        self.playbook_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.playbook_path, 'w', encoding='utf-8') as f:
            f.write(md)

    # ==================== PUBLIC API ====================

    def learn(self) -> Dict:
        """Pipeline complet d'apprentissage"""
        print("=" * 70)
        print("🧠 NEXUS LEARNING ENGINE - Analyse & Apprentissage")
        print("=" * 70)
        print()

        # Phase 1: Generator
        self.traces = self.parse_chat_history()

        if not self.traces:
            print("⚠️ Aucune trace extraite - vérifier format du fichier log")
            return self.stats

        # Phase 2: Reflector
        self.patterns = self.extract_patterns(self.traces)

        if not self.patterns:
            print("⚠️ Aucun pattern détecté - besoin de plus de données")
            return self.stats

        # Phase 3: Curator
        self.update_playbook(self.patterns)

        print()
        print("=" * 70)
        print("✅ Apprentissage terminé")
        print("=" * 70)

        return self.stats

    def suggest_strategy(self, context: str) -> Optional[LearnedPattern]:
        """Suggère meilleure stratégie pour un contexte donné"""
        # Charger patterns depuis PLAYBOOK
        # TODO: Implémenter parsing PLAYBOOK.md si nécessaire

        if not self.patterns:
            print("⚠️ Aucun pattern chargé - exécuter --learn d'abord")
            return None

        best_match = None
        best_score = 0

        for pattern in self.patterns.values():
            score = self._similarity_score(pattern.trigger_context, context)
            weighted_score = score * pattern.confidence

            if weighted_score > best_score:
                best_score = weighted_score
                best_match = pattern

        return best_match

    def show_stats(self):
        """Affiche statistiques du système"""
        print("=" * 70)
        print("📊 NEXUS LEARNING ENGINE - Statistiques")
        print("=" * 70)
        print()

        if self.playbook_path.exists():
            with open(self.playbook_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Compter patterns par type (insensible à la casse et espaces)
            success_count = len(re.findall(r'Type\*\*:\s*Success Strategy', content, re.IGNORECASE))
            error_count = len(re.findall(r'Type\*\*:\s*Error Pattern', content, re.IGNORECASE))
            optim_count = len(re.findall(r'Type\*\*:\s*Optimization', content, re.IGNORECASE))
            insight_count = len(re.findall(r'Type\*\*:\s*Domain Insight', content, re.IGNORECASE))

            print(f"📖 PLAYBOOK: {self.playbook_path}")
            print(f"   Taille: {len(content)} caractères")
            print()
            print("📊 Patterns par type:")
            print(f"   ✅ Stratégies succès: {success_count}")
            print(f"   ❌ Patterns erreur: {error_count}")
            print(f"   ⚡ Optimisations: {optim_count}")
            print(f"   💡 Insights domaine: {insight_count}")
            print(f"   📈 TOTAL: {success_count + error_count + optim_count + insight_count}")
        else:
            print(f"⚠️ PLAYBOOK non trouvé: {self.playbook_path}")
            print("   Exécuter: python nexus_learning.py --learn <history_file>")

        print()
        print("=" * 70)


# ==================== CLI ====================

def main():
    parser = argparse.ArgumentParser(
        description="NEXUS Learning Engine - Apprentissage automatique depuis logs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Analyser logs et mettre à jour PLAYBOOK
  python nexus_learning.py --learn 20_NEXUS/NEXUS_KERNEL/MEMORY/ARCHIVES/CHAT_HISTORY_MASTER.md

  # Suggérer stratégie pour contexte
  python nexus_learning.py --suggest "deploy infrastructure"

  # Voir statistiques
  python nexus_learning.py --stats
        """
    )

    parser.add_argument('--learn', metavar='HISTORY_FILE',
                       help='Analyser fichier historique et mettre à jour PLAYBOOK.md')

    parser.add_argument('--suggest', metavar='CONTEXT',
                       help='Suggérer stratégie pour contexte donné')

    parser.add_argument('--stats', action='store_true',
                       help='Afficher statistiques PLAYBOOK actuel')

    parser.add_argument('--playbook', metavar='PATH',
                       default='20_NEXUS/NEXUS_KERNEL/MEMORY/PLAYBOOK.md',
                       help='Chemin vers PLAYBOOK.md (défaut: 20_NEXUS/NEXUS_KERNEL/MEMORY/PLAYBOOK.md)')

    parser.add_argument('--min-confidence', type=float, default=0.60,
                       help='Confiance minimale pour patterns (défaut: 0.60)')

    parser.add_argument('--min-examples', type=int, default=2,
                       help='Nombre minimum d\'exemples pour pattern (défaut: 2)')

    args = parser.parse_args()

    # Au moins une action requise
    if not (args.learn or args.suggest or args.stats):
        parser.print_help()
        sys.exit(1)

    # Mode LEARN
    if args.learn:
        engine = NexusLearningEngine(
            history_path=args.learn,
            playbook_path=args.playbook
        )
        engine.min_confidence_threshold = args.min_confidence
        engine.min_examples_for_pattern = args.min_examples

        stats = engine.learn()

        print()
        print("📊 Résumé:")
        print(f"   Traces parsées: {stats['traces_parsed']}")
        print(f"   Patterns extraits: {stats['patterns_extracted']}")
        print(f"   Patterns mergés: {stats['patterns_merged']}")
        print(f"   PLAYBOOK mis à jour: {'✅' if stats['playbook_updated'] else '❌'}")

    # Mode SUGGEST
    elif args.suggest:
        engine = NexusLearningEngine(
            history_path="",  # Non utilisé en mode suggest
            playbook_path=args.playbook
        )

        # Charger patterns depuis PLAYBOOK (si implémenté)
        suggestion = engine.suggest_strategy(args.suggest)

        if suggestion:
            print(f"💡 Suggestion pour: '{args.suggest}'")
            print()
            print(suggestion.to_markdown())
        else:
            print(f"⚠️ Aucune stratégie trouvée pour: '{args.suggest}'")

    # Mode STATS
    elif args.stats:
        engine = NexusLearningEngine(
            history_path="",
            playbook_path=args.playbook
        )
        engine.show_stats()


if __name__ == "__main__":
    main()
