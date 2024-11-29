# py-export-formatter-ob2wp

> Convertissez votre fichier d'export OverBlog en trois fichiers XML compatibles avec le plugin WP All Import pour WordPress

Occupée à la migration d'un blog OverBlog vers WordPress, j'ai suivi le [guide fait par Camélicot](https://cooklicot.fr/blog/migrer-depuis-overblog-vers-wordpress/) à ce sujet.

Cependant le [script PowerShell](https://github.com/jibap/Overblog2Wordpress) fourni me générait des erreurs, et n'étant pas spécialiste de ce langage, j'ai préféré le réécrire en Python.

Quelques mois après les faits, je révise le code et ajoute une interface avec PySide6 pour en faciliter l'usage.

## Quand l'utiliser ?

Ce script remplace le PowerShell exécuté à la **quatrième étape** du guide de Camélicot.

Après avoir déterminé le dernier ID de contenu créé dans votre base `wp_posts`, exécutez cet utilitaire pour transformer votre fichier d'export OverBlog, puis poursuivez le guide.

## Comment l'utiliser ?
### Pré-requis

Clonez le projet dans votre IDE préférée, créez un environnement virtuel utilisant la dernière version de Python (le code a été développé en utilisant la 3.12).

Installez les pré-requis du projet avec pip :

`pip install -r requirements.txt`

### Lancement de l'interface

Exécutez le code :

`python main.py`

Sélectionnez votre fichier d'entrée, votre dossier de sortie, et l'ID récupéré à l'étape précédente du guide.

Cliquez ensuite sur "Convertir", patientez, puis récupérez vos fichiers dans le dossier choisi pour passer à l'import dans WordPress.
![Aperçu de l'interface graphique](https://github.com/user-attachments/assets/045361e6-9740-4b32-b7e6-c8f379ef2e6f)
