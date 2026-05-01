# Documentation technique de l'API locale

## 1. Vue d'ensemble

L'API est exposée par l'application Flask sous le préfixe `/api`. Elle sert à automatiser les conversions, suivre l'état des jobs, télécharger les résultats, consulter l'historique et gérer les profils de conversion.

Caractéristiques principales:
- API locale, prévue pour un usage sur la machine de développement.
- Réponses au format JSON, sauf pour le téléchargement des fichiers convertis.
- Authentification optionnelle via clé API.
- Stockage persistant local pour l'historique et les profils.
- Jobs gardés en mémoire par l'application pour le suivi et le téléchargement différé.

## 2. Base URL

En local, l'API est disponible à l'adresse:

```text
http://127.0.0.1:5000/api
```

Le port peut être modifié avec la variable d'environnement `PORT`.

## 3. Authentification

L'API utilise une clé optionnelle:

- Variable d'environnement: `LOCAL_API_KEY`
- Header HTTP attendu: `X-API-Key`

Comportement:
- Si `LOCAL_API_KEY` est vide ou non définie, l'API accepte toutes les requêtes.
- Si `LOCAL_API_KEY` est définie, les routes sensibles exigent `X-API-Key`.

Exemple:

```bash
curl -H "X-API-Key: VOTRE_CLE" "http://127.0.0.1:5000/api/jobs"
```

## 4. Limites et configuration

Variables d'environnement utiles:
- `LOCAL_API_KEY`: protège les endpoints `/api/*`.
- `MAX_GLOBAL_UPLOAD_MB`: limite la taille totale d'un lot envoyé à `/api/convert`.
- `FLASK_SECRET_KEY`: clé secrète Flask.

Limites codées dans `config.py`:
- Taille maximale d'un fichier Flask: `10 MB`.
- Taille maximale d'un lot: `MAX_GLOBAL_UPLOAD_MB` (par défaut `20 MB`).
- Historique retourné par l'API: jusqu'à `100` entrées.
- Jobs conservés en mémoire: jusqu'à `200` jobs récents.

## 5. Modèle de données

### 5.1 Job

Un job représente une conversion soumise par l'API.

Champs principaux:
- `id`: identifiant unique du job.
- `type`: type de conversion (`data`, `image`, `audio`, `document`).
- `target_format`: format cible.
- `files_count`: nombre de fichiers envoyés.
- `status`: `en_attente`, `en_cours`, `termine`, `erreur`.
- `success_count`: nombre de conversions réussies.
- `error_count`: nombre d'erreurs.
- `message`: message de synthèse.
- `created_at`, `updated_at`: timestamps ISO 8601.
- `api_output_path`, `api_output_name`, `api_output_mimetype`: informations de sortie pour téléchargement.

### 5.2 Historique

L'historique est stocké dans `data/history.json`.

Une entrée contient notamment:
- `id`
- `job_id`
- `date`
- `type`
- `source_formats`
- `target_format`
- `size_bytes`
- `files_count`
- `success_count`
- `error_count`
- `status`

### 5.3 Profils

Les profils sont stockés dans `data/profiles.json`.

Structure:
- clé par type de conversion: `data`, `image`, `audio`, `document`
- chaque profil contient:
  - `id`
  - `name`
  - `source`
  - `target`

## 6. Endpoints

### 6.1 POST /api/convert

Soumet une conversion.

Headers:
- `X-API-Key` si l'authentification est activée.

Form-data:
- `conversion_type` : obligatoire, ex. `data`, `image`, `audio`, `document`
- `target_format` : obligatoire, dépend du type
- `txt_encoding` : optionnel, défaut `utf-8`
- `file` : un ou plusieurs fichiers

Exemple:

```bash
curl -X POST "http://127.0.0.1:5000/api/convert" \
  -F "conversion_type=data" \
  -F "target_format=yaml" \
  -F "file=@./exemple.json"
```

Réponse de succès:

```json
{
  "job_id": "a1b2c3d4...",
  "status": "termine",
  "success_count": 1,
  "error_count": 0,
  "errors": [],
  "status_url": "/api/jobs/a1b2c3d4...",
  "download_url": "/api/jobs/a1b2c3d4.../download"
}
```

Cas de réponse:
- `201 Created`: conversion acceptée et job enregistré.
- `400 Bad Request`: fichier absent, format invalide, conversion impossible.
- `413 Payload Too Large`: lot trop volumineux.
- `500 Internal Server Error`: erreur inattendue.

Règles de traitement:
- Un seul fichier réussi sans erreur retourne un fichier directement côté backend puis stocke la sortie dans le job.
- Plusieurs fichiers ou des erreurs produisent un ZIP.
- Les fichiers intermédiaires sont nettoyés après création du ZIP.

### 6.2 GET /api/jobs

Retourne la liste des jobs récents.

Paramètres:
- aucun

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Réponse:

```json
[
  {
    "id": "...",
    "type": "data",
    "target_format": "yaml",
    "status": "termine",
    "files_count": 1,
    "success_count": 1,
    "error_count": 0,
    "message": "Conversion terminée",
    "created_at": "2026-05-01T15:12:47.056674+00:00",
    "updated_at": "2026-05-01T15:12:47.056674+00:00"
  }
]
```

### 6.3 GET /api/jobs/<job_id>

Retourne le statut détaillé d'un job.

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Réponse:
- `200 OK` si le job existe.
- `404 Not Found` si le job est introuvable.

### 6.4 GET /api/jobs/<job_id>/download

Télécharge la sortie associée au job.

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Comportement:
- renvoie directement le fichier converti ou l'archive ZIP.
- l'en-tête `Content-Disposition` force le téléchargement.

Réponses possibles:
- `200 OK` avec fichier binaire.
- `404 Not Found` si le job n'existe pas ou si aucun fichier n'est disponible.

### 6.5 GET /api/jobs/<job_id>/preview

Retourne un aperçu du fichier de sortie.

Sécurité:
- pas de contrôle de clé API dans l'implémentation actuelle.

Comportement:
- si le fichier de sortie existe, l'API génère un aperçu via `utils.generate_preview()`.
- utile pour l'affichage dans l'interface web.

Réponses possibles:
- `200 OK` avec JSON d'aperçu.
- `404 Not Found` si le job ou le fichier de sortie est absent.

### 6.6 GET /api/history?limit=20

Retourne les dernières entrées d'historique.

Paramètres query:
- `limit` : entier, défaut `20`

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Réponses possibles:
- `200 OK` avec liste d'entrées.
- `400 Bad Request` si `limit` n'est pas un entier.

### 6.7 GET /api/profiles

Retourne tous les profils, ou ceux d'un type donné.

Paramètres query:
- `type` : optionnel, `data`, `image`, `audio`, `document`

Comportement:
- sans paramètre, retourne tous les profils.
- avec `type`, retourne uniquement les profils associés.

Réponses possibles:
- `200 OK`
- `400 Bad Request` si le type est invalide.

### 6.8 POST /api/profiles

Crée un nouveau profil.

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Body JSON attendu:

```json
{
  "type": "data",
  "name": "Mon profil",
  "source": "json",
  "target": "yaml"
}
```

Réponses possibles:
- `201 Created`
- `400 Bad Request` si un champ manque ou si le type est invalide.

### 6.9 DELETE /api/profiles/<conversion_type>/<profile_id>

Supprime un profil.

Sécurité:
- protégée par `X-API-Key` si la clé est configurée.

Réponses possibles:
- `200 OK` si le profil est supprimé.
- `404 Not Found` si le profil n'existe pas.
- `400 Bad Request` si le type est invalide.

## 7. Codes de retour fréquents

- `200 OK`: requête réussie.
- `201 Created`: création de job ou de profil.
- `400 Bad Request`: données invalides.
- `401 Unauthorized`: clé API absente ou incorrecte.
- `404 Not Found`: ressource introuvable.
- `413 Payload Too Large`: lot trop volumineux.
- `500 Internal Server Error`: erreur inattendue.

## 8. Exemples d'utilisation

### Vérifier les jobs

```bash
curl "http://127.0.0.1:5000/api/jobs"
```

### Consulter l'historique

```bash
curl "http://127.0.0.1:5000/api/history?limit=20"
```

### Lister les profils de données

```bash
curl "http://127.0.0.1:5000/api/profiles?type=data"
```

### Créer un profil

```bash
curl -X POST "http://127.0.0.1:5000/api/profiles" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: VOTRE_CLE" \
  -d '{"type":"data","name":"JSON vers YAML","source":"json","target":"yaml"}'
```

### Supprimer un profil

```bash
curl -X DELETE "http://127.0.0.1:5000/api/profiles/data/json2yaml_abc123" \
  -H "X-API-Key: VOTRE_CLE"
```

## 9. Notes techniques

- Les services utilisés par l'API sont partagés via `services/services_container.py`.
- Les jobs sont stockés en mémoire et la persistance longue durée repose sur `data/history.json` et `data/profiles.json`.
- Les fichiers convertis par l'API sont écrits dans `uploads/api_exports/`.
- Le monitoring de l'UI consomme `/api/jobs` pour calculer les statistiques visibles dans l'interface.
- L'API s'appuie sur la logique métier définie dans `services/` et sur les fonctions de conversion du module `converter.py`.

## 10. Références utiles

- Routes API: [routes/api.py](../routes/api.py)
- Services partagés: [services/services_container.py](../services/services_container.py)
- Configuration: [config.py](../config.py)
- Modèles: [models.py](../models.py)
