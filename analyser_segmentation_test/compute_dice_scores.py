import os
import subprocess
import pandas as pd

# === CONFIGURATION ===
GT_DIR = "/home/ge.polymtl.ca/mestaa/propseg_fusion_cropped_2004"
PRED_DIR = "/home/ge.polymtl.ca/mestaa/output_extend-seg-upper-cord_2004"
OUTPUT_CSV = "/home/ge.polymtl.ca/mestaa/results/dice_scores_2004.csv"

SUBJECTS = [
    "sub-barcelona02",
    "sub-geneva01"
]

CONTRASTS = ["T1w", "T2w"]

def compute_dice_sct(pred_path, gt_path):
    try:
        result = subprocess.run(
            ["sct_dice_coefficient", "-i", pred_path, "-d", gt_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True
        )
        for line in result.stdout.splitlines():
            if "Dice coefficient" in line:
                return float(line.split("=")[-1].strip())
    except subprocess.CalledProcessError as e:
        print(f"Erreur avec sct_maths : {e.stderr}")
        return None

results = []

for subj in SUBJECTS:
    for contrast in CONTRASTS:
        gt_file = os.path.join(GT_DIR, f"{subj}_{contrast}_fusion_cropped.nii.gz")
        pred_file = os.path.join(PRED_DIR, f"{subj}_{contrast}_seg_nnunet.nii.gz")

        if not os.path.isfile(gt_file):
            print(f"GT introuvable : {gt_file}, recherche dans data-multi-subject")
            gt_file = os.path.join(f"data-multi-subject/derivatives/labels_softseg_bin/{subj}/anat", f"{subj}_{contrast}_desc-softseg_label-SC_seg.nii.gz")
        if not os.path.isfile(pred_file):
            print(f"Prédiction introuvable : {pred_file}")
            continue

        dice = compute_dice_sct(pred_file, gt_file)
        if dice is not None:
            print(f"Dice {subj} ({contrast}) : {dice:.4f}")
            results.append({
                "subject": subj,
                "contrast": contrast,
                "dice_score": round(dice, 4)
            })

# === Sauvegarde CSV ===
df = pd.DataFrame(results)
df.to_csv(OUTPUT_CSV, index=False)
print(f"Résultats sauvegardés dans : {OUTPUT_CSV}")

# === Moyenne, écart-type, coefficient de variation ===
mean_dice = df["dice_score"].mean()
std_dice = df["dice_score"].std()
cv_dice = std_dice / mean_dice if mean_dice > 0 else 0

# Affichage console
print("\n=== Statistiques globales ===")
print(f"Moyenne Dice      : {mean_dice:.4f}")
print(f"Écart-type Dice   : {std_dice:.4f}")
print(f"Coefficient de variation : {cv_dice:.4f}")

# === Export dans un second fichier CSV ===
stats_output = {
    "mean_dice": [round(mean_dice, 4)],
    "std_dice": [round(std_dice, 4)],
    "cv_dice": [round(cv_dice, 4)]
}

df_stats = pd.DataFrame(stats_output)
df_stats.to_csv("/home/ge.polymtl.ca/mestaa/results/dice_stats_2004.csv", index=False)

print("Statistiques sauvegardées dans : /home/ge.polymtl.ca/mestaa/results/dice_stats_2004.csv")
