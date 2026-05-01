"""Configuration centralisée du projet."""

import os
from pathlib import Path

# Chemins
REP_BASE = Path(__file__).resolve().parent
REP_UPLOADS = REP_BASE / "uploads"
REP_UPLOADS.mkdir(parents=True, exist_ok=True)
REP_API_EXPORTS = REP_UPLOADS / "api_exports"
REP_API_EXPORTS.mkdir(parents=True, exist_ok=True)

# Nouveau dossier pour données persistantes
REP_DATA = REP_BASE / "data"
REP_DATA.mkdir(parents=True, exist_ok=True)

# Fichiers de données (déplacés dans data/)
HISTORIQUE_PATH = REP_DATA / "history.json"
PROFILS_PATH = REP_DATA / "profiles.json"

# Configuration Flask
UPLOAD_FOLDER = str(REP_UPLOADS)
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

# API
CLE_API = os.environ.get("LOCAL_API_KEY", "").strip()
TAILLE_MAX_GLOBALE = int(os.environ.get("MAX_GLOBAL_UPLOAD_MB", "20")) * 1024 * 1024

# Limites mémoire
MAX_JOBS_MEMOIRE = 200
MAX_HISTORY_ENTRIES = 1000
MAX_API_HISTORY_RETURNS = 100

# Types MIME par format
MIME_ATTENDUS_PAR_TYPE = {
    "data": {
        "json": {"application/json", "text/json"},
        "yaml": {
            "application/x-yaml",
            "application/yaml",
            "text/yaml",
            "text/x-yaml",
            "application/octet-stream",
        },
        "yml": {
            "application/x-yaml",
            "application/yaml",
            "text/yaml",
            "text/x-yaml",
            "application/octet-stream",
        },
    },
    "image": {
        "png": {"image/png"},
        "jpg": {"image/jpeg"},
        "jpeg": {"image/jpeg"},
        "webp": {"image/webp"},
        "svg": {"image/svg+xml", "text/xml", "application/xml"},
    },
    "audio": {
        "mp4": {"audio/mp4", "video/mp4"},
        "mp3": {"audio/mpeg", "audio/mp3"},
    },
    "document": {
        "pdf": {"application/pdf"},
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "txt": {"text/plain"},
    },
}

# Formats cibles autorisés par type
FORMATS_CIBLES_AUTORISES = {
    "data": {"json", "yaml"},
    "image": {"png", "jpg", "jpeg", "webp", "pdf"},
    "audio": {"mp3", "wav"},
    "document": {"pdf", "docx", "txt"},
}

# Profils de conversion par défaut
PROFILS_PAR_DEFAUT = {
    "data": [
        {"id": "json2yaml", "name": "JSON → YAML", "source": "json", "target": "yaml"},
        {"id": "yaml2json", "name": "YAML → JSON", "source": "yaml", "target": "json"},
    ],
    "image": [
        {"id": "png2jpg", "name": "PNG → JPG", "source": "png", "target": "jpg"},
        {"id": "jpg2webp", "name": "JPG → WebP", "source": "jpg", "target": "webp"},
        {"id": "webp2jpg", "name": "WebP → JPG", "source": "webp", "target": "jpg"},
        {"id": "png2webp", "name": "PNG → WebP", "source": "png", "target": "webp"},
        {"id": "png2pdf", "name": "PNG → PDF", "source": "png", "target": "pdf"},
        {"id": "svg2png", "name": "SVG → PNG", "source": "svg", "target": "png"},
    ],
    "audio": [
        {"id": "mp42mp3", "name": "MP4 → MP3", "source": "mp4", "target": "mp3"},
        {"id": "mp32wav", "name": "MP3 → WAV", "source": "mp3", "target": "wav"},
    ],
    "document": [
        {"id": "pdf2docx", "name": "PDF → DOCX", "source": "pdf", "target": "docx"},
        {"id": "docx2pdf", "name": "DOCX → PDF", "source": "docx", "target": "pdf"},
        {"id": "pdf2txt", "name": "PDF → TXT", "source": "pdf", "target": "txt"},
        {"id": "txt2pdf", "name": "TXT → PDF", "source": "txt", "target": "pdf"},
        {"id": "docx2txt", "name": "DOCX → TXT", "source": "docx", "target": "txt"},
        {"id": "txt2docx", "name": "TXT → DOCX", "source": "txt", "target": "docx"},
    ],
}
