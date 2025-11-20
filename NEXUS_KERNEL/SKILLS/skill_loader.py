"""
NEXUS Skill Loader
==================

Module de chargement dynamique des compétences NEXUS.

Usage:
    from skill_loader import SkillLoader

    loader = SkillLoader()
    result = loader.execute_skill("skill_name", params={"key": "value"})
"""

import os
import sys
import importlib.util
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class SkillLoader:
    """Gestionnaire de chargement et d'exécution des Skills NEXUS."""

    def __init__(self, skills_dir: Optional[str] = None):
        """
        Initialise le loader.

        Args:
            skills_dir: Chemin vers le dossier SKILLS.
                       Si None, utilise le dossier courant.
        """
        if skills_dir is None:
            # Détecter le chemin du dossier SKILLS automatiquement
            current_file = Path(__file__).resolve()
            skills_dir = current_file.parent

        self.skills_dir = Path(skills_dir)
        self.loaded_skills: Dict[str, Any] = {}

    def list_available_skills(self) -> List[str]:
        """
        Liste toutes les skills disponibles.

        Returns:
            Liste des noms de skills (sans extension .py)
        """
        skills = []
        for file in self.skills_dir.glob("*.py"):
            if file.name != "skill_loader.py" and not file.name.startswith("_"):
                skills.append(file.stem)
        return sorted(skills)

    def load_skill(self, skill_name: str) -> Any:
        """
        Charge un module de skill dynamiquement.

        Args:
            skill_name: Nom de la skill (sans .py)

        Returns:
            Module chargé

        Raises:
            FileNotFoundError: Si la skill n'existe pas
            ImportError: Si le chargement échoue
        """
        skill_path = self.skills_dir / f"{skill_name}.py"

        if not skill_path.exists():
            raise FileNotFoundError(
                f"Skill '{skill_name}' introuvable dans {self.skills_dir}"
            )

        # Charger le module dynamiquement
        spec = importlib.util.spec_from_file_location(skill_name, skill_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Impossible de charger la skill '{skill_name}'")

        module = importlib.util.module_from_spec(spec)
        sys.modules[skill_name] = module
        spec.loader.exec_module(module)

        # Mettre en cache
        self.loaded_skills[skill_name] = module

        return module

    def execute_skill(self, skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécute une skill avec les paramètres fournis.

        Args:
            skill_name: Nom de la skill
            params: Dictionnaire de paramètres (optionnel)

        Returns:
            Résultat de la skill (format dict standard)

        Raises:
            AttributeError: Si la skill n'a pas de fonction execute()
        """
        if params is None:
            params = {}

        # Charger la skill si pas déjà en cache
        if skill_name not in self.loaded_skills:
            self.load_skill(skill_name)

        module = self.loaded_skills[skill_name]

        # Vérifier que la fonction execute existe
        if not hasattr(module, "execute"):
            raise AttributeError(
                f"La skill '{skill_name}' doit définir une fonction execute(params)"
            )

        # Exécuter
        try:
            result = module.execute(params)
            return {
                "status": "success",
                "skill": skill_name,
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "skill": skill_name,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """
        Récupère les informations d'une skill (docstring, signature).

        Args:
            skill_name: Nom de la skill

        Returns:
            Dictionnaire avec les métadonnées de la skill
        """
        if skill_name not in self.loaded_skills:
            self.load_skill(skill_name)

        module = self.loaded_skills[skill_name]

        info = {
            "name": skill_name,
            "description": module.__doc__ or "Pas de description",
            "has_execute": hasattr(module, "execute")
        }

        if hasattr(module, "execute"):
            execute_func = getattr(module, "execute")
            info["execute_doc"] = execute_func.__doc__ or "Pas de documentation"

        return info


# ==========================================
# Exemple d'utilisation (pour tests rapides)
# ==========================================
if __name__ == "__main__":
    print("=== NEXUS Skill Loader - Test ===\n")

    loader = SkillLoader()

    # Lister les skills disponibles
    available = loader.list_available_skills()
    print(f"Skills disponibles: {available}\n")

    # Tester le chargement d'une skill fictive (sera en erreur si aucune skill)
    if available:
        test_skill = available[0]
        print(f"Test de la skill: {test_skill}")
        info = loader.get_skill_info(test_skill)
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print("Aucune skill à tester. Créez des fichiers skill_*.py dans SKILLS/")
