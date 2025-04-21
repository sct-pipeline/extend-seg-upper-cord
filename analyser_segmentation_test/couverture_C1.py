"""
Script d’évaluation de la couverture du segment C1 par contrast-agnostic et par le modèle
entraîné, ainsi que le gain de pourcentage de couverture.

OBJECTIF :
----------
Ce script mesure le pourcentage de couverture du segment vertébral C1 par deux méthodes
de segmentation de la moelle épinière :
  - une segmentation contrast-agnostic (`*_contrast.nii.gz`)
  - une segmentation par le nouveau modèle (`*_seg_nnunet.nii.gz`)

La couverture est évaluée par rapport à une segmentation de référence (GT) sur la région C1,
définie comme l’intervalle entre les deux labels vertébraux les plus supérieurs dans un
fichier de labels (C2 et C1).

FONCTIONNEMENT :
----------------
Pour chaque sujet/contraste :
1. Charge les fichiers :
   - Segmentation GT
   - Segmentation contrast-agnostic
   - Segmentation obtenue par le nouveau modèle
   - Fichier de labels vertébraux (`*_label-discs_dlabel.nii.gz`)
2. Localise C1 à partir du fichier de labels.
3. Calcule, dans cette région C1, le pourcentage de voxels GT couverts par chaque segmentation.
4. Calcule le gain de couverture entre la segmentation étendue et la segmentation d'origine.
5. Exporte un tableau récapitulatif dans un fichier CSV avec :
   - `subject`
   - `coverage_contrast_agnostic (%)`
   - `coverage_extend_seg (%)`
   - `gain (%)`

FORMAT DES FICHIERS ATTENDUS :
-------------------------------
- Les noms doivent suivre la structure attendue, par exemple :
    - sub-XXX_T1w_seg_nnunet.nii.gz
    - sub-XXX_T1w_contrast.nii.gz
    - sub-XXX_T1w__desc-softseg_label-SC_seg.nii.gz
    - sub-XXX_T1w_label-discs_dlabel.nii.gz

- Les répertoires suivants sont utilisés :
    - `seg_extend_dir` : répertoire des segmentations obtenues avec le nouveau modèle
    - `seg_contrast_agnostic_dir` : répertoire des segmentations contrast-agnostic
    - `seg_gt_dir` : répertoire des segmentations GT 
    - `label_path` : répertoire des labels vertébraux pour localiser C1
Les répertoires peuvent être modifiés directement dans le script par l'utilisateur

AUTEUR :
--------
Mélisende St-Amour-Bilodeau  
Avril 2025
"""

import os
import nibabel as nib
import numpy as np
import pandas as pd
from glob import glob
from pathlib import Path

def compute_c1_coverage(gt_seg, pred_seg, label_sup, label_inf):
    mask_c1 = np.zeros_like(gt_seg, dtype=bool)
    if label_sup > label_inf:
        mask_c1[:, :, label_inf:label_sup+1] = True
    else:
        mask_c1[:, :, label_sup:label_inf+1] = True

    gt_c1 = (gt_seg > 0) & mask_c1
    pred_c1 = (pred_seg > 0) & mask_c1

    total_gt = np.sum(gt_c1)
    if total_gt == 0:
        return 0.0

    covered = np.sum(pred_c1 & gt_c1)
    return (covered / total_gt) * 100

# === Chemins ===
label_path = "data-multi-subject/derivatives/labels" 
seg_contrast_agnostic_dir = "output_contrast" # À modifier dépendemment de où se trouvent les segmentations contrast-agnostic
seg_extend_dir = "output_extend-seg-upper-cord_2004" # À modifier dépendemment de où se trouvent les segmentations obtenues par le modèle entraîné
seg_gt_dir = "data-multi-subject/derivatives/labels_softseg_bin"
output_csv_path = "c1_coverage_results_2004.csv" # À modifier dépendemment du fichier output désiré



# Boucler sur les segmentations extend
results = []

for seg_path in sorted(glob(os.path.join(seg_extend_dir, "*.nii.gz"))):
    filename = Path(seg_path).name  # ex: sub-unf01_T1w_seg_nnunet.nii.gz
    subject_and_contrast = filename.replace("_seg_nnunet.nii.gz", "")
    print(f"Traitement de {subject_and_contrast}")
    subject = subject_and_contrast.split('_')[0]
    seg_extend_data = nib.load(seg_path).get_fdata()

    contrast_file = os.path.join(seg_contrast_agnostic_dir, f"{subject_and_contrast}_contrast.nii.gz")
    gt_file = os.path.join(seg_gt_dir, f"{subject}/anat/{subject_and_contrast}_desc-softseg_label-SC_seg.nii.gz")

    if not os.path.exists(contrast_file):
        print(f"Fichier contrast manquant pour {subject_and_contrast}")
        continue
    if not os.path.exists(gt_file):
        print(f"Fichier gt manquant pour {subject_and_contrast}")
        continue
    
    seg_contrast_data = nib.load(contrast_file).get_fdata()
    gt_data = nib.load(gt_file).get_fdata()

    label_file = os.path.join(label_path, subject, "anat", f"{subject_and_contrast}_label-discs_dlabel.nii.gz")

    # Charger les labels
    label_img = nib.load(label_file)
    label_data = label_img.get_fdata()

    # Trouver toutes les coordonnées de labels > 0
    coords = np.argwhere(label_data > 0)

    # Trier par Z décroissant (du plus haut vers le plus bas)
    sorted_coords = coords[np.argsort(coords[:, 2])[::-1]]

    # Récupérer les deux plus hauts labels (Z les plus grands)
    label_sup = int(sorted_coords[0][2])  # haut de C1
    label_inf = int(sorted_coords[1][2])  # bas de C1

    print(f"Label supérieur (haut C1) : slice z = {label_sup}")
    print(f"Label inférieur (bas C1) : slice z = {label_inf}")  

    coverage_contrast = compute_c1_coverage(gt_data, seg_contrast_data, label_sup, label_inf)
    coverage_extend = compute_c1_coverage(gt_data, seg_extend_data, label_sup, label_inf)
    gain = coverage_extend - coverage_contrast


    results.append({
        "subject": subject_and_contrast,
        "coverage_contrast_agnostic (%)": coverage_contrast,
        "coverage_extend_seg (%)": coverage_extend,
        "gain (%)": gain
    })

# Sauvegarder
df = pd.DataFrame(results)
df.to_csv(output_csv_path, index=False)
print(f"Résultats sauvegardés dans {output_csv_path}")
