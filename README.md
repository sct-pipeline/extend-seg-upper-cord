# Contrast-agnostic: Extend segmentation to the upper cord 

## Table des matières
* [Schéma explicatif](#schéma-explicatif)
* [Utilisation du pipeline](#utilisation-du-pipeline)
* [Entraîner le modèle](#entrainer-le-modèle)

## Schéma explicatif

Le schéma suivant résume les différentes étapes pour l'obtention des vérités-terrain pour entraîner le modèle de segmentation de la moelle épinière contrast-agnostic qui permet une couverture adéquate de la région de la vertèbre C1.

![Schema_explicatif](https://github.com/user-attachments/assets/7fc8818a-5f77-4f14-bdca-2345cf851f21)

## Utilisation du pipeline

### 1. Prérequis

1. Spinal Cord Toolbox (version 6.4 ou plus)
2. Python (version 3.9 ou plus)

### 2. Banque de données

La banque de données utilisée dans le cadre de ce projet est Spine Generic Public Database (Multi Subject) https://github.com/spine-generic/data-multi-subject/ 

### 3. Lancer les scripts

1. Calculer où se rendent les segmentations vérité terrain de contrast-agnostic par rapport au label de C1: seg_vs_label.py
```bash
python creer_GT/seg_vs_label.py \
        -segmentation_regex regex_des_segmentations \
        -labels_regex regex_des_labels \
        -d_seg chemin/vers/les/segmentations \
        -d_label chemin/vers/les/labels \
        -seg_method NomMethode
```
2. Vérifier quelles segmentations GT ont besoin d'être modifiées afin d'aller plus haut: analyse_seg_vs_label.py
```bash
python creer_GT/analyse_gt_propseg.py \
        -f chemin/CSV/sortie/de/seg_vs_label \
        -o chemin/de/sortie/désiré
```
3. Créer une segmentation propseg avec des paramètres différents selon jusqu'où se rend la segmentation avec les paramètres par défaut: modification_propseg.py
```bash
python creer_GT/modification_propseg.py \
        -f chemin/CSV/sortie/de/analyse_seg_vs_label \
        -o chemin/de/sortie/désiré \
```
4. Calculer un facteur d'échelle entre la segmentation vérité terrain de contrast-agnostic et la segmentation propseg: calcul_facteurs_echelle.sh
```bash
bash creer_GT/calcul_facteur_echelle.sh
```
5. Appliquer ce facteur d'échelle à la segmentation propseg: aplliquer_facteur_echelle.py
```bash
python creer_GT/appliquer_facteur_echelle.py
```
6. Fusionner les segmentations propseg et vérité terrain de contrast-agnostic: fusion_seg.sh
```bash
bash creer_GT/fusion_seg.sh
```
7. Couper la segmentation si elle se rend trop haut: crop_above_C1.sh
```bash
bash creer_GT/crop_above_C1.sh
```
8. Faire des rapports de contrôle de qualité: qc_fusion_all.sh
```bash
bash creer_GT/qc_fusion_all.sh
```

## Entraîner le modèle

### 1. Créer YAML

1. Créer un fichier YAML avec les sujets ayant passé le contrôle de qualité
2. Créer un datasplit avec ces sujets: train, val, test

### 2. Scripts pour l'entraînement

Le protocole suivi pour l'entraînement est celui provenant de ce dépôt: https://github.com/sct-pipeline/contrast-agnostic-softseg-spinalcord

### 3. Analyse de la qualité de la segmentation

1. Calcul des Dice scores: compute_dice_scores.py
```bash
python analyser_segmentation_test/compute_dice_scores.py
```
2. Calcul du pourcentage de couverture de C1: couverture_C1.py
```bash
python analyser_segmentation_test/couverture_C1.py
```
