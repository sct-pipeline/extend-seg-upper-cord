#!/bin/bash

# Dossiers
propseg_dir="correction/dossier_vide/anat" # Adapt depending on where the files are located
output_csv="facteurs_echelle_1904.csv" # Adapt depending on how you want to name your file
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

    # 1. CSA PropSeg
    sct_process_segmentation -i "$propseg_path" -perslice 1 -vert 2:4 -vertfile "$label_rpi" -o "$tmp_csa_propseg" -v 0

    # 2. CSA GT
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
done

echo "Terminé ! Résultats enregistrés dans $output_csv"