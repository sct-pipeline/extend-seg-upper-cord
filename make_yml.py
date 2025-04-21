"""
Script de génération automatique d’un fichier YAML listant les sujets validés par QC à partir du fichier json

OBJECTIF :
----------
Ce script lit un fichier 'qc_flags.json' et extrait
les sujets ayant passé le contrôle qualité manuel ('✅') pour la tâche 'sct_deepseg_sc'.

Pour chaque sujet validé :
- Si au moins une des modalités (T1w ou T2w) est marquée comme valide,
  le script inclut les deux modalités dans la sortie YAML.

FONCTIONNEMENT :
----------------
1. Charge le fichier 'qc_flags.json' contenant les résultats de QC (issus du HTML).
2. Extrait les noms de fichiers marqués comme validés ('✅') pour la tâche 'sct_deepseg_sc_qc'.
3. Identifie les sujets ('sub-XXXX') et les contrastes ('T1w', 'T2w').
4. Génère la liste complète des chemins relatifs vers les images anatomiques à inclure.
5. Sauvegarde le tout dans un fichier 'subjects_to_include.yml' conforme au format attendu.

FORMAT DE SORTIE YAML :
-----------------------
Exemple de contenu :

data-multi-subject:
  - sub-barcelona02/anat/sub-barcelona02_T1w.nii.gz
  - sub-barcelona02/anat/sub-barcelona02_T2w.nii.gz
  - sub-geneva01/anat/sub-geneva01_T1w.nii.gz

AUTEUR :
--------
Mélisende St-Amour-Bilodeau  
Date : Avril 2025
"""

import json
import yaml
from collections import defaultdict
import os

# Charger le fichier qc.json
with open("qc_flags.json", "r") as f:
    qc_data = json.load(f)

# Dictionnaire temporaire pour suivre les sujets validés
subjects_validated = defaultdict(set)

# Parcourir les entrées QC
for key, value in qc_data.items():
    if "sct_deepseg_sc_qc" in key and value.strip() == "✅":
        # Format attendu : 2025-04-01 07:02:09_sub-barcelona02_T1w.nii.gz_sct_deepseg_sc_qc
        parts = key.split("_")
        try:
            subject = parts[1]              # sub-barcelona02
            contrast = parts[2].split(".")[0]  # T1w (remove .nii.gz)
            subjects_validated[subject].add(contrast)
        except IndexError:
            print(f"Problème de format avec la ligne : {key}")

# Générer la liste complète des chemins à inclure
subjects_yml = {"data-multi-subject": []}
for subject, contrasts in subjects_validated.items():
    # Ajoute T1w s'il n'est pas déjà là
    if "T1w" in contrasts or "T2w" in contrasts:
        for contrast in ("T1w", "T2w"):
            path = f"{subject}/anat/{subject}_{contrast}.nii.gz"
            subjects_yml["data-multi-subject"].append(path)

# Sauvegarder en YAML
with open("subjects_to_include.yml", "w") as f:
    yaml.dump(subjects_yml, f, default_flow_style=False)

print("Fichier 'subjects_to_include.yml' généré avec succès.")