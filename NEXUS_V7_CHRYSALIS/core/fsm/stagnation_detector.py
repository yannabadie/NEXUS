"""
Stagnation Detector - Détection adaptative de stagnation dans le brainstorming

Problème: Agents peuvent discuter en boucle sans jamais agir
Solution: Détecte la similarité textuelle des messages TALK

Méthode:
1. Stocke les 3 derniers messages TALK
2. Compare la similarité pairwise (difflib.SequenceMatcher)
3. Si 2+ paires sont similaires (> 0.8) → stagnation détectée
4. Injecte warning système pour forcer décision
"""
from typing import List
from difflib import SequenceMatcher


class StagnationDetector:
    """
    Détecte la stagnation dans le brainstorming

    Usage:
        detector = StagnationDetector()
        detector.add_message("Je pense qu'on devrait lire auth.py")
        detector.add_message("Oui, lisons auth.py d'abord")
        detector.add_message("D'accord, lire auth.py")
        if detector.is_stagnant():
            # Force decision
    """

    def __init__(self, similarity_threshold: float = 0.8, window_size: int = 3):
        """
        Initialize detector

        Args:
            similarity_threshold: Seuil de similarité (0.0 - 1.0)
                                0.8 = 80% similaire
            window_size: Nombre de messages à comparer (3 = derniers 3 messages)
        """
        self.similarity_threshold = similarity_threshold
        self.window_size = window_size
        self.message_history: List[str] = []

    def add_message(self, content: str):
        """
        Ajoute un message à l'historique

        Args:
            content: Contenu du message TALK
        """
        # Normalize: lowercase, strip whitespace
        normalized = content.lower().strip()
        self.message_history.append(normalized)

        # Keep only last N messages
        if len(self.message_history) > self.window_size:
            self.message_history = self.message_history[-self.window_size:]

    def is_stagnant(self) -> bool:
        """
        Détecte si la conversation stagne

        Returns:
            True si les messages se répètent (stagnation)

        Example:
            Message 1: "Je pense qu'on devrait lire auth.py"
            Message 2: "Oui, lisons auth.py d'abord"
            Message 3: "D'accord, lire auth.py"
            → Similarité élevée entre les 3 → stagnation = True
        """
        if len(self.message_history) < self.window_size:
            return False

        # Compare last N messages pairwise
        recent = self.message_history[-self.window_size:]

        similarities = []
        for i in range(len(recent)):
            for j in range(i + 1, len(recent)):
                sim = self._similarity(recent[i], recent[j])
                similarities.append(sim)

        # Si au moins 2 paires sont très similaires → stagnation
        high_similarity_pairs = [s for s in similarities if s > self.similarity_threshold]

        return len(high_similarity_pairs) >= 2

    def _similarity(self, text1: str, text2: str) -> float:
        """
        Calcule similarité entre 2 textes

        Uses difflib.SequenceMatcher (Gestalt Pattern Matching)

        Args:
            text1: Premier texte
            text2: Deuxième texte

        Returns:
            Score 0.0 - 1.0 (0 = différent, 1 = identique)

        Example:
            _similarity("lire auth.py", "lisons auth.py") → 0.85
            _similarity("lire auth.py", "écrire test.py") → 0.30
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def reset(self):
        """Reset détecteur (appelé après switch agent ou action)"""
        self.message_history.clear()

    def get_stagnation_message(self) -> str:
        """
        Message système à injecter en cas de stagnation

        Returns:
            Warning markdown à ajouter au contexte
        """
        return """
---

## ⚠️ ALERTE STAGNATION DÉTECTÉE

**Vous vous répétez depuis 3 tours sans prendre d'action concrète.**

**VOUS DEVEZ MAINTENANT:**
1. Prendre une décision claire (quel outil utiliser?)
2. Exécuter l'action (utiliser <tool_use>)
3. Arrêter de discuter

**Exemple de ce qui est attendu:**
```
<tool_use name="read">
{"file_path": "src/auth.py"}
</tool_use>
```

**Agissez immédiatement ou je passerai à l'agent suivant.**

---
"""

    def get_stats(self) -> dict:
        """
        Get detector statistics (pour debugging)

        Returns:
            {
                "message_count": int,
                "similarity_scores": List[float],
                "is_stagnant": bool
            }
        """
        recent = self.message_history[-self.window_size:] if len(self.message_history) >= self.window_size else []

        similarities = []
        if len(recent) >= 2:
            for i in range(len(recent)):
                for j in range(i + 1, len(recent)):
                    similarities.append(self._similarity(recent[i], recent[j]))

        return {
            "message_count": len(self.message_history),
            "recent_messages": recent,
            "similarity_scores": similarities,
            "is_stagnant": self.is_stagnant()
        }
