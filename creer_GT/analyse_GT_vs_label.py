"""
Script pour analyser le fichier CSV créé par seg_vs_label.py.

OBJECTIF :
----------
Ce script prend en entrée un fichier CSV contenant des mesures d’écart en coordonnées Z 
entre des segmentations et un label de référence (C1). Ce fichier CSV contient l'écart entre le label
et la segmentation pour deux méthodes: propseg et le ground truth de la méthode contrast-agnostic (GT).

Il permet de :
1. Identifier les sujets ayant uniquement une des deux colonnes renseignées (PropSeg ou GT).
2. Identifier les sujets dont la valeur GT est inférieure à un seuil (par défaut < 5).
3. Calculer des statistiques de base (moyenne, médiane, min, max) pour les deux méthodes.
4. Générer deux fichiers CSV :
   - `recapitulatif.csv` : tableau récapitulatif des statistiques.
   - `gt_negatif.csv` : sujets avec une valeur de GT inférieure à 5.

UTILISATION :
-------------
Ce script peut être exécuté depuis la ligne de commande avec les arguments suivants :

    python analyse_gt_propseg.py -f chemin/vers/fichier.csv -o chemin/vers/dossier_output

ARGUMENTS :
-----------
- `-f` : chemin du fichier CSV contenant les colonnes "Sujet", "GT", "propseg".
- `-o` : chemin du dossier de sortie où seront écrits les fichiers de résultats.

EXEMPLE :
---------
    python analyse_gt_propseg.py \
        -f GT_vs_label_1904.csv \
        -o resultats_analyses/

AUTEUR :
--------
Mélisende St-Amour-Bilodeau
Date : Avril 2025
"""

import pandas as pd
import argparse

def analyze_segmentation(file_path, output_path):
    # Charger le fichier CSV
    df = pd.read_csv(file_path)
    
    # Convertir en numérique en gérant les erreurs
    df["propseg"] = pd.to_numeric(df["propseg"], errors="coerce")
    df["GT"] = pd.to_numeric(df["GT"], errors="coerce")
    
    # 1. Identifier les sujets ayant une valeur pour propseg mais pas pour GT
    propseg_only = df[df["GT"].isna()]["Sujet"].tolist()
    
    # 2. Identifier les sujets ayant une valeur pour GT mais pas pour propseg
    gt_only = df[df["propseg"].isna()]["Sujet"].tolist()
    
    # 3. Identifier les sujets où GT < 5
    gt_negative = df[df["GT"] < 5].copy()
    
    # Créer un DataFrame récapitulatif
    recap_data = {
        "Nombre de sujets avec propseg mais pas GT": [len(propseg_only)],
        "Nombre de sujets avec GT mais pas propseg": [len(gt_only)],
        "Moyenne GT": [df["GT"].mean()],
        "Médiane GT": [df["GT"].median()],
        "Max GT": [df["GT"].max()],
        "Min GT": [df["GT"].min()],
        "Moyenne propseg": [df["propseg"].mean()],
        "Médiane propseg": [df["propseg"].median()],
        "Max propseg": [df["propseg"].max()],
        "Min propseg": [df["propseg"].min()],
    }
    
    recap_df = pd.DataFrame(recap_data)
    
    # Sauvegarde des résultats
    recap_df.to_csv(output_path + "/recapitulatif.csv", index=False)
    gt_negative.to_csv(output_path + "/gt_negatif.csv", index=False)
    
    print("Analyse terminée. Résultats sauvegardés dans le dossier spécifié.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse un fichier de GT_vs_label et génère des rapports.")
    parser.add_argument("-f", type=str, help="Chemin du fichier CSV à analyser")
    parser.add_argument("-o", type=str, help="Dossier où sauvegarder les résultats")
    
    args = parser.parse_args()
    
    analyze_segmentation(args.f, args.o)
