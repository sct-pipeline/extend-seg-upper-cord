import argparse
import pandas as pd
import os
import glob
import re
import subprocess

def get_parser():
    parser = argparse.ArgumentParser(
        description="Lance la segmentation propseg avec des paramètres modifiés si la valeur pour propseg dans le fichier CSV est inférieure à 5.")
    parser.add_argument("-f", type=str, help="Fichier CSV contenant le nom des sujets à analyser")
    parser.add_argument("-max_area", type=float, help="Valeur de max-area dans propseg: [mm^2], stop condition (affects only the Z propogation): maximum cross-sectional area. Default is 120.")
    parser.add_argument("-max_deformation", type=float, help="Valeur de max-deformation dans propseg: [mm], stop condition (affects only the Z propogation): maximum deformation per iteration. Default is 2.5")
    parser.add_argument("-min_contrast", type=float, help="Valeur de min-contrast dans propseg: [intensity value], stop condition (affects only the Z propogation): minimum local SC/CSF contrast, default is 50")
    return parser



def liste_fichiers(file_path):
    # Charger le fichier CSV
    df = pd.read_csv(file_path)
    
    # Filtrer les sujets avec un propseg < 5 et exclure les valeurs NaN
    df_filtered = df[(df['propseg'] < 5) & (df['propseg'].notna())]

    # Extraire et séparer le nom des sujets
    subject_dict = {}

    for name in df_filtered['Sujet']:
        parts = name.rsplit('T', 1)
        if len(parts) == 2:
            sujet = parts[0]
            contraste = 'T' + parts[1]
            if sujet in subject_dict:
                subject_dict[sujet].append(contraste)
            else:
                subject_dict[sujet] = [contraste]
    
    # Trouver fichiers
    matched_files = []
    for sujet, contrastes in subject_dict.items():
        all_files = glob.glob(os.path.join("data-multi-subject/derivatives/data_preprocessed", sujet, "anat", "*.nii.gz"), recursive=True)
        for contraste in contrastes:
            matched_files.extend([f for f in all_files if re.search(contraste, f)])
    
    return matched_files


def trouver_nom_sujet(file_path):
    match = re.search(r"(sub-[a-zA-Z0-9]+)", file_path)
    return match.group(1) if match else "Unknown"


def extraire_contraste(file_path):
    match = re.search(r'_(T1w|T2w)\.nii\.gz$', file_path)
    return match.group(1) if match else None
    

def propseg(image_list, max_area, max_deformation, min_contrast):
    """Applique sct_propseg sur chaque image trouvée."""
    for image_path in image_list:
        print(f"Segmentation en cours : {image_path}")

        sujet = trouver_nom_sujet(image_path)
        nom_contraste = extraire_contraste(image_path)

        if nom_contraste == 'T1w':
            contrast = 't1'
        elif nom_contraste == 'T2w':
            contrast = 't2'

        # Exécute sct_propseg
        cmd = [
            "sct_propseg",
            "-i", image_path,
            "-c", contrast,  # Définition du contraste choisi
            "-o", f"test/anat/{sujet}_{nom_contraste}_propseg.nii.gz",
            "-max-area", str(max_area),
            "-max-deformation", str(max_deformation),
            "-min-contrast", str(min_contrast),
        ]
        
        try:
            print("Commande exécutée:", " ".join(cmd))
            subprocess.run(cmd, check=True)
            print(f"Segmentation terminée pour : {image_path}")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de la segmentation de {image_path}: {e}")
    

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    fichiers = liste_fichiers(args.f)
    propseg(fichiers, args.max_area, args.max_deformation, args.min_contrast)

    

