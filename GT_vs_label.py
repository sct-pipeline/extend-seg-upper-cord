import nibabel as nib
import numpy as np
import argparse

def get_parser():
    parser = argparse.ArgumentParser(
        description="Vérifie si la segmentation touche le premier label des vertèbres.")
    parser.add_argument("-segmentation", type=str, help="Chemin du fichier NIfTI de segmentation (.nii.gz)")
    parser.add_argument("-labels", type=str, help="Chemin du fichier NIfTI des labels des vertèbres (.nii.gz)")

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # Charger les images NIfTI
    seg_img = nib.load(args.segmentation)
    label_img = nib.load(args.labels)

    # Convertir en tableaux numpy
    seg_data = seg_img.get_fdata()
    label_data = label_img.get_fdata()

    # Trouver les indices des labels (excluant le fond = 0)
    label_indices = np.where(label_data != 0)[2]
    
    if label_indices.size == 0:
        print("Aucun label trouvé dans l'image des labels.")
        return False

    # Trouver la coordonnée Z minimale où il y a un label
    max_z_label = np.max(label_indices)
    
    seg_indices = np.where(seg_data > 0)[2]
    min_z_seg = np.min(seg_indices)  # Premier niveau Z où la segmentation est présente
    max_z_seg = np.max(seg_indices)
    print(f"La segmentation commence à Z={min_z_seg} et se termine à Z={max_z_seg}.")


    # Vérifier si la segmentation atteint cette coordonnée Z
    seg_at_max_z = seg_data[:, :, max_z_label] > 0  # Pixels segmentés à ce niveau Z
    
    if np.any(seg_at_max_z):
        print(f"La segmentation atteint le premier label (Z={max_z_label}).")
        return True
    else:
        print(f"La segmentation NE touche PAS le premier label (Z={max_z_label}).")
        return False

if __name__ == '__main__':
    main()
