# projet_perso_l3

Convertisseur de fichiers basé sur Flask, usage local uniquement (pas de déploiement internet prévu).

Statut actuel (Sprint 2 terminé): 
- Conversion de données JSON ⇄ YAML et reformatage JSON opérationnels.
- Conversions d'images PNG→JPG, JPG↔WebP, PNG→WebP opérationnelles.

Des conversions SVG, audio et documents sont prévues pour les prochains sprints.

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
- Sélectionnez le type de conversion (Données ou Image).
- Uploadez un fichier.
- Choisissez le format de sortie.
- Cliquez « Convertir et télécharger ».

Notes:
- (Sprint 1 & 2) Support de JSON/YAML et PNG/JPG/WebP.
- La taille maximale autorisée est de 10 Mo.
- Les fichiers temporaires sont supprimés automatiquement après le téléchargement.

## Fonctionnalités

Disponibles (Sprint 1 & 2)
- **Données**: JSON ⇄ YAML, reformatage JSON (bibliothèques `json` et `PyYAML`).
- **Images**: PNG → JPG, JPG → WebP, WebP → JPG, PNG → WebP (bibliothèque `Pillow`).
  - Gestion automatique de la transparence (conversion RGBA → RGB avec fond blanc pour JPG).
  - Optimisation et compression de qualité 85% par défaut.

En préparation (prochains sprints)
- SVG: SVG → PNG (via CairoSVG/Inkscape).
- Documents: PDF ↔ DOCX (via LibreOffice en mode headless).
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

## MILESTONE (7 sprints)
- Sprint 1 – **fait**: Base Flask, JSON ⇄ YAML, README
- Sprint 2 – **fait**: images PNG → JPG, JPG ↔ WebP, PNG → WebP (Pillow)
- Sprint 3 – SVG: SVG → PNG (CairoSVG/Inkscape)
- Sprint 4 – audio: MP4 → MP3, MP3 → WAV (FFmpeg/pydub)
- Sprint 5 – documents: PDF ↔ DOCX (LibreOffice headless), sandbox tmp, tests simples
- Sprint 6 – (...)
- Sprint 7 – (...)
