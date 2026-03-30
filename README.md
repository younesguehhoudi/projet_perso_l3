# projet_perso_l3

Convertisseur de fichiers basé sur Flask, usage local uniquement (pas de déploiement internet prévu).

Statut actuel (Sprint 6): 
- Conversion de données JSON ⇄ YAML et reformatage JSON opérationnels.
- Conversions d'images PNG→JPG, JPG↔WebP, PNG→WebP, SVG→PNG opérationnelles.
- Conversions audio MP4→MP3 et MP3→WAV opérationnelles.
- Conversions documents PDF ⇄ DOCX, PDF ⇄ TXT, DOCX ⇄ TXT opérationnelles (LibreOffice headless).
- API locale REST disponible (convert, status, download, history).

Des conversions de documents sont prévues pour les prochains sprints.

## Prérequis
- Python 3.10+
- CairoSVG (pour les conversions SVG → PNG)
- LibreOffice (pour les conversions documents PDF/DOCX/TXT)

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

### Variables d'environnement API (Sprint 6)
- `LOCAL_API_KEY` (optionnelle): si définie, les endpoints `/api/*` exigent le header `X-API-Key`.
- `MAX_GLOBAL_UPLOAD_MB` (optionnelle): taille totale max d'un lot de fichiers (défaut: `20` MB).

## Utilisation
- Ouvrez la page d'accueil `/` (index).
- Sélectionnez le type de conversion (Données ou Image).
- Uploadez un fichier.
- Choisissez le format de sortie.
- Cliquez « Convertir et télécharger ».

Notes:
- La taille maximale d'un fichier autorisée est de 10 Mo.

## Fonctionnalités
- **Données**: JSON ⇄ YAML, reformatage JSON (bibliothèques `json` et `PyYAML`).
- **Images**: PNG → JPG, JPG → WebP, WebP → JPG, PNG → WebP (bibliothèque `Pillow`).
  - Gestion automatique de la transparence (conversion RGBA → RGB avec fond blanc pour JPG).
  - Optimisation et compression de qualité 85% par défaut.
- **SVG**: SVG → PNG (bibliothèque `CairoSVG`).
- **Audio**: MP4 → MP3, MP3 → WAV (via `ffmpeg`).
- **Documents**: PDF ⇄ DOCX, PDF ⇄ TXT, DOCX ⇄ TXT (via LibreOffice headless).
- **API locale**:
  - `POST /api/convert` (upload + conversion)
  - `GET /api/jobs/<job_id>` (statut)
  - `GET /api/jobs/<job_id>/download` (téléchargement différé)
  - `GET /api/jobs` (liste de jobs)
  - `GET /api/history?limit=20` (historique local JSON)

Remarques techniques:
- Les conversions d’images, d’audio et de documents peuvent nécessiter des dépendances système (ex: `ffmpeg`, `libreoffice`, `inkscape`).

## API locale (Sprint 6) — Exemples

Les endpoints API sont locaux et exposés par la même application Flask.

### 1) Convertir un fichier (JSON → YAML)
Sans clé API:

```bash
curl -X POST "http://127.0.0.1:5000/api/convert" \
  -F "conversion_type=data" \
  -F "target_format=yaml" \
  -F "file=@./exemple.json"
```

Avec clé API (`LOCAL_API_KEY` définie):

```bash
curl -X POST "http://127.0.0.1:5000/api/convert" \
  -H "X-API-Key: VOTRE_CLE" \
  -F "conversion_type=data" \
  -F "target_format=yaml" \
  -F "file=@./exemple.json"
```

Réponse type:
- `job_id`
- `status`
- `success_count` / `error_count`
- `status_url`
- `download_url`

### 2) Vérifier le statut d'un job

```bash
curl "http://127.0.0.1:5000/api/jobs/<job_id>"
```

### 3) Télécharger la sortie d'un job

```bash
curl -L "http://127.0.0.1:5000/api/jobs/<job_id>/download" -o resultat.bin
```

### 4) Consulter l'historique des conversions

```bash
curl "http://127.0.0.1:5000/api/history?limit=20"
```

Historique stocké localement dans `history.json` avec:
- date
- formats source/cible
- taille totale (octets)
- statut
- compteurs de succès/erreurs

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
- Sprint 3 – **fait**: SVG → PNG (CairoSVG)
- Sprint 4 – **fait**: audio MP4 → MP3, MP3 → WAV (FFmpeg)
- Sprint 5 – **documents et batch**:
  - Conversions documents PDF ⇄ DOCX, PDF ⇄ TXT, DOCX ⇄ TXT (LibreOffice headless)
  - Gestion de lots (multi-upload) et ZIP de sortie
  - File d’attente simple en memoire (en attente / en cours / termine / erreur)
  - Tests unitaires conversions documents
  - Validation basique des formats en entree (extension + MIME)
  - Parametres de conversion limits a 1 ou 2 options (ex: encodage TXT)
  - Nettoyage automatique des fichiers temporaires par job termine
  - refonte complete de l'interface (ajout du js/css)
  - ajout de la navigation entre les differentes sections (données, images, documents)
- Sprint 6 – **fait**:
  - API REST locale (upload, convert, status, download)
  - Cle API en header (optionnelle, valeur dans env)
  - Historique des conversions en JSON local (date, formats, taille, statut)
  - Endpoint de liste (dernieres conversions)
  - Telechargement differe via ID de job
  - Limites basiques (taille max globale, formats autorises)
  - Documentation API locale minimale (exemples curl)
- Sprint 7 – **UI avancee et profils**:
  - Profils de conversion (JSON local, un profil par type)
  - Tableau de suivi (liste + statut, sans temps reel)
  - Previsualisation des fichiers (images, extraits de texte)
  - Ameliorations UX (erreurs claires, resumes, aide contextuelle)
  - Presets rapides (boutons pour conversions frequentes)
  - Historique consultable depuis l’UI 