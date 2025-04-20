import nibabel as nib
import numpy as np
import pandas as pd
import os
from scipy.ndimage import zoom
from scipy.ndimage import center_of_mass

# === PARAMÈTRES ===
csv_path = "facteurs_echelle_filtre_1904.csv"
input_seg_dir = "correction/dossier_vide/anat"  # répertoire des segmentations originales
output_seg_dir = "correction_2004/propseg_echelle"  # où sauvegarder les segmentations modifiées
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

    input_seg = os.path.join(input_seg_dir, f"{sujet}_space-other_{contraste}_seg.nii.gz")
    output_seg = os.path.join(output_seg_dir, f"{subject_contrast}_seg_corrige.nii.gz")

    if not os.path.exists(input_seg):
        print(f"Fichier manquant : {input_seg}")
        continue

    print(f"Traitement de {subject_contrast} avec facteur {facteur}")
    scale_segmentation_per_slice(input_seg, output_seg, facteur)

print("Terminé.")