import pandas as pd
import argparse

def analyze_segmentation(file_path, output_path):
    # Charger le fichier CSV
    df = pd.read_csv(file_path)
    
    # Convertir en numérique en gérant les erreurs
    df["propseg"] = pd.to_numeric(df["propseg"], errors="coerce")
    df["GT"] = pd.to_numeric(df["GT"], errors="coerce")
    
    # 1. Identifier les sujets ayant une valeur pour propseg mais pas pour GT
    propseg_only = df[df["GT"].isna()]["Sujet"].tolist()
    
    # 2. Identifier les sujets ayant une valeur pour GT mais pas pour propseg
    gt_only = df[df["propseg"].isna()]["Sujet"].tolist()
    
    # 3. Identifier les sujets où GT < 5
    gt_negative = df[df["GT"] < 5].copy()
    
    # Créer un DataFrame récapitulatif
    recap_data = {
        "Nombre de sujets avec propseg mais pas GT": [len(propseg_only)],
        "Nombre de sujets avec GT mais pas propseg": [len(gt_only)],
        "Moyenne GT": [df["GT"].mean()],
        "Médiane GT": [df["GT"].median()],
        "Max GT": [df["GT"].max()],
        "Min GT": [df["GT"].min()],
        "Moyenne propseg": [df["propseg"].mean()],
        "Médiane propseg": [df["propseg"].median()],
        "Max propseg": [df["propseg"].max()],
        "Min propseg": [df["propseg"].min()],
    }
    
    recap_df = pd.DataFrame(recap_data)
    
    # Sauvegarde des résultats
    recap_df.to_csv(output_path + "/recapitulatif.csv", index=False)
    gt_negative.to_csv(output_path + "/gt_negatif.csv", index=False)
    
    print("Analyse terminée. Résultats sauvegardés dans le dossier spécifié.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse un fichier de GT_vs_label et génère des rapports.")
    parser.add_argument("-f", type=str, help="Chemin du fichier CSV à analyser")
    parser.add_argument("-o", type=str, help="Dossier où sauvegarder les résultats")
    
    args = parser.parse_args()
    
    analyze_segmentation(args.f, args.o)
