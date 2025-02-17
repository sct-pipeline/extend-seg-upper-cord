# Ce script vise à vérifier si la segmentation dépasse légèrement label de la vertèbre C1

import nibabel as nib
import numpy as np
import argparse
from nibabel.orientations import aff2axcodes, axcodes2ornt, ornt_transform


def get_parser():
    parser = argparse.ArgumentParser(
        description="Vérifie si la segmentation dépasse légèrement le premier label des vertèbres.")
    parser.add_argument("-segmentation", type=str, help="Chemin du fichier NIfTI de segmentation (.nii.gz)")
    parser.add_argument("-labels", type=str, help="Chemin du fichier NIfTI des labels des vertèbres (.nii.gz)")
    parser.add_argument("-margin", type=int, default=5, help="Nombre de slices au-dessus du label à vérifier")
    return parser

def check_and_reorient(img, desired_orientation=('R', 'A', 'S')):
    """
    Vérifie et réoriente une image NIfTI selon l'orientation désirée.
    :param img: Image NIfTI chargée avec nibabel
    :param desired_orientation: Tuple définissant l'orientation cible (ex: ('R', 'A', 'S'))
    :return: Image potentiellement réorientée
    """
    current_orientation = aff2axcodes(img.affine)  # Obtenir l'orientation actuelle
    if current_orientation != desired_orientation:
        print(f"Réorientation nécessaire : {current_orientation} -> {desired_orientation}")
        
        # Calculer la transformation d'orientation
        ornt_transform_matrix = ornt_transform(axcodes2ornt(current_orientation), axcodes2ornt(desired_orientation))
        
        # Appliquer la transformation
        reoriented_img = img.as_reoriented(ornt_transform_matrix)
        return reoriented_img
    else:
        print("L'image est déjà correctement orientée.")
        return img

def main():
    parser = get_parser()
    args = parser.parse_args()
    
    # Charger les images NIfTI
    seg_img = nib.load(args.segmentation)
    label_img = nib.load(args.labels)

    # Vérifier et corriger l'orientation de l'image si nécessaire
    seg_img = check_and_reorient(seg_img)
    label_img = check_and_reorient(label_img)

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
