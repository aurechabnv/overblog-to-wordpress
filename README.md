# py-export-formatter-ob2wp

> Convertissez votre fichier d'export OverBlog en trois fichiers XML compatibles avec le plugin WP All Import pour WordPress

Occupée à la migration d'un blog OverBlog vers WordPress, j'ai suivi le [guide fait par Camélicot](https://cooklicot.fr/blog/migrer-depuis-overblog-vers-wordpress/) à ce sujet.

Cependant le [script PowerShell](https://github.com/jibap/Overblog2Wordpress) fourni me générait des erreurs, et n'étant pas spécialiste de ce langage, j'ai préféré le réécrire en Python.

Quelques mois après les faits, je révise le code et ajoute une interface avec PySide6 pour en faciliter l'usage.

## Comment l'utiliser ?
### Pré-requis

Clonez le projet dans votre IDE préférée, créez un environnement virtuel utilisant Python 3.12

Installez les pré-requis du projet avec pip :

`pip install -r requirements.txt`

### Lancement de l'interface

Exécutez le code :

`python main.py`

Sélectionnez votre fichier d'entrée, votre dossier de sortie, et la dernière ID connue de votre base WordPress.

Cliquez ensuite sur "Convertir" et voilà !