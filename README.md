# projet_perso_l3

Convertisseur de fichiers basé sur Flask. Le projet supporte les conversions de données, d'images, d'audio et de documents, avec une API locale, un historique persistant, un système de profils, un tableau de suivi et des pages UI dédiées.

## Vue d'ensemble

Fonctionnalités principales:
- Conversion de données JSON ⇄ YAML et reformatage JSON.
- Conversion d'images PNG → JPG, JPG ↔ WebP, PNG → WebP, SVG → PNG, images → PDF.
- Conversion audio MP4 → MP3 et MP3 → WAV.
- Conversion de documents PDF ⇄ DOCX, PDF ⇄ TXT, DOCX ⇄ TXT.
- API REST locale pour convertir, suivre les jobs, télécharger les résultats, consulter l'historique et gérer les profils.
- Profils de conversion stockés localement en JSON.
- Tableau de suivi avec statistiques.
- Prévisualisation de fichiers pour les images et le texte.
- Presets rapides sur les pages de conversion.
- Historique consultable via l'interface web.

## Prérequis

- Python 3.10+.
- CairoSVG pour la conversion SVG → PNG.
- LibreOffice pour les conversions de documents.
- FFmpeg pour les conversions audio.

## Installation

Créer et activer un environnement virtuel, puis installer les dépendances:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Lancement de l'application

Avec Python:

```bash
source .venv/bin/activate
python3 app.py
```

Avec Flask CLI:

```bash
source .venv/bin/activate
export FLASK_APP=app.py
flask run
```

Par défaut, le serveur écoute sur `127.0.0.1:5000`.

Variables d'environnement utiles:
- `PORT`: port du serveur, défaut `5000`.
- `BIND`: adresse d'écoute, défaut `127.0.0.1`.
- `LOCAL_API_KEY`: clé API optionnelle pour protéger `/api/*`.
- `MAX_GLOBAL_UPLOAD_MB`: taille totale maximale d'un lot, défaut `20` MB.
- `FLASK_SECRET_KEY`: clé secrète Flask, défaut de développement si non définie.

## Utilisation rapide

1. Ouvrir la page d'accueil `/`.
2. Choisir le type de conversion.
3. Sélectionner un ou plusieurs fichiers.
4. Choisir le format cible.
5. Lancer la conversion.

Pour le suivi des traitements, utiliser la page `/monitoring`. Pour l'historique, utiliser `/history`.

## API locale

Endpoints principaux:
- `POST /api/convert`
- `GET /api/jobs`
- `GET /api/jobs/<job_id>`
- `GET /api/jobs/<job_id>/download`
- `GET /api/jobs/<job_id>/preview`
- `GET /api/history?limit=20`
- `GET /api/profiles`
- `POST /api/profiles`
- `DELETE /api/profiles/<type>/<profile_id>`

Exemple de conversion JSON → YAML:

```bash
curl -X POST "http://127.0.0.1:5000/api/convert" \
  -F "conversion_type=data" \
  -F "target_format=yaml" \
  -F "file=@./exemple.json"
```

Avec clé API:

```bash
curl -X POST "http://127.0.0.1:5000/api/convert" \
  -H "X-API-Key: VOTRE_CLE" \
  -F "conversion_type=data" \
  -F "target_format=yaml" \
  -F "file=@./exemple.json"
```

## Structure du projet

```text
.
├── app.py
├── config.py
├── converters
│   ├── audio.py
│   ├── base.py
│   ├── data.py
│   ├── document.py
│   ├── image.py
│   └── __init__.py
├── data
│   ├── history.json
│   └── profiles.json
├── documentation
│   └── api_technique.md
├── models.py
├── README.md
├── requirements.txt
├── routes
│   ├── api.py
│   ├── conversion.py
│   ├── __init__.py
│   └── pages.py
├── services
│   ├── conversion_service.py
│   ├── history_service.py
│   ├── __init__.py
│   ├── job_service.py
│   ├── profile_service.py
│   └── services_container.py
├── static
│   ├── main.js
│   └── style.css
├── templates
│   ├── audio.html
│   ├── base.html
│   ├── data.html
│   ├── documents.html
│   ├── history.html
│   ├── images.html
│   ├── index.html
│   ├── _jobs_table.html
│   └── monitoring.html
├── tests
│   ├── conftest.py
│   ├── test_app_sprint5.py
│   ├── test_app_sprint6.py
│   ├── test_app_sprint7.py
│   ├── test_converter_audio.py
│   ├── test_converter_documents.py
│   ├── test_converter_images.py
│   └── test_converter.py
├── uploads
│   └── api_exports
└── utils.py

11 directories, 44 files
```

## Bonnes pratiques et notes techniques

- Les données persistantes (`history.json`, `profiles.json`) sont stockées dans `data/`.
- Les fichiers temporaires et exports API vivent dans `uploads/`.
- Le dossier `uploads/api_exports/` peut être vidé sans impact sur les données persistantes.
- Les conversions audio et documents dépendent de binaires système externes, donc certains tests peuvent être ignorés si FFmpeg ou LibreOffice ne sont pas installés.

## Historique des sprints

- Sprint 1: base Flask et conversions JSON ⇄ YAML.
- Sprint 2: conversions d'images.
- Sprint 3: support SVG → PNG.
- Sprint 4: conversions audio.
- Sprint 5: documents, lots, ZIP et refonte UI.
- Sprint 6: API locale, historique, téléchargement différé.
- Sprint 7: profils, monitoring, preview, presets, historique UI.