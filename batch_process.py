import subprocess

# Lire la liste des fichiers
with open("file_list.txt", "r") as f:
    lines = f.readlines()

# Boucle sur chaque ligne
for line in lines:
    seg_file, label_file = line.strip().split()
    print("\n" + "="*50)
    print(f"Traitement de : {seg_file} et {label_file}")

    # Exécuter le script principal
    cmd = ["python", "extend-seg-upper-cord/GT_vs_label.py", "-segmentation", seg_file, "-labels", label_file, "-margin", "10"]
    subprocess.run(cmd)