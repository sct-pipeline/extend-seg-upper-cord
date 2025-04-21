#!/bin/bash

###############################################################################
# Script de calcul automatique du facteur d’échelle entre une segmentation 
# PropSeg et le GT (Ground Truth) de contrast-agnostic.
#
# OBJECTIF :
# ----------
# Pour chaque fichier de segmentation PropSeg trouvé dans un dossier donné,
# ce script :
#   1. Recherche le fichier de segmentation de référence (GT de contrast-agnostic) correspondant.
#   2. Recherche le fichier de labels vertébraux associé.
#   3. Réoriente le fichier de labels au format RPI si nécessaire.
#   4. Calcule la surface moyenne de la moelle épinière (CSA) entre C2 et C4
#      à partir des segmentations PropSeg et GT en utilisant `sct_process_segmentation`.
#   5. Calcule le facteur d’échelle = moyenne_CSA_GT / moyenne_CSA_PropSeg.
#   6. Enregistre les résultats dans un fichier CSV avec :
#         Sujet, CSA_PropSeg, CSA_GT, Facteur_Echelle
#
# ORGANISATION DES FICHIERS :
# ---------------------------
# - Les segmentations PropSeg sont attendues dans le dossier spécifié par `propseg_dir`.
# - Les segmentations GT et les labels sont cherchés automatiquement dans `data-multi-subject/derivatives/`.
# - Chaque sujet est identifié par un nom de fichier de type : sub-XXX_contraste.nii.gz
#
# UTILISATION :
# -------------
# Le script est autonome et peut être lancé tel quel :
#
#     bash extend-seg-upper-cord/creer_GT/calcul_facteur_echelle.sh
#
# Il génère un fichier CSV.
# 
# L'utilisateur peut modifier les chemins directement dans le script avant de le lancer.
# Les endroits à modifier sont identifiés par des commentaires dans le script.
#
# AUTEUR :
# --------
# Mélisende St-Amour-Bilodeau
# Avril 2025
###############################################################################

# Dossiers
propseg_dir="correction/dossier_vide/anat" # À adapter dépendemment de l'emplacement des segmentations propseg
output_csv="facteurs_echelle_1904.csv" # À adapter dépendemment du nom du fichier CSV de sortie voulu
echo "Sujet,CSA_PropSeg,CSA_GT,Facteur_Echelle" > "$output_csv"

# Pour chaque fichier PropSeg
for propseg_path in "$propseg_dir"/sub-*.nii.gz; do
    propseg_file=$(basename "$propseg_path")
    sujet=$(echo "$propseg_file" | cut -d'_' -f1)  # ex: sub-geneva01
    contraste=$(echo "$propseg_file" | cut -d'_' -f3)  

    echo $sujet
    echo $contraste

    # Rechercher le GT correspondant (premier match)
    gt_path=$(find data-multi-subject/derivatives/labels_softseg_bin/ -path "*/${sujet}/anat/${sujet}_${contraste}_desc-softseg_label-SC_seg.nii.gz" | head -n 1)

    # Rechercher le fichier de labels
    label_path=$(find data-multi-subject/derivatives/labels/ -path "*/${sujet}/anat/${sujet}_${contraste}_label-discs_dlabel.nii.gz" | head -n 1)

    # Réorienter
    label_rpi="${sujet}_${contraste}_label_RPI.nii.gz"
    sct_image -i "$label_path" -setorient RPI -o "$label_rpi" 


    if [[ ! -f "$gt_path" || ! -f "$label_path" ]]; then
        echo "Fichiers manquants pour $sujet, saut..."
        continue
    fi

    echo "Traitement de $sujet"

    # Temp files
    tmp_csa_propseg="tmp_propseg_${sujet}_${contraste}.csv"
    tmp_csa_gt="tmp_gt_${sujet}_${contraste}.csv"

    # CSA PropSeg
    sct_process_segmentation -i "$propseg_path" -perslice 1 -vert 2:4 -vertfile "$label_rpi" -o "$tmp_csa_propseg" -v 0

    # CSA GT
    sct_process_segmentation -i "$gt_path" -perslice 1 -vert 2:4 -vertfile "$label_rpi" -o "$tmp_csa_gt" -v 0

    if [[ ! -s "$tmp_csa_propseg" || ! -s "$tmp_csa_gt" ]]; then
        echo "${sujet}_${contraste},Fichier CSV vide" >> "$output_csv"
        continue
    fi

    # 3. Calcul du facteur en Python
    facteur_line=$(python3 -c "
import pandas as pd
try:
    df_prop = pd.read_csv('$tmp_csa_propseg')
    df_gt = pd.read_csv('$tmp_csa_gt')
    csa_prop = df_prop['MEAN(area)'].mean()
    csa_gt = df_gt['MEAN(area)'].mean()
    facteur = round(csa_gt / csa_prop, 4)
    print(f'{csa_prop},{csa_gt},{facteur}')
except Exception as e:
    print('NaN,NaN,NaN')
")
    echo "${sujet}_${contraste},$facteur_line" >> "$output_csv"

    # Suppression des fichiers temporaires
    rm -f "$label_rpi" "$tmp_csa_propseg" "$tmp_csa_gt"

done

echo "Terminé ! Résultats enregistrés dans $output_csv"