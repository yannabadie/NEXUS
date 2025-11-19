import json
import csv
import io
from typing import List, Dict, Optional
from datetime import datetime

class ProductionMetrics:
    """Classe pour calculer les métriques de production et détecter les anomalies."""

    def __init__(self, data: List[Dict]):
        """
        Initialise les métriques de production.

        Args:
            data: Liste de dictionnaires contenant les données de production
                  avec les clés 'timestamp', 'status', 'count'
        """
        self.data = data

    def calculate_oee(self, planned_time: float, cycle_time: float = 1.5) -> float:
        """
        Calcule l'OEE (Overall Equipment Effectiveness).

        Args:
            planned_time: Temps planifié en minutes
            cycle_time: Temps de cycle par pièce en minutes (défaut: 1.5)

        Returns:
            OEE en pourcentage

        Raises:
            ValueError: Si planned_time est <= 0
        """
        if planned_time <= 0:
            raise ValueError("planned_time doit être supérieur à 0")

        if not self.data:
            return 0.0

        useful_time = sum(d.get('count', 0) for d in self.data) * cycle_time
        return min((useful_time / planned_time) * 100, 100.0)

    def detect_anomalies(self, threshold: int) -> List[Dict]:
        """
        Détecte les anomalies basées sur un seuil de production.

        Args:
            threshold: Seuil minimum de production

        Returns:
            Liste des enregistrements en dessous du seuil
        """
        return [d for d in self.data if d.get('count', 0) < threshold]

    def export_report(self, format: str = 'json') -> str:
        """
        Exporte les données dans le format spécifié.

        Args:
            format: Format d'export ('json' ou 'csv')

        Returns:
            Données formatées en string

        Raises:
            ValueError: Si le format n'est pas supporté
        """
        if format == 'json':
            return json.dumps(self.data, indent=2, default=str)
        elif format == 'csv':
            if not self.data:
                return "timestamp,status,count"

            output = io.StringIO()
            fieldnames = ['timestamp', 'status', 'count']
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(self.data)
            return output.getvalue()
        else:
            raise ValueError(f"Format non supporté: {format}. Utilisez 'json' ou 'csv'")