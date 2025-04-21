#!/bin/bash

###############################################################################
# Script de génération automatique de rapports de qualité (QC) pour plusieurs segmentations.
#
# OBJECTIF :
# ----------
# Ce script génère des rapports QC (Quality Control) visuels pour évaluer 
# la qualité des segmentations.
#
# Deux types de QC sont générés pour chaque sujet :
#   1. Une vérification par slice via `sct_deepseg_sc`
#   2. Une vérification avec la coupe saggitale via `sct_label_vertebrae`
#
# STRUCTURE ATTENDUE :
# --------------------
# - Les segmentations sont stockées dans le chemin spécifié par l'utilisateur directement dans le script
#     (nom attendu : sub-XXX_contraste_fusion_cropped.nii.gz)
# - Les images anatomiques correspondantes doivent être dans :
#     data-multi-subject/sub-XXX/anat/sub-XXX_contraste.nii.gz
#
# FONCTIONNEMENT :
# ----------------
# Pour chaque segmentation dans 'fusion_dir' (spécifié par l'utilisateur) :
#   1. Identifie le sujet (ex: sub-XXX) et le contraste (T1w/T2w).
#   2. Recherche l’image anatomique correspondante.
#   3. Génère deux types de rapports QC avec la commande 'sct_qc' :
#        - sct_deepseg_sc
#        - sct_label_vertebrae
#   4. Sauvegarde les rapports dans le dossier 'qc_output/' (spécifié par l'utilisateur).
#
# UTILISATION :
# -------------
#     bash extend-seg-upper-cord/creer_GT/qc_fusion_all.sh
#
# AUTEUR :
# --------
# Mélisende St-Amour-Bilodeau
# Avril 2025
###############################################################################

# Dossiers
fusion_dir="test_2004/output_fusion_cropped_2004" # Adapt depending on where your segmentations are
qc_output="qc_report_2104" # Adapt to what you want your output to be

mkdir -p "$qc_output"

# Boucle sur toutes les segmentations fusionnées
for fusion_seg in "$fusion_dir"/*.nii.gz; do
    subj_name=$(basename "$fusion_seg")  
    sujet=$(echo "$subj_name" | cut -d'_' -f1)         
    contraste=$(echo "$subj_name" | cut -d'_' -f2)       
    anat_img=$(find data-multi-subject/$sujet/anat -name "${sujet}_${contraste}.nii.gz" | head -n 1)
 
    echo -e "\n Traitement de: $subj_name"

    if [[ ! -f "$anat_img" ]]; then
        echo "Image anatomique non trouvée pour $subj_name"
        continue
    fi

    # Génère un QC overlay (vue axiale complète, overlay segmentation + image)
    sct_qc -i "$anat_img" -s "$fusion_seg" -p sct_deepseg_sc -qc "$qc_output" -qc-subject "$subj_name"

    # Lancement de sct_label_vertebrae (et QC associé automatiquement généré)
    sct_qc -i "$anat_img" -s "$fusion_seg" -p sct_label_vertebrae -qc "$qc_output" -qc-subject "$subj_name"

    echo "QC généré pour $subj_name"
done

echo -e "\n Tous les QC ont été générés dans: $qc_output"


