import os
import glob
import re
import argparse
import subprocess

def get_parser():
    parser = argparse.ArgumentParser(description="Script pour automatiser sct_propseg sur plusieurs images.")
    parser.add_argument('-d', '--directory', type=str, required=True, help='Répertoire racine contenant les images')
    parser.add_argument('-r', '--regex', type=str, required=True, help="Pattern regex pour filtrer les images")
    parser.add_argument('-c', '--contrast', type=str, required=True, help="Type de contraste pour sct_propseg")
    return parser

def find_images(directory, regex_pattern):
    all_files = glob.glob(os.path.join(directory, "*", "anat", "*.nii.gz"), recursive=True)
    matched_files = [f for f in all_files if re.search(regex_pattern, f)]
    return matched_files

def trouver_nom_sujet(file_path):
    match = re.search(r"(sub-[a-zA-Z0-9]+)", file_path)
    return match.group(1) if match else "Unknown"

def segment_images(image_list, contrast):
    """Applique sct_propseg sur chaque image trouvée."""
    for image_path in image_list:
        print(f"Segmentation en cours : {image_path}")

        sujet = trouver_nom_sujet(image_path)

        # Exécute sct_propseg
        cmd = [
            "sct_propseg",
            "-i", image_path,
            "-c", contrast,  # Définition du contraste choisi
            "-o", f"extend-seg-upper-cord/anat/{sujet}_{contrast}_propseg.nii.gz"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Segmentation terminée pour : {image_path}")
        except subprocess.CalledProcessError as e:
            print(f"Erreur lors de la segmentation de {image_path}: {e}")

def main():
    """Récupère les arguments et exécute le pipeline de segmentation."""
    parser = get_parser()
    args = parser.parse_args()

    # Trouver les images
    images_to_process = find_images(args.directory, args.regex)

    # Lancer la segmentation
    if images_to_process:
        print(f"{len(images_to_process)} images trouvées. Lancement de la segmentation...")
        segment_images(images_to_process, args.contrast)
    else:
        print("Aucune image correspondant au pattern n'a été trouvée.")

if __name__ == "__main__":
    main()