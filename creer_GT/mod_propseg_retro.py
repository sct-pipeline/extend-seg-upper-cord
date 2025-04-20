import argparse
import pandas as pd
import os
import glob
import re
import subprocess


def get_parser():
    parser = argparse.ArgumentParser(
        description="Lance la segmentation propseg avec des paramètres adaptatifs selon la qualité du propseg existant."
    )
    parser.add_argument("-f", type=str, required=True, help="Fichier CSV contenant le nom des sujets à analyser")
    parser.add_argument("--log", type=str, default=None, help="Fichier CSV pour enregistrer les paramètres utilisés")
    parser.add_argument("-o", type=str, default=".", help="Répertoire de sortie pour les segmentations")
    return parser


def generer_liste_images(csv_path, output_dir):
    df = pd.read_csv(csv_path)
    df_filtered = df[(df['propseg'] < 5) & (df['propseg'].notna())]

    image_param_list = []

    for _, row in df_filtered.iterrows():
        subject_name = row['Sujet']
        propseg_value = row['propseg']
        match = re.match(r"(sub-[a-zA-Z0-9]+)(T1w|T2w)", subject_name)
        if not match:
            print(f"Format inattendu pour: {subject_name}")
            continue

        sujet = match.group(1)      # ex: sub-barcelona02
        nom_contraste = match.group(2)  # ex: T1w
        print(sujet)
        
        if nom_contraste == 'T1w':
            contrast = 't1'
        elif nom_contraste == 'T2w':
            contrast = 't2'

        # Construire le chemin d’accès attendu
        file_pattern = os.path.join(
            "data-multi-subject/derivatives/data_preprocessed",
            sujet,
            "anat",
            f"*{nom_contraste}*.nii.gz"  # Le * avant et après pour matcher tout suffixe BIDS
        )

        matched_files = glob.glob(file_pattern)

        if not matched_files:
            print(f"Aucun fichier trouvé pour {sujet} ({contrast}) → pattern: {file_pattern}")
        
        # Définir des paramètres dynamiques (ajuster cette logique si nécessaire)
        if propseg_value < 2:
            max_area = 100
            max_deformation = 2.0
            min_contrast = 30
        else:
            max_area = 150
            max_deformation = 3.0
            min_contrast = 50

        for file_path in matched_files:
            output_path = os.path.join(output_dir, f"{sujet}_{nom_contraste}_propseg.nii.gz")
            image_param_list.append({
                'path': file_path,
                'subject': sujet,
                'contrast': contrast,  # 't1' ou 't2'
                'propseg_value': propseg_value,
                'max_area': max_area,
                'max_deformation': max_deformation,
                'min_contrast': min_contrast,
                'output_path': output_path
            })
    print(f"✅ Total images sélectionnées pour segmentation: {len(image_param_list)}")
    return image_param_list


def run_propseg(image_param_list, log_file=None):
    if log_file:
        log_entries = []

    for img in image_param_list:
        image_path = img['path']
        contrast = img['contrast']
        max_area = img['max_area']
        max_deformation = img['max_deformation']
        min_contrast = img['min_contrast']
        sujet = img['subject']
        output_path = img['output_path']

        print(f"\n Segmenting: {image_path}")
        print(f"   Params: max_area={max_area}, max_deformation={max_deformation}, min_contrast={min_contrast}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            "sct_propseg",
            "-i", image_path,
            "-c", contrast,
            "-o", output_path,
            "-max-area", str(max_area),
            "-max-deformation", str(max_deformation),
            "-min-contrast", str(min_contrast),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"Done: {output_path}")
            if log_file:
                log_entries.append({
                    'subject': sujet,
                    'image': os.path.basename(image_path),
                    'contrast': contrast,
                    'propseg_value': img['propseg_value'],
                    'max_area': max_area,
                    'max_deformation': max_deformation,
                    'min_contrast': min_contrast,
                    'output_path': output_path
                })
        except subprocess.CalledProcessError as e:
            print(f"Error with {image_path}: {e}")

    if log_file:
        keys = log_entries[0].keys()
        with open(log_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(log_entries)
        print(f"\nParamètres enregistrés dans: {log_file}")


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()

    images = generer_liste_images(args.f, args.o)
    if not images:
        print(" Aucun fichier image trouvé pour segmentation. Vérifie le CSV et les chemins.")

    run_propseg(images, log_file=args.log)