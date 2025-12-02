# -*- coding: utf-8 -*-
"""
VSDX French to English Translation Script
Translates text in Visio XML files without altering the drawing structure.
"""

import re
import os
import shutil
from pathlib import Path

# Translation mapping FR -> EN (includes &apos; variants for XML)
TRANSLATIONS = {
    # HTML entity variants for apostrophes
    "Gestion de l&apos;entreprise": "Enterprise Management",
    "Nom d&apos;operateur": "Operator Name",
    "nom d&apos;operateur": "Operator Name",
    "Nom d&apos;op\xe9rateur": "Operator Name",
    "nom d&apos;op\xe9rateur": "Operator Name",
    "Date d&apos;application": "Application Date",
    "Heure d&apos;application": "Application Time",
    "nombre d&apos;outillage": "Number of tools",
    "d&apos;outillage": "tooling",
    "d&apos;environment": "environment",
    "d&apos;environnement": "environment",
    "d&apos;operateur": "Operator Name",
    "l&apos;entreprise": "enterprise",
    "l&apos;outillage": "tooling",
    "l&apos;ambient": "ambient",
    "d&apos;ouverture": "opening",
    "sachet inserts": "insert bag",
    "pi\xe8ces sabl\xe9e": "sandblasted parts",

    # Page 2 specific with &apos;
    "Prise en charge matiere premiere ( Date , Nom d&apos;operateur , Date de peremption)": "Raw material reception (Date, Operator Name, Expiration Date)",
    "Controle delegue ( Date , Nom d&apos;operateur )": "Delegated inspection (Date, Operator Name)",
    "Controle d\xe9l\xe9gu\xe9 : v\xe9rification traitement du moule ( Date )": "Delegated inspection: mold treatment verification (Date)",

    # Common French terms
    "Prise en charge": "Reception",
    "matiere premiere": "raw material",
    "Controle delegue": "Delegated inspection",
    "Controle d\xe9l\xe9gu\xe9": "Delegated inspection",
    "v\xe9rification": "verification",
    "traitement du moule": "mold treatment",
    "D\xe9coupe automatique": "Automatic cutting",
    "mise en Kit": "Kit assembly",
    "D\xe9but": "Start",
    "Fin": "End",
    "Dateb limite de cuisson": "Curing deadline",
    "Pr\xe9paration des plis": "Ply preparation",
    "Pre formage": "Preforming",
    "Pose des films": "Film placement",
    "compactage": "compaction",
    "Cuisson": "Curing",
    "D\xe9moulage": "Demolding",
    "Per\xe7age": "Drilling",
    "D\xe9graissage": "Degreasing",
    "cuvettes": "cups",
    "entretoises": "spacers",
    "Sablage": "Sandblasting",
    "cuisson de la colle": "adhesive curing",
    "S\xe9chage": "Drying",
    "Drapage": "Layup",
    "plis": "plies",
    "pli": "ply",
    "Collage": "Bonding",
    "Mise en place": "Placement",
    "Mise sous vide": "Vacuum application",
    "branchement vide": "vacuum connection",
    "perte de vide": "vacuum loss",
    "thermocouple": "thermocouple",
    "Autov\xe9rification": "Self-verification",
    "apr\xe8s cuisson": "post-curing",
    "du cycle": "cycle",
    "D\xe9coupe": "Cutting",

    # Generic terms
    # Page 1 - ISA-95/ISA-88 Conceptual Models
    "Modèle Physique (ISA-95)": "Physical Model (ISA-95)",
    "Modèles Conceptuels ISA-95 (Physique) vs ISA-88 (Procédural)": "ISA-95 Conceptual Models (Physical) vs ISA-88 (Procedural)",
    "Modèles Conceptuels ISA-95 (Phy": "ISA-95 Conceptual Models (Phy",
    '"Où ?" (Les Ressources)': '"Where?" (Resources)',
    "Entreprise: Motherson": "Enterprise: Motherson",
    "Site: Tanger": "Site: Tanger",
    "Atelier: Atelier Composites": "Workshop: Composites Workshop",
    "Équipements:": "Equipment:",
    "Equipement: Poste ZUND": "Equipment: ZUND Station",
    "Equipement: Autoclave N°1": "Equipment: Autoclave #1",
    "Equipement: Poste CND (US)": "Equipment: NDT Station (US)",
    "Equipement: Poste Détourage CN": "Equipment: CNC Trimming Station",
    "Modèle Procédural (ISA-88)": "Procedural Model (ISA-88)",
    '"Comment ?" (La Recette)': '"How?" (The Recipe)',
    "Processus: Fab. Kit LEAP 1A": "Process: Mfg. Kit LEAP 1A",
    "Étape: Préparation, Cuisson, CND...": "Step: Preparation, Curing, NDT...",
    "Opération": "Operation",
    "Opération: Découpe Nida": "Operation: Nida Cutting",
    "Opération: Cycle Polymérisation": "Operation: Polymerization Cycle",
    "Opération: Contrôle US": "Operation: US Inspection",
    "Opération: Détourage": "Operation: Trimming",
    "Phase": "Phase",
    "(ex: Lancer Prog, Montée T°, Valider Scan...)": "(e.g.: Start Prog, Temp Ramp-up, Validate Scan...)",
    "MAPPING FONDAMENTAL": "FUNDAMENTAL MAPPING",
    "(Orchestré par le MES Niveau 3)": "(Orchestrated by Level 3 MES)",

    # Page 2 - ISA-95 Functional Model
    "Modèle ISA-95 (Fonctionnel)": "ISA-95 Model (Functional)",
    "Niveau 4: ERP": "Level 4: ERP",
    "Gestion de l'entreprise": "Enterprise Management",
    "Niveau 3: Gestion des Opérations": "Level 3: Operations Management",
    "Flux transitionnel": "Transitional Flow",
    "(Demande Intervention)": "(Intervention Request)",
    "Niveau 2/1: Contrôle (PLC/CN)": "Level 2/1: Control (PLC/CNC)",
    "Contrôle-Commande": "Control-Command",
    "Autoclave, Découpe, CNs": "Autoclave, Cutting, CNCs",
    "Ordres de Fabrication": "Work Orders",
    "Traçabilité, OEE": "Traceability, OEE",
    "Consignes T°, Pression": "Temp, Pressure Setpoints",

    # Page 2 - ISA-88 Procedural Model
    "Modèle ISA-88 (Procédural) - Données Réelles VSM": "ISA-88 Model (Procedural) - Actual VSM Data",
    "Processus: Fabrication Kit Composite LEAP 1A (607 pièces) - Tanger": "Process: LEAP 1A Composite Kit Manufacturing (607 parts) - Tanger",

    # Phase headers
    "Phase 120 :  Découpe": "Phase 120: Cutting",
    "Phase 120: \xa0Découpe": "Phase 120: Cutting",
    "Phase 130: Drapage": "Phase 130: Layup",
    "Phase 140: Cuisson Autoclave": "Phase 140: Autoclave Curing",
    "Phase 150: Démoulage": "Phase 150: Demolding",
    "Phase 160 :Fraisage": "Phase 160: Milling",
    "Phase 170: Collage": "Phase 170: Bonding",
    "Phase 180: Cuisson": "Phase 180: Curing",
    "Phase 200: Contrôle Maquette": "Phase 200: Mock-up Inspection",
    "Phase 210: Robot multiperforation": "Phase 210: Multi-drilling Robot",
    "Phase 220: Extraction des poussieres": "Phase 220: Dust Extraction",
    "Phase 230 : Contrôle final": "Phase 230: Final Inspection",
    "Phase 120: \xa0TRAITEMENT OUTILLAGE ET AUTOVERIFICATION": "Phase 120: TOOLING TREATMENT AND SELF-VERIFICATION",

    # Unit descriptions
    "(UNIT-01-CUTTING: Cutting Table)": "(UNIT-01-CUTTING: Cutting Table)",
    "(UNIT-02-LAYUP-01 to 10: Drapage Stations)": "(UNIT-02-LAYUP-01 to 10: Layup Stations)",
    "(UNIT-03-AUTOCLAVE-01, 02: 2 Autoclaves )": "(UNIT-03-AUTOCLAVE-01, 02: 2 Autoclaves)",
    "(UNIT-04-DEMOLD-01/02, CNC-01, FINISH-01/02/03, DUST-01 (7 units))": "(UNIT-04-DEMOLD-01/02, CNC-01, FINISH-01/02/03, DUST-01 (7 units))",
    "(UNIT-05-MACHINING-01)": "(UNIT-05-MACHINING-01)",
    "(UNIT-09-MOCK-INSP-01)": "(UNIT-09-MOCK-INSP-01)",
    "(UNIT-11-DUST-EXTRUCT-01)": "(UNIT-11-DUST-EXTRUCT-01)",

    # Operations descriptions
    "Prise en charge matiere premiere ( Date , Nom d'operateur , Date de peremption)": "Raw material reception (Date, Operator Name, Expiration Date)",
    "Controle delegue ( Date , Nom d'operateur )": "Delegated inspection (Date, Operator Name)",
    "Découpe automatique des plis et mise en Kit ( Date , Nom d'operateur ,\nDébut ( T° et H%)\nFin ( T , H% ) , Dateb limite de cuisson)": "Automatic ply cutting and Kit assembly (Date, Operator Name,\nStart (Temp and H%)\nEnd (T, H%), Curing deadline)",
    "Controle délégué : vérification traitement du moule ( Date )": "Delegated inspection: mold treatment verification (Date)",
    "Préparation des plis (Temperature T°C ,\xa0 H%, Date , Nom d'operateur)": "Ply preparation (Temperature T°C, H%, Date, Operator Name)",
    "Pre formage Halarn ( Date , Nom d'operateur)": "Halar preforming (Date, Operator Name)",
    "Pose des films d'environnement + compactage(Date , Nom d'operateur)": "Environment films placement + compaction (Date, Operator Name)",
    "Cuisson ( Date / Nom d'operateur\xa0/ \xa0Nom d'Autoclave\xa0/ Date limite de cuisson\xa0/ Numéro de voie de vide\xa0/ numéro de cycle de cuisson\xa0/ Plan de chargement/ nombre d'outillage)": "Curing (Date / Operator Name / Autoclave Name / Curing deadline / Vacuum line number / Curing cycle number / Loading plan / Number of tools)",
    "Démoulage( Date , Nom d'operateur)": "Demolding (Date, Operator Name)",
    "Perçage des inserts ( Date , Nom d'operateur)": "Insert drilling (Date, Operator Name)",
    "Autovérification Perçage des inserts (\xa0Date , Nom d'operateur , N° programme\xa0)": "Insert drilling self-verification (Date, Operator Name, Program #)",
    "Dégraissage des cuvettes selon Pr-1500 ( Durée de trempage , durée de séchage à l'ambient , C/NC , Date , Nom d'operateur )": "Cup degreasing per Pr-1500 (Soaking time, ambient drying time, C/NC, Date, Operator Name)",
    "Dégraissage des entretoises selon Pr-1500 (\xa0Durée de trempage , durée de séchage à l'ambient , C/NC , Date , Nom d'operateur\xa0)": "Spacer degreasing per Pr-1500 (Soaking time, ambient drying time, C/NC, Date, Operator Name)",
    "Sablage des entretoises selon Pr 1800 ( Date , Nom d'opérateur )": "Spacer sandblasting per Pr 1800 (Date, Operator Name)",
    "cuisson de la colle sellon Pr-8000 ( Date / Nom d'operateur , Heure début cycle , N° de cycle cuisson , Température , Temps cuisson , N° Moyen\xa0)": "Adhesive curing per Pr-8000 (Date / Operator Name, Cycle start time, Curing cycle #, Temperature, Curing time, Equipment #)",

    # Legend
    "Légende": "Legend",
    "Niveau 4 (ERP)": "Level 4 (ERP)",
    "Niveau 3 (MES)": "Level 3 (MES)",
    "Niveau 3 (GMAO)": "Level 3 (CMMS)",
    "Niveau 2 (Contrôle)": "Level 2 (Control)",
    "Flux de données": "Data Flow",

    # Tooling treatment operations
    "Traitement de l'outillage de moulage(Date , Nom d'operateur , Date de péremption Frekote , N° de Pv Frekote 700 ,Outillage de moulage , Heure d'application traitemement )": "Mold tooling treatment (Date, Operator Name, Frekote expiration date, Frekote 700 PV #, Mold tooling, Treatment application time)",
    "Séchage d'outillage (Heure de fin de séchage , Durée de séchage traitement)": "Tooling drying (Drying end time, Treatment drying duration)",
    "Autovérification": "Self-verification",
    "Collage Halar(Date , nom d'operateur)": "Halar bonding (Date, Operator Name)",
    "Poses de film d'environment + compactage(Date , nom d'operateur)": "Environment film placement + compaction (Date, Operator Name)",
    "Drapage des plis 11 A/B/C/D et 2 (Date , nom d'operateur)": "Plies 11 A/B/C/D and 2 layup (Date, Operator Name)",
    "Drapage des plis 3 et 4(Date , nom d'operateur)": "Plies 3 and 4 layup (Date, Operator Name)",
    "Drapage des plis 5 et 6 (Date , nom d'operateur)": "Plies 5 and 6 layup (Date, Operator Name)",
    "Drapage des plis 7 et 8 et 9 sur la table (Date , nom d'operateur)": "Plies 7, 8 and 9 layup on table (Date, Operator Name)",
    "Decoupe films de colle AF 3109 + expansible AF3024 ou FM410(Date , nom d'operateur)": "AF 3109 adhesive film + AF3024 or FM410 expandable cutting (Date, Operator Name)",
    "Drapage bordures (film expansible + pli 10) + les premiers plis AF3024 ou FM410(Date / nom d'operateur / heure de début d'ouverture du sachet inserts / délai max de manipulation des pièces sablée apres l'ouverture de sachet)": "Edge layup (expandable film + ply 10) + first AF3024 or FM410 plies (Date / Operator Name / Insert bag opening start time / Max handling time for sandblasted parts after bag opening)",
    "Collage inserts(Heure ,\xa0Date , nom d'operateur)": "Insert bonding (Time, Date, Operator Name)",
    "Preparation des nida nomex + identification des perçage(Heure\xa0,\xa0Date , nom d'operateur)": "Nomex honeycomb preparation + drilling identification (Time, Date, Operator Name)",
    "Perçage des nida nomex (Date , nom d'operateur)": "Nomex honeycomb drilling (Date, Operator Name)",
    "Mise en place du Nida et des inserts ( C/NC , Date , Nom d'operateur)": "Honeycomb and insert placement (C/NC, Date, Operator Name)",
    "Drapage peau superieur (7,8 et 9) sur moule (Heure ,\xa0Date , nom d'operateur)": "Upper skin (7, 8 and 9) layup on mold (Time, Date, Operator Name)",
    "Drapage peau retour pli 2 (Date , nom d'operateur)": "Ply 2 return skin layup (Date, Operator Name)",
    "Controle délégée (C/NC ,\xa0Date , nom d'operateur)": "Delegated inspection (C/NC, Date, Operator Name)",
    "Mise en place du thermocouple(\xa0Date , nom d'operateur)": "Thermocouple placement (Date, Operator Name)",
    "Mise sous vide pour cuisson(\xa0Date , nom d'operateur, C/CN , Heure branchement vide , Valeur perte de vide\xa0)": "Vacuum application for curing (Date, Operator Name, C/NC, Vacuum connection time, Vacuum loss value)",
    "Autovérification du cycle (C/CN , Date , Nom d'operateur)": "Cycle self-verification (C/NC, Date, Operator Name)",
    "Autovérification après cuisson ( Date , Nom d'operateur , C/NC)": "Post-curing self-verification (Date, Operator Name, C/NC)",

    # Long checklist (Controle délégué block)
    "Controle délégué\xa0( C/NC )\npréformage halar( C/NC )\ncompactage( C/NC )\nCollage pli Halar( C/NC )\ncompactage( C/NC )\nPli 1 carbone\xa0( C/NC )\nPli 2 carbone\xa0( C/NC )\ncompactage( C/NC )\nPli 3 carbone\xa0( C/NC )\nPli 4 carbone\xa0( C/NC )\ncompactage( C/NC )\nPli 5 carbone( C/NC )\nPli 6 carbone( C/NC )\ncompactage( C/NC )\nPli 7 carbone( C/NC )\nPli 8 carbone( C/NC )\nPli 9 carbone( C/NC )\ncompactage( C/NC )\nPli 10 carbone( C/NC )\nAF3109 filmp de colle\xa0( C/NC )\nAF3024 inserts ou FM 410( C/NC )\nPose du Nida Nomex( C/NC )\ncompactage( C/NC )\nAF3109 Film de cole\xa0( C/NC )\nPLI 7 Carbone\xa0( C/NC )\nPli 8 Carbone( C/NC )\nPli 9 Carbone( C/NC )\ncompactage\xa0( C/NC )\nRecouverement PLI 12\xa0( C/NC )\nCompactage\xa0( C/NC )": "Delegated inspection (C/NC)\nHalar preforming (C/NC)\nCompaction (C/NC)\nHalar ply bonding (C/NC)\nCompaction (C/NC)\nCarbon ply 1 (C/NC)\nCarbon ply 2 (C/NC)\nCompaction (C/NC)\nCarbon ply 3 (C/NC)\nCarbon ply 4 (C/NC)\nCompaction (C/NC)\nCarbon ply 5 (C/NC)\nCarbon ply 6 (C/NC)\nCompaction (C/NC)\nCarbon ply 7 (C/NC)\nCarbon ply 8 (C/NC)\nCarbon ply 9 (C/NC)\nCompaction (C/NC)\nCarbon ply 10 (C/NC)\nAF3109 adhesive film (C/NC)\nAF3024 inserts or FM 410 (C/NC)\nNomex honeycomb placement (C/NC)\nCompaction (C/NC)\nAF3109 adhesive film (C/NC)\nCarbon PLY 7 (C/NC)\nCarbon ply 8 (C/NC)\nCarbon ply 9 (C/NC)\nCompaction (C/NC)\nPLY 12 covering (C/NC)\nCompaction (C/NC)",

    # Additional specific terms found in the XML
    "équipements": "equipment",
    "Equipement": "Equipment",
    "Montée T°": "Temp Ramp-up",
    "Nom d'operateur": "Operator Name",
    "nom d'operateur": "Operator Name",
    "Nom d'opérateur": "Operator Name",
    "nom d'opérateur": "Operator Name",
    "Date de peremption": "Expiration Date",
    "Date de péremption": "Expiration Date",
    "Date limite de cuisson": "Curing deadline",
    "Numéro de voie de vide": "Vacuum line number",
    "numéro de cycle de cuisson": "Curing cycle number",
    "Plan de chargement": "Loading plan",
    "nombre d'outillage": "Number of tools",
    "Durée de trempage": "Soaking time",
    "durée de séchage": "drying time",
    "Heure début cycle": "Cycle start time",
    "Température": "Temperature",
    "Temps cuisson": "Curing time",
    "Heure de fin de séchage": "Drying end time",
    "Durée de séchage traitement": "Treatment drying duration",
    "heure de début d'ouverture": "opening start time",
    "délai max de manipulation": "Max handling time",
    "Heure branchement vide": "Vacuum connection time",
    "Valeur perte de vide": "Vacuum loss value",

    # XML attribute translations (NameU, Name fields)
    "Modèles Conceptuels ISA-95 (Phy": "ISA-95 Conceptual Models (Phy",

    # Additional missing translations (Phase 2 analysis)
    "Modèle Hybride ISA-95/ISA-88 - ": "Hybrid ISA-95/ISA-88 Model - ",
    "Modèle Hybride ISA-95/ISA-88": "Hybrid ISA-95/ISA-88 Model",
    "Extraction des poussieres": "Dust Extraction",
    "Extraction des poussières": "Dust Extraction",
    "Perçage des nida nomex": "Nomex honeycomb drilling",
    "Per\xe7age des nida nomex": "Nomex honeycomb drilling",
    "Controle délégée": "Delegated inspection",
    "Controle déléguée": "Delegated inspection",
    "Contrôle délégée": "Delegated inspection",
    "après cuisson": "post-curing",
    "apr\xe8s cuisson": "post-curing",
    "Vérification aspect visuel du sablage": "Visual sandblasting inspection",
    "V\xe9rification aspect visuel du sablage": "Visual sandblasting inspection",
    "Préparation colle": "Adhesive preparation",
    "Pr\xe9paration colle": "Adhesive preparation",
    "Ebavurage de la pièce": "Part deburring",
    "Ebavurage de la pi\xe8ce": "Part deburring",
    "Detection des porosité": "Porosity detection",
    "Detection des porosit\xe9": "Porosity detection",
    "Détection des porosité": "Porosity detection",
    "D\xe9tection des porosit\xe9": "Porosity detection",
    "Preparation colle APF-7": "APF-7 adhesive preparation",
    "Ponçage surplus de colle": "Sanding excess adhesive",
    "Pon\xe7age surplus de colle": "Sanding excess adhesive",
    "ponçage surplus de colle": "sanding excess adhesive",
    "Ponçage de la hauteur des spacers": "Sanding spacer height",
    "Pon\xe7age de la hauteur des spacers": "Sanding spacer height",
    "Drilling Acoustique": "Acoustic drilling",
    "Ponçage panneau face veine": "Grain face panel sanding",
    "Pon\xe7age panneau face veine": "Grain face panel sanding",
    "Contrôle final et expédition": "Final inspection and shipping",
    "Contr\xf4le final et exp\xe9dition": "Final inspection and shipping",
    "Controle final et expedition": "Final inspection and shipping",
    "Relevé d'info via": "Data collected via",
    "Relev\xe9 d'info via": "Data collected via",
    "Relevé d&apos;info via": "Data collected via",
    "Relev\xe9 d&apos;info via": "Data collected via",
    "Controle de la hauteur des spacers": "Spacer height inspection",
    "Contrôle de la hauteur des spacers": "Spacer height inspection",
    "Hauteur controler avant": "Height to check before",
    "Marquage avec Vernis": "Marking with Varnish",
    "secteur de la pièce": "part sector",
    "secteur de la pi\xe8ce": "part sector",
    "si nécessaire": "if necessary",
    "si n\xe9cessaire": "if necessary",
    "Degreasing des cups": "Cup degreasing",
    "Degreasing des spacers": "Spacer degreasing",
    "Heure de début du séchage": "Drying start time",
    "Heure de d\xe9but du s\xe9chage": "Drying start time",
    "Heure fin du séchage": "Drying end time",
    "Heure fin du s\xe9chage": "Drying end time",
    "Qté base": "Base qty",
    "Qt\xe9 base": "Base qty",
    "Heure maxi utilisation": "Max usage time",
    "passage des alésoirs": "reamer pass",
    "passage des al\xe9soirs": "reamer pass",
    "N° outillage": "Tooling #",
    "N\xb0 outillage": "Tooling #",
    "N° sableuse": "Sandblaster #",
    "N\xb0 sableuse": "Sandblaster #",

    # Non-breaking space handling (\xa0)
    "\xa0": " ",

    # Final fixes (Phase 3 - encoding variants)
    "Preparation des nida nomex": "Nomex honeycomb preparation",
    "identification des perçage": "drilling identification",
    "identification des per\xe7age": "drilling identification",
    "Controle de la hauteur des spacers": "Spacer height inspection",
    "Relevé d&apos;info : Check list": "Data collected via: Check list",
    "Relev\xe9 d&apos;info : Check list": "Data collected via: Check list",
    "Relevé d&apos;info": "Data collected",
    "Relev\xe9 d&apos;info": "Data collected",
    "Ponçage de la hauteur": "Height sanding",
    "Pon\xe7age de la hauteur": "Height sanding",
    "Perçage des nida": "Honeycomb drilling",
    "Per\xe7age des nida": "Honeycomb drilling",

    # Phase 4 - individual word fixes
    "Perçage des nida nomex": "Nomex honeycomb drilling",
    "Per\xe7age des nida nomex": "Nomex honeycomb drilling",
    "Controle délégée": "Delegated inspection",
    "Controle déléguée": "Delegated inspection",
    "Controle d\xe9leg\xe9e": "Delegated inspection",
    "Controle d\xe9l\xe9gu\xe9e": "Delegated inspection",
    "avant/après": "before/after",
    "avant/apr\xe8s": "before/after",
    "après ponçage": "after sanding",
    "apr\xe8s pon\xe7age": "after sanding",
    "Controle visuel": "Visual inspection",
    "Contrôle visuel": "Visual inspection",
    "Contr\xf4le visuel": "Visual inspection",
    "de la finition": "of finish",
    "ponçage si": "sanding if",
    "pon\xe7age si": "sanding if",
}


def translate_xml_file(filepath: Path) -> bool:
    """
    Translate French text in a Visio XML file to English.
    Returns True if any changes were made.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    original_content = content

    # Sort translations by length (longest first) to avoid partial replacements
    sorted_translations = sorted(TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True)

    for french, english in sorted_translations:
        # Escape special regex characters in the French text
        escaped_french = re.escape(french)
        # Replace preserving case sensitivity
        content = content.replace(french, english)

    if content != original_content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Translated: {filepath.name}")
            return True
        except Exception as e:
            print(f"Error writing {filepath}: {e}")
            return False
    else:
        print(f"- No changes: {filepath.name}")
        return False


def main():
    base_path = Path("C:/Code/NEXUS/20_NEXUS - Copie/NEXUS_V7_CHRYSALIS/workspace/external_sources/Translation")
    extracted_path = base_path / "extracted_vsdx"

    if not extracted_path.exists():
        print(f"Error: Extracted folder not found at {extracted_path}")
        return

    # Files to translate
    xml_files = [
        extracted_path / "visio" / "pages" / "page1.xml",
        extracted_path / "visio" / "pages" / "page2.xml",
        extracted_path / "visio" / "document.xml",
        extracted_path / "visio" / "masters" / "master1.xml",
        extracted_path / "visio" / "masters" / "master2.xml",
    ]

    print("=== VSDX French to English Translation ===\n")

    translated_count = 0
    for xml_file in xml_files:
        if xml_file.exists():
            if translate_xml_file(xml_file):
                translated_count += 1
        else:
            print(f"! File not found: {xml_file.name}")

    print(f"\n=== Translation complete: {translated_count} files modified ===")

    # Create the translated VSDX
    output_vsdx = base_path / "EN_ISA-KIT-LEAP-VSM-BASED.vsdx"
    output_zip = base_path / "EN_ISA-KIT-LEAP-VSM-BASED.zip"

    # First create as ZIP
    print(f"\nCreating translated VSDX: {output_vsdx.name}")

    # Use shutil to create the zip (we'll rename it after)
    if output_zip.exists():
        output_zip.unlink()
    if output_vsdx.exists():
        output_vsdx.unlink()

    # Create zip archive
    shutil.make_archive(
        str(output_zip).replace('.zip', ''),
        'zip',
        extracted_path
    )

    # Rename .zip to .vsdx
    output_zip.rename(output_vsdx)

    print(f"[OK] Created: {output_vsdx.name}")
    print("\nDone! Open EN_ISA-KIT-LEAP-VSM-BASED.vsdx in Microsoft Visio to verify.")


if __name__ == "__main__":
    main()
