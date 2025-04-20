import json
import yaml

# Charger le fichier qc.json
with open("qc_flags.json", "r") as f:
    qc_data = json.load(f)

# Initialiser structure YAML
subjects_yml = {"data": []} 

# Parcourir les entrées QC
for key, value in qc_data.items():
    if "sct_deepseg_sc_qc" in key and value.strip() == "✅":
        # Extraire le nom du sujet_contraste à partir de la clé
        # Format attendu : 2025-04-01 07:02:09_sub-barcelona02_T1w.nii.gz_sct_deepseg_sc_qc
        parts = key.split("_")
        try:
            full_filename = parts[1]  # ex: sub-barcelona02_T1w.nii.gz
            subject_contrast = full_filename.replace(".nii.gz", "")  # ex: sub-barcelona02_T1w
            subjects_yml["data"].append(subject_contrast)
        except IndexError:
            print(f"Problème de format avec la ligne : {key}")

# Sauvegarder en YAML
with open("subjects_to_include.yml", "w") as f:
    yaml.dump(subjects_yml, f, default_flow_style=False)

print("Fichier 'subjects_to_include.yml' généré avec succès.")
