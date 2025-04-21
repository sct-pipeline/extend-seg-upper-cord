#!/bin/bash

###############################################################################
# Script de "crop" (découpe) vertical des segmentations fusionnées autour de C1.
#
# OBJECTIF :
# ----------
# Ce script découpe les segmentations fusionnées (contrast-agnostic + PropSeg)
# en gardant uniquement les slices situées au-dessus de C1 (jusqu’à 10 slices plus haut).
#
# STRUCTURE DES DONNÉES :
# ------------------------
# - L'emplacement des segmentations fusionnées doit être modifié directement dans le script par l'utilisateur.
#     (nom attendu : sub-XXX_contraste_fusion.nii.gz)
# - Les fichiers de labels vertébraux (contenant C1) doivent être dans :
#     data-multi-subject/derivatives/labels/sub-XXX/anat/sub-XXX_contraste_label-discs_dlabel.nii.gz
# - Les segmentations recadrées sont enregistrées selon l'emplacement spécifié directement dans le script par 
#     l'utilisateur.
#
# FONCTIONNEMENT :
# ----------------
# Pour chaque segmentation fusionnée :
#   1. Identifie le sujet et le contraste.
#   2. Charge le fichier de labels vertébraux et localise la slice Z correspondant à C1 (valeur label != 0).
#   3. Définit une position de découpe `z_max = z_c1 + 10`.
#   4. Applique un masque conservant uniquement les slices de Z = 0 jusqu’à Z = z_max.
#   5. Sauvegarde la nouvelle image segmentée avec le suffixe `_fusion_cropped.nii.gz`.
#
# UTILISATION :
# -------------
#     bash extend-seg-upper-cord/creer_GT/crop_above_C1.sh
#
# AUTEUR :
# --------
# Mélisende St-Amour-Bilodeau
# Avril 2025
###############################################################################

fusion_dir="test_2004/output_fusion_2004" # Adapter selon l'emplacement des segmentation que l'on veut crop
label_dir="data-multi-subject/derivatives/labels"
output_dir="test_2004/output_fusion_cropped_2004" # Adapter selon l'emplacement désiré des fichiers résultants
mkdir -p "$output_dir"

echo "Début du crop (10 slices au-dessus de C1)"

for fusion_seg in "$fusion_dir"/*_fusion.nii.gz; do
    subj_name=$(basename "$fusion_seg" _fusion.nii.gz)
    subj=${subj_name%%_*}
    contraste=$(echo "$subj_name" | cut -d'_' -f2)
    label_file="$label_dir/$subj/anat/${subj}_${contraste}_label-discs_dlabel.nii.gz"

    if [[ ! -f "$label_file" ]]; then
        echo "Label manquant pour $subj_name"
        continue
    fi

    echo "Traitement de $subj_name..."

    python3 <<EOF
import nibabel as nib
import numpy as np
import os

label_img = nib.load("$label_file")
label_data = label_img.get_fdata()

# Trouver l'index Z du label C1 (valeur == 1)
indices = np.where(label_data != 0)[2]
if indices.size == 0:
    print("C1 introuvable pour $subj_name")
    exit()

z_c1 = np.max(indices)
z_max = z_c1 + 10

# Charger la segmentation fusionnée
seg_img = nib.load("$fusion_seg")
seg_data = seg_img.get_fdata()

# Vérification des dimensions
if z_c1 >= seg_data.shape[2]:
    print(f"C1 est hors des dimensions de la segmentation pour $subj_name")
    exit()

# Masquage des slices au-dessus de z_max
masked_data = np.zeros_like(seg_data)
masked_data[:, :, :z_max] = seg_data[:, :, :z_max]
masked_img = nib.Nifti1Image(masked_data.astype(np.uint8), seg_img.affine, seg_img.header)

output_path = os.path.join("$output_dir", f"${subj_name}_fusion_cropped.nii.gz")
nib.save(masked_img, output_path)
print(f" Sauvegardé : {output_path}")
EOF


done

echo "Tous les fichiers ont été recadrés avec succès"
