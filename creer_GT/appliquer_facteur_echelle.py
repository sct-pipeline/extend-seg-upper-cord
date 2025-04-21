"""
Script pour appliquer les facteurs d'échelle aux segmentations propseg pour qu'elles
soient compatibles avec les segmentations GT de contrast-agnostic.

OBJECTIF :
----------
Ce script applique un facteur d’échelle aux segmentations binaires
de la moelle épinière (obtenues par PropSeg), **slice par slice**, en 2D, pour ajuster 
leur surface moyenne (CSA).

Le facteur utilisé par sujet est issu d’un fichier CSV, où il a été calculé comme :
    facteur = moyenne_CSA_GT / moyenne_CSA_PropSeg

FONCTIONNEMENT :
----------------
1. Lit un fichier CSV contenant les sujets, leurs contrastes (T1w ou T2w),
   et le facteur d’échelle à appliquer (`Facteur_Echelle`).
2. Pour chaque sujet :
   - Charge la segmentation d’entrée au format `.nii.gz`.
   - Applique un **zoom isotrope slice par slice (XY)** avec recentrage basé sur le centre de masse.
   - Sauvegarde la nouvelle segmentation mise à l’échelle.
3. Les images sont sauvegardées dans un dossier de sortie avec le suffixe `_seg_corrige.nii.gz`.

STRUCTURE ATTENDUE DES DONNÉES :
--------------------------------
- Le CSV doit contenir les colonnes suivantes :
    - `Sujet` (ex: sub-geneva01_T1w)
    - `CSA_PropSeg`
    - `CSA_GT`
    - `Facteur_Echelle`

- Les segmentations d’entrée doivent être dans `input_seg_dir`, et suivre le nom :
    sub-XXX_contraste_propseg.nii.gz

- Les segmentations corrigées sont sauvegardées dans `output_seg_dir`.

UTILISATION :
-------------
Le script est prévu pour être lancé directement :

    python appliquer_facteur_echelle.py

(Modifier les chemins `csv_path`, `input_seg_dir`, `output_seg_dir` dans les paramètres du haut du script.)

AUTEUR :
--------
Mélisende St-Amour-Bilodeau  
Date : Avril 2025
"""

import nibabel as nib
import numpy as np
import pandas as pd
import os
from scipy.ndimage import zoom
from scipy.ndimage import center_of_mass

# === PARAMÈTRES ===
csv_path = "facteurs_echelle_filtre_1904.csv" # À modifier selon le nom du fichier CSV contenant les facteurs d'échelle
input_seg_dir = "correction/dossier_vide/anat"  # À modifier selon le chemin contenant les segmentations auxquelles appliquer le facteur d'échelle
output_seg_dir = "correction_2004/propseg_echelle"  # À modifier selon là où on veut enregistrer les segmentations modifiées
os.makedirs(output_seg_dir, exist_ok=True)

def scale_segmentation_per_slice(input_path, output_path, scale_factor):
    img = nib.load(input_path)
    data = img.get_fdata()
    affine = img.affine

    output = np.zeros_like(data)

    for z in range(data.shape[2]):
        slice_bin = data[:, :, z]
        if np.sum(slice_bin) == 0:
            continue

        # Zoom de la slice (scaling)
        zoomed_img = zoom(slice_bin, zoom=(scale_factor, scale_factor), order=0)

        # Calcul du centre de masse original et zoomé
        original_com = center_of_mass(slice_bin)
        zoomed_com = center_of_mass(zoomed_img)

        # Décalage requis pour recentrer
        shift_x = int(round(original_com[0] - zoomed_com[0]))
        shift_y = int(round(original_com[1] - zoomed_com[1]))

        # Dimensions
        h, w = slice_bin.shape
        zh, zw = zoomed_img.shape

        # Création de la nouvelle slice vide
        zoomed_resized = np.zeros_like(slice_bin)

        # Coordonnées de placement (dans la slice d’origine)
        x_start = max(0, shift_x)
        y_start = max(0, shift_y)
        x_end = min(h, shift_x + zh)
        y_end = min(w, shift_y + zw)

        # Coordonnées de découpe (dans l’image zoomée)
        zoom_x_start = max(0, -shift_x)
        zoom_y_start = max(0, -shift_y)
        zoom_x_end = zoom_x_start + (x_end - x_start)
        zoom_y_end = zoom_y_start + (y_end - y_start)

        # Insertion de l’image zoomée dans la slice finale
        zoomed_resized[x_start:x_end, y_start:y_end] = zoomed_img[zoom_x_start:zoom_x_end, zoom_y_start:zoom_y_end]

        output[:, :, z] = zoomed_resized

    nib.save(nib.Nifti1Image(output, affine), output_path)
    print(f"Sauvegardé : {output_path}")


# === LECTURE CSV ET TRAITEMENT ===
df = pd.read_csv(csv_path)

for idx, row in df.iterrows():
    subject_contrast = row["Sujet"]
    csa_propseg = row["CSA_PropSeg"]
    csa_gt = row["CSA_GT"]
    facteur = row["Facteur_Echelle"]
    sujet, contraste = subject_contrast.split('_')

     # Skip si facteur est vide ou NaN
    if pd.isna(facteur):
        print(f"Facteur vide ou NaN pour {subject_contrast}, skip...")
        continue

    try:
        facteur = float(facteur)
    except:
        print(f"Facteur non convertible pour {subject_contrast}, skip...")
        continue

    input_seg = os.path.join(input_seg_dir, f"{sujet}_{contraste}_propseg.nii.gz")
    output_seg = os.path.join(output_seg_dir, f"{subject_contrast}_seg_corrige.nii.gz")

    if not os.path.exists(input_seg):
        print(f"Fichier manquant : {input_seg}")
        continue

    print(f"Traitement de {subject_contrast} avec facteur {facteur}")
    scale_segmentation_per_slice(input_seg, output_seg, facteur)

print("Terminé.")