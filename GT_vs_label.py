# Ce script vise à vérifier si la segmentation dépasse légèrement label de la vertèbre C1

import nibabel as nib
import numpy as np
import argparse

def get_parser():
    parser = argparse.ArgumentParser(
        description="Vérifie si la segmentation dépasse légèrement le premier label des vertèbres.")
    parser.add_argument("-segmentation", type=str, help="Chemin du fichier NIfTI de segmentation (.nii.gz)")
    parser.add_argument("-labels", type=str, help="Chemin du fichier NIfTI des labels des vertèbres (.nii.gz)")
    parser.add_argument("-margin", type=int, default=5, help="Nombre de slices au-dessus du label à vérifier")
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

    # Trouver la coordonnée Z maximale où il y a un label
    max_z_label = np.max(label_indices)
    
    # Définir là où on veut vérifier si la segmentation se rend
    z_upper_limit = max_z_label + args.margin  # Définir la limite supérieure
    z_upper_limit = min(z_upper_limit, seg_data.shape[2] - 1)  # S'assurer qu'on ne dépasse pas les dimensions

    # Vérifier les limites de la segmentation
    seg_indices = np.where(seg_data > 0)[2]
    min_z_seg = np.min(seg_indices)  # Premier niveau Z où la segmentation est présente
    max_z_seg = np.max(seg_indices)
    print(f"La segmentation commence à Z={min_z_seg} et se termine à Z={max_z_seg}.")

    # Vérifier si la segmentation atteint cette coordonnée Z
    seg_above_label = seg_data[:, :, z_upper_limit] > 0  # Pixels segmentés à ce niveau Z
    
    if np.any(seg_above_label):
        print(f"La segmentation atteint {args.margin} slices au dessus du premier label (Z={seg_above_label}).")
        return True
    else:
        print(f"La segmentation n'atteint pas {args.margin} slices au dessus du premier label (Z={seg_above_label}).")
        return False

if __name__ == '__main__':
    main()
