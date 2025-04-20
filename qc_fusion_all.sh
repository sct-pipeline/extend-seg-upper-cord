#!/bin/bash

# Dossiers
fusion_dir="correction/propseg_fusion_cropped_2004" # Adapt depending on where your segmentations are
to_crop="_fusion_cropped" # Adapt depending on what extra words are at the end of your file names
qc_output="qc_report_final_2004" # Adapt to what you want your output to be

mkdir -p "$qc_output"

# Boucle sur toutes les segmentations fusionnées
for fusion_seg in "$fusion_dir"/*.nii.gz; do
    subj_name=$(basename "$fusion_seg" "$to_crop")  
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


