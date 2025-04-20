"""
Script de comparaison entre la position du label C1 et l'extrémité supérieure
d'une segmentation de la moelle épinière.

OBJECTIF :
---------
Ce script analyse automatiquement des paires segmentation / labels vertébraux
dans un dataset organisé par sujet, et calcule pour chaque sujet l'écart en
coordonnée Z entre :
- la position la plus haute atteinte par la segmentation donnée ;
- la position du label le plus haut (C1) dans le fichier de labels.

L’écart est exprimé en nombre de slices (négatif si la segmentation se rend moins
haut que le label de C1).

FONCTIONNEMENT :
----------------
1. Recherche des fichiers NIfTI de segmentation et de labels dans des dossiers
   distincts selon deux regex définis par l’utilisateur.
2. Appariement automatique des fichiers en fonction du nom sujet_contraste (ex: sub-amu01_T1w).
3. Réorientation éventuelle des images/segmentations selon l'orientation (RAS).
4. Calcul de l'écart entre le haut de la segmentation et le label le plus haut.
5. Export des résultats dans un fichier CSV dont le nom peut être modifié par l'utilisateur,
   avec une colonne par méthode de segmentation. Si le fichier existe déjà, le script vérifie si la
   colonne existe déjà. Si c'est le cas, rien n'est modifié, un message s'affiche précisant que la 
   colonne existe déjà. Si la colonne n'existe pas, elle est créée et a comme nom le nom de la méthode.

UTILISATION :
-------------
Ce script peut être appelé en ligne de commande avec les arguments suivants :

    python GT_vs_label.py \
        -segmentation_regex "regex_des_segmentations" \
        -labels_regex "regex_des_labels" \
        -d_seg "chemin/vers/les/segmentations" \
        -d_label "chemin/vers/les/labels" \
        -seg_method "NomMethode"

Exemple d'utilisation pour comparer la segmentation ground truth de contrast-agnostic avec les labels:

    python GT_vs_label.py \
        -segmentation_regex "desc-softseg_label-SC_seg" \
        -labels_regex "label-discs_dlabel" \
        -d_seg "data-multi-subject/derivatives/labels_softseg_bin" \
        -d_label "data-multi-subject/derivatives/labels" \
        -seg_method "GT_contrast-agnostic"

Les sections qui peuvent être modifiées par l'utilisateur sont précisées dans le script.

À partir du chemin spécifié pour les segmentations (-d_seg) ou pour les labels (-d_label), 
le script recherche les fichiers .nii.gz correspondant au regex donné dans tous les sous-dossiers, 
en supposant que ceux-ci sont organisés selon la structure suivante :

d_seg/
├── sub-XX1/
│   └── anat/
│       └── fichier_segmentation.nii.gz
├── sub-XX2/
│   └── anat/
│       └── fichier_segmentation.nii.gz

Les noms des dossiers intermédiaires (sub-XX) peuvent varier, mais chaque fichier doit se 
trouver dans un dossier anat/ à l'intérieur de ces sous-dossiers.

Ce script n'analyse que les fichiers provenant des contrastes T1w et T2w

ARGUMENTS :
-----------
- `-segmentation_regex` : expression régulière pour identifier les fichiers de segmentation
- `-labels_regex`       : expression régulière pour identifier les fichiers de labels
- `-d_seg`              : chemin vers le dossier contenant les segmentations
- `-d_label`            : chemin vers le dossier contenant les labels
- `-seg_method`         : nom de la méthode de segmentation (ajouté comme nom de colonne dans le CSV)

AUTEUR :
--------
Mélisende St-Amour-Bilodeau
Date : Avril 2025

"""

import os
import glob
import re
import pandas as pd
import nibabel as nib
import numpy as np
import argparse
from nibabel.orientations import aff2axcodes, axcodes2ornt, ornt_transform

CSV_FILE = "test_2004.csv" # Adapter dépendemment du nom du fichier csv de sortie désiré.

def get_parser():
    parser = argparse.ArgumentParser(
        description="Vérifie où se situe la segmentation par rapport au premier label des vertèbres.")
    parser.add_argument("-segmentation_regex", type=str, help="Expression régulière pour les fichiers de segmentation (.nii.gz)")
    parser.add_argument("-labels_regex", type=str, help="Expression régulière pour les fichiers de labels (.nii.gz)")
    parser.add_argument("-d_seg", type=str, help="Dossier contenant les fichiers de segmentation à analyser")
    parser.add_argument("-d_label", type=str, help="Dossier contenant les fichiers de labels à analyser")
    parser.add_argument("-seg_method", type=str, help="Nom de la méthode de segmentation utilisée")
    return parser



def find_files(directory, regex_pattern):
    """
    Trouve les fichiers correspondant à une expression régulière dans un dossier.
    """
    all_files = glob.glob(os.path.join(directory, "*", "anat", "*.nii.gz"), recursive=True)
    matched_files = [f for f in all_files if re.search(regex_pattern, f) and "centerline" not in f]
    return matched_files



def check_and_reorient(img, desired_orientation=('R', 'A', 'S')):
    """
    Vérifie et réoriente une image NIfTI selon l'orientation désirée.
    :param img: Image NIfTI chargée avec nibabel
    :param desired_orientation: Tuple définissant l'orientation cible (ex: ('R', 'A', 'S'))
    :return: Image potentiellement réorientée
    """
    current_orientation = aff2axcodes(img.affine)  # Obtenir l'orientation actuelle
    if current_orientation != desired_orientation:
        # Calculer la transformation d'orientation
        ornt_transform_matrix = ornt_transform(axcodes2ornt(current_orientation), axcodes2ornt(desired_orientation))
        
        # Appliquer la transformation
        reoriented_img = img.as_reoriented(ornt_transform_matrix)
        return reoriented_img
    else:
        return img



def trouver_nom_sujet_contraste(file_path):
    """
    Trouve le nom du sujet et le contraste (T1w ou T2w) à partir du nom du fichier.
    """
    match_sujet = re.search(r"(sub-[a-zA-Z0-9]+)", file_path)
    match_contraste = re.search(r"(T[1-2]w)", file_path)
    if match_sujet and match_contraste:
        return match_sujet.group(1) + match_contraste.group(1)
    return "Unknown"



def process_segmentation(seg_file, label_file, methode):
    """
    Calcule l'écart entre la segmentation et le label.
    """
    # Charger les images NIfTI
    seg_img = nib.load(seg_file)
    label_img = nib.load(label_file)

    # Vérifier et corriger l'orientation de l'image si nécessaire
    seg_img = check_and_reorient(seg_img)
    label_img = check_and_reorient(label_img)

    # Convertir en tableaux numpy
    seg_data = seg_img.get_fdata()
    label_data = label_img.get_fdata()

    # Trouver les indices des labels (excluant le fond = 0)
    label_indices = np.where(label_data != 0)[2]
    
    if label_indices.size == 0:
        return {
            "Sujet": trouver_nom_sujet_contraste(seg_file),
            methode: "N/A"
        }
    
    # Trouver la coordonnée Z maximale où il y a un label
    max_z_label = np.max(label_indices)

    # Vérifier les limites de la segmentation
    seg_indices = np.where(seg_data > 0)[2]
    
    if seg_indices.size == 0:
        return {
            "Sujet": trouver_nom_sujet_contraste(seg_file),
            methode: "N/A"
        }
    
    max_z_seg = np.max(seg_indices)

    # Calculer l'écart entre le label le plus haut et la limite supérieure de la segmentation
    ecart = max_z_seg - max_z_label

    return {
        "Sujet": trouver_nom_sujet_contraste(seg_file),
        methode: ecart
    }


def load_existing_results():
    """
    Charge le fichier CSV existant et retourne un DataFrame.
    """
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()



def save_results(new_results, methode):
    """
    Ajoute les nouveaux résultats au fichier CSV sans dupliquer des méthodes existantes pour un même sujet.
    """
    df_existing = load_existing_results()

    if not df_existing.empty and methode in df_existing.columns:
        print(f"Les résultats pour la méthode '{methode}' existent déjà. Aucun ajout effectué.")
        return

    # Filtrer les nouvelles données pour éviter d'ajouter une méthode déjà présente pour un même sujet
    new_df = pd.DataFrame(new_results)

    if df_existing.empty:
        # Si le fichier CSV est vide, on initialise avec Sujet + nouvelle colonne
        final_df = new_df
    
    else:
        # Vérifier que "Sujet" existe dans df_existing
        if "Sujet" not in df_existing.columns:
            print("Erreur : Le fichier CSV existant ne contient pas la colonne 'Sujet'. Vérifiez le format du fichier.")
            return
        
        # Fusionner les nouvelles données avec les anciennes sur la colonne "Sujet"
        final_df = df_existing.merge(new_df, on="Sujet", how="outer")

    # Sauvegarder le fichier CSV mis à jour
    final_df.to_csv(CSV_FILE, index=False)
    print(f"Résultats ajoutés sous la colonne '{methode}' et sauvegardés dans '{CSV_FILE}'.")



def main():
    """
    Applique toutes les fonctions sur les fichiers.
    """
    parser = get_parser()
    args = parser.parse_args()

    # Trouver les fichiers correspondant aux regex
    seg_files = find_files(args.d_seg, args.segmentation_regex)
    label_files = find_files(args.d_label, args.labels_regex)

    seg_dict = {trouver_nom_sujet_contraste(f): f for f in seg_files if trouver_nom_sujet_contraste(f)}
    label_dict = {trouver_nom_sujet_contraste(f): f for f in label_files if trouver_nom_sujet_contraste(f)}
    sujets_communs = set(seg_dict.keys()) & set(label_dict.keys())
    paired_files = sorted([(seg_dict[sub], label_dict[sub]) for sub in sujets_communs], key=lambda x: trouver_nom_sujet_contraste(x[0]))

    print(f"Sujets communs trouvés : {len(sujets_communs)}")


    if not seg_files or not label_files:
        print("Aucun fichier correspondant trouvé.")
        return
    
    results = []
    for seg_file, label_file in paired_files:
        print(f"Traitement : {seg_file} et {label_file}")
        result = process_segmentation(seg_file, label_file, args.seg_method)
        results.append(result)

    save_results(results, args.seg_method)



if __name__ == '__main__':
    main()
