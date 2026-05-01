"""Application Flask principale (refactorisée)."""

import os
import uuid
from pathlib import Path
from threading import Lock
from flask import Flask

import config
from routes import pages_bp, api_bp, convert_bp
from services import JobService, HistoryService, ProfileService

# Importer les services partagés depuis le conteneur unique
from services.services_container import job_service as _job_service
from services.services_container import history_service as _history_service
from services.services_container import profile_service as _profile_service

# Exports pour compatibilité avec les tests
JOBS = {}
JOBS_LOCK = Lock()
HISTORY_LOCK = Lock()
PROFILS_LOCK = Lock()
HISTORIQUE_PATH = config.HISTORIQUE_PATH
PROFILS_PATH = config.PROFILS_PATH
CLE_API = config.CLE_API

# Fonctions de compatibilité avec les tests
def _profils_par_defaut():
    """Retourner les profils par défaut."""
    return config.PROFILS_PAR_DEFAUT

def _charger_profils():
    """Charger les profils."""
    return _profile_service.load_all()

def _sauver_profils(profils):
    """Sauvegarder les profils."""
    _profile_service._save(profils)

def _charger_historique():
    """Charger l'historique."""
    return _history_service._load()

def _sauver_historique(entries):
    """Sauvegarder l'historique."""
    _history_service._save(entries)

def _ajouter_historique(entry):
    """Ajouter une entrée d'historique."""
    history = _history_service._load()
    history.append(entry)
    if len(history) > config.MAX_HISTORY_ENTRIES:
        history = history[-config.MAX_HISTORY_ENTRIES:]
    _history_service._save(history)
    return entry

def _dernier_historique(limit):
    """Obtenir les entrées d'historique récentes."""
    return _history_service.get_recent(limit)

def _obtenir_profils(conversion_type):
    """Obtenir les profils pour un type de conversion."""
    return _profile_service.get_profiles(conversion_type)

def _ajouter_profil(conversion_type, nom, source, target):
    """Ajouter un profil."""
    return _profile_service.add_profile(conversion_type, nom, source, target)

def _supprimer_profil(conversion_type, profile_id):
    """Supprimer un profil."""
    return _profile_service.delete_profile(conversion_type, profile_id)

def _creer_job(conversion_type, target_format, files_count):
    """Créer un nouveau job."""
    job_id = _job_service.create_job(conversion_type, target_format, files_count)
    job = _job_service.get_job(job_id)
    if job:
        JOBS[job_id] = job.to_dict()
    return job_id

def _maj_job(job_id, **kwargs):
    """Mettre à jour un job."""
    _job_service.update_job(job_id, **kwargs)
    job = _job_service.get_job(job_id)
    if job:
        JOBS[job_id] = job.to_dict()


def create_app():
    """Créer et configurer l'application Flask."""
    app = Flask(__name__)
    
    # Configuration
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.secret_key = config.SECRET_KEY
    
    # Enregistrer les blueprints
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(convert_bp)
    
    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("BIND", "127.0.0.1")
    app.run(debug=True, host=host, port=port)
