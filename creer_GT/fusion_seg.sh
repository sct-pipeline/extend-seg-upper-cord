#!/bin/bash

###############################################################################
# Script de fusion des segmentations contrast-agnostic et PropSeg corrigées.
#
# OBJECTIF :
# ----------
# Ce script fusionne deux segmentations :
#   - une segmentation corrigée par PropSeg (partie supérieure)
#   - une segmentation contrast-agnostic (partie inférieure)
#
# La fusion s'effectue le long de l'axe Z selon une position de découpe fixée à 5 
# slices avant la dernière slice non vide de la segmentation contrast-agnostic.
#
# STRUCTURE ATTENDUE :
# --------------------
# - Les segmentations PropSeg corrigées sont dans le fichier inscrit directement dans le script par l'utilisateur.
#     (suffixe attendu : _seg_corrige.nii.gz)
# - Les segmentations contrast-agnostic sont dans : data-multi-subject/derivatives/labels_softseg_bin/
#     (format : sub-*/anat/sub-*_desc-softseg_label-SC_seg.nii.gz)
# - Les fichiers de sortie fusionnés sont enregistrés selon un chemin spécifié directement dans le script
#   par l'utilisateur.
#
# FONCTIONNEMENT :
# ----------------
# Pour chaque fichier de segmentation corrigée :
#   1. Identifie le sujet et le contraste (ex: sub-vuiisIngenia03_T1w).
#   2. Localise la segmentation contrast-agnostic correspondante.
#   3. Détermine la dernière slice non vide dans la segmentation contrast-agnostic.
#   4. Définit une position de fusion `zsplit = zmax - 5`.
#   5. Utilise un script Python temporaire pour fusionner :
#        - les slices [0:zsplit] de la segmentation contrast-agnostic
#        - les slices [zsplit+1:end] de la segmentation PropSeg corrigée
#   6. Sauvegarde l’image fusionnée avec le suffixe `_fusion.nii.gz`.
#
# UTILISATION :
# -------------
#     bash extend-seg-upper-cord/creer_GT/fusion_seg.sh
#
# AUTEUR :
# --------
# Mélisende St-Amour-Bilodeau
# Avril 2025
###############################################################################

# Dossiers
propseg_dir="test_2004/propseg_echelle_2004" # Adapter selon l'emplacement des fichiers de segmentation propseg corrigées
contrast_dir="data-multi-subject/derivatives/labels_softseg_bin"
output_dir="test_2004/output_fusion_2004" # Adapter selon l'emplacement voulu des segmentations fusionnées
mkdir -p "$output_dir"

# Script python temporaire
script_python="/tmp/fuse_segmentations.py"
cat <<EOF > "$script_python"
import nibabel as nib
import numpy as np
import sys

contrast_path = sys.argv[1]
propseg_path = sys.argv[2]
zsplit = int(sys.argv[3])
output_path = sys.argv[4]

img_contrast = nib.load(contrast_path)
img_propseg = nib.load(propseg_path)

data_contrast = img_contrast.get_fdata()
data_propseg = img_propseg.get_fdata()

if data_contrast.shape != data_propseg.shape:
    raise ValueError(f"Dimensions mismatch: contrast={data_contrast.shape}, propseg={data_propseg.shape}")

lower = data_contrast[:, :, :zsplit+1]
upper = data_propseg[:, :, zsplit+1:]

fused_data = np.concatenate((lower, upper), axis=2)

fused_img = nib.Nifti1Image(fused_data, img_contrast.affine, img_contrast.header)
nib.save(fused_img, output_path)
EOF


echo -e "\n========== Début fusion contrast-agnostic + propseg corrigée ==========\n"

for propseg_file in "$propseg_dir"/*.nii.gz; do
    filename=$(basename "$propseg_file")
    sujet_contraste="${filename%_seg_corrige.nii.gz}"
    sujet=$(echo "$sujet_contraste" | cut -d'_' -f1)
    contraste=$(echo "$sujet_contraste" | cut -d'_' -f2)

    echo "Fusion pour ${sujet_contraste}"

    contrast_seg=$(find "$contrast_dir" -path "*/${sujet}/anat/${sujet}*${contraste}*_desc-softseg_label-SC_seg.nii.gz" | head -n 1)

    if [[ ! -f "$contrast_seg" ]]; then
        echo "Contrast-agnostic manquant pour $sujet_contraste"
        continue
    fi

    zmax=$(python3 -c "
import nibabel as nib
import numpy as np
img = nib.load('$contrast_seg')
data = img.get_fdata()
z = data.shape[2]
found = 0
for i in reversed(range(z)):
    if np.any(data[:, :, i]):
        found = i
        break
print(found)
")

    if [[ -z "$zmax" ]]; then
        echo "Erreur lecture Z max pour $contrast_seg"
        continue
    fi

    zsplit=$((zmax - 5))
    if (( zsplit < 0 )); then
        echo "Z max trop petit pour $sujet_contraste (z=$zmax)"
        continue
    fi

    fusion_file="${output_dir}/${sujet_contraste}_fusion.nii.gz"
    python3 "$script_python" "$contrast_seg" "$propseg_file" "$zsplit" "$fusion_file"

    echo "Fusion enregistrée : $fusion_file"
done

echo -e "\n Toutes les fusions sont terminées."

# Nettoyage
touch "$script_python" && rm "$script_python"

