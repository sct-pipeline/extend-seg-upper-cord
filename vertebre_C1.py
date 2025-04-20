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
label_path = "data-multi-subject/derivatives/labels"  # fichier avec 2 labels : 1 = haut de C1, 2 = bas de C1
seg_contrast_agnostic_dir = "output_contrast"
seg_extend_dir = "output_extend-seg-upper-cord_2004"
seg_gt_dir = "propseg_fusion_cropped_2004"
output_csv_path = "c1_coverage_results_2004.csv"



# Boucler sur les segmentations extend
results = []

for seg_path in sorted(glob(os.path.join(seg_extend_dir, "*.nii.gz"))):
    filename = Path(seg_path).name  # ex: sub-unf01_T1w_seg_nnunet.nii.gz
    subject_and_contrast = filename.replace("_seg_nnunet.nii.gz", "")
    print(f"Traitement de {subject_and_contrast}")
    subject = subject_and_contrast.split('_')[0]
    seg_extend_data = nib.load(seg_path).get_fdata()

    contrast_file = os.path.join(seg_contrast_agnostic_dir, f"{subject_and_contrast}_contrast.nii.gz")
    gt_file = os.path.join(seg_gt_dir, f"{subject_and_contrast}_fusion_cropped.nii.gz")

    if not os.path.exists(contrast_file):
        print(f"Fichier contrast manquant pour {subject_and_contrast}")
        continue
    if not os.path.exists(gt_file):
        print(f"Fichier gt manquant pour {subject_and_contrast}, recherche dans data-multi-subject")
        gt_file = os.path.join(f"data-multi-subject/derivatives/labels_softseg_bin/{subject}/anat", f"{subject_and_contrast}_desc-softseg_label-SC_seg.nii.gz")

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
