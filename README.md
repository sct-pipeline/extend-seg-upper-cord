# Extend segmentation to the upper cord

## Scripts

1. GT_vs_label.py

    Ce script vise à créer un document CSV qui présente l'écart entre le label de C1 et le haut de la segmentation donnée (négatif si la segmentation arrive en dessous du label).
    Le script prend en entrée l'expression régulière pour les fichiers de segmentation (.nii.gz),
   l'expression régulière pour les fichiers de labels (.nii.gz), le dossier initial contenant les fichiers de segmentation à analyser,
    le dossier initial contenant les fichiers de labels à analyser et le nom de la méthode de segmentation utilisée (GT ou propseg).

   Le fichier CSV créé contient une colonne contenant le nom du sujet (par exemple: sub-amu01T1w). Les autres colonnes sont nommées selon le nom de la méthode (GT ou propseg).
   Si le fichier existe déjà, le script vérifie si la colonne existe déjà. Si c'est le cas, rien n'est modifié, un message s'affiche précisant que la colonne existe déjà.
   Si la colonne n'existe pas, elle est créée et a comme nom le nom de la méthode. Le contenu de la colonne correspond au nombre de slices d'écart entre le premier label de disque
   et la fin de la segmentation. Une valeur négative indique que la segmentation arrête avant le label.

    Un exemple de sortie est le suivant:

   <img width="301" alt="image" src="https://github.com/user-attachments/assets/66f83880-4c74-4772-9d7a-a2318f7244df" />

   Dans le cas où il y a des cases vides dans une des deux colonnes, cela signifie que le fichier de segmentation n'existait pas pour cette méthode.

   <img width="302" alt="image" src="https://github.com/user-attachments/assets/bd6cae03-6754-490e-b8ba-fde65bb2e369" />

   Exemple d'utilisation:

   ```bash
   python extend-seg-upper-cord/GT_vs_label.py -segmentation_regex t -labels_regex w_label-discs_dlabel -d_seg . -d_label data-multi-subject/derivatives/labels/ -seg_method propseg
   ```



   
