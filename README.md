# projet_perso_l3

Convertisseur de fichiers basé sur Flask, usage local uniquement (pas de déploiement internet prévu).

Statut actuel (Sprint 1): conversion de données JSON ⇄ YAML et reformatage JSON opérationnels.
Des conversions d’images, d’audio et de documents sont prévues pour les prochains sprints.

## Prérequis
- Python 3.10+

## Installation

Créez et activez un environnement virtuel, puis installez les dépendances:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

assurez-vous d'être dans l'environnement virtuel (commande `source .venv/bin/activate`) et d'utiliser `python3`.

## Lancement du serveur

Méthode 1 (python direct):
```bash
python3 app.py
```

Méthode 2 (flask CLI):
```bash
export FLASK_APP=app.py
flask run
```

Le serveur démarre sur http://localhost:5000
\- Par défaut, le serveur n’est accessible que depuis la machine locale: http://127.0.0.1:5000
\- Variables d’environnement utiles: `PORT` (défaut 5000), `BIND` (défaut `127.0.0.1`).

## Utilisation
- Ouvrez la page d'accueil `/` (index).
- Uploadez un fichier.
- Choisissez le format de sortie.
- Cliquez « Convertir et télécharger ».

Notes:
- (Sprint 1), l'interface prend en charge la conversion de données JSON ⇄ YAML et le reformatage JSON.
- La taille maximale autorisée est de 10 Mo.
- Les fichiers temporaires sont supprimés automatiquement après le téléchargement.

## Fonctionnalités

Disponibles (Sprint 1)
- JSON ⇄ YAML, reformatage JSON (bibliothèques `json` et `PyYAML`).

En préparation (prochains sprints)
- Documents: PDF ↔ DOCX (via LibreOffice en mode headless).
- Images: PNG → JPG, JPG ↔ WebP, SVG → PNG (via Pillow/CairoSVG).
- Audio: MP4 → MP3, MP3 → WAV (via FFmpeg/pydub).

Remarques techniques:
- Les conversions d’images, d’audio et de documents peuvent nécessiter des dépendances système (ex: `ffmpeg`, `libreoffice`, `inkscape`). Des wrappers et des checks d’environnement seront ajoutés.

## Tests

Installez les dépendances (incluant pytest), puis lancez les tests:
```bash
pytest -q
```

## Structure du projet
```
app.py
converter.py
requirements.txt
/templates/
/static/
/uploads/
/tests/
```

## MILESTONE (5 sprints)
- Sprint 1 – fait: Base Flask, JSON ⇄ YAML, README
- Sprint 2 – images: PNG → JPG, JPG ↔ WebP, PNG → WebP (Pillow)
- Sprint 3 – SVG: SVG → PNG (CairoSVG/Inkscape)
- Sprint 4 – audio: MP4 → MP3, MP3 → WAV (FFmpeg/pydub)
- Sprint 5 – documents: PDF ↔ DOCX (LibreOffice headless), sandbox tmp, tests simples
