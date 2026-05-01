"""Routes API."""

import zipfile
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, send_file, url_for

from models import ConversionError
import config
import utils
from services import JobService, HistoryService, ProfileService, ConversionService

# Importer les instances partagées du conteneur
from services.services_container import job_service, history_service, profile_service, conversion_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


def check_api_key():
    """Vérifier la clé API.
    
    Returns:
        Tuple (is_valid, error_response)
    """
    if not config.CLE_API:
        return True, None
    
    key = request.headers.get("X-API-Key", "")
    if key != config.CLE_API:
        return False, jsonify({"error": "API key invalide ou absente."}), 401
    
    return True, None


@api_bp.route("/jobs", methods=["GET"])
def get_jobs():
    """Obtenir la liste des jobs récents."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    jobs = job_service.get_recent_jobs(limit=30)
    return jsonify([job.to_dict() for job in jobs])


@api_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """Obtenir le statut d'un job."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    job = job_service.get_job(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404
    
    return jsonify(job.to_dict())


@api_bp.route("/jobs/<job_id>/preview", methods=["GET"])
def get_job_preview(job_id: str):
    """Obtenir un aperçu du fichier de sortie d'un job."""
    job = job_service.get_job(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404
    
    if not job.api_output_path:
        return jsonify({"error": "Pas de fichier de sortie pour ce job."}), 404
    
    preview = utils.generate_preview(Path(job.api_output_path))
    return jsonify(preview)


@api_bp.route("/jobs/<job_id>/download", methods=["GET"])
def download_job(job_id: str):
    """Télécharger le fichier de sortie d'un job."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    job = job_service.get_job(job_id)
    if not job:
        return jsonify({"error": "Job introuvable."}), 404
    
    if not job.api_output_path or not Path(job.api_output_path).exists():
        return jsonify({"error": "Aucune sortie disponible pour ce job."}), 404
    
    file_path = Path(job.api_output_path)
    return send_file(
        file_path,
        as_attachment=True,
        download_name=job.api_output_name or file_path.name,
        mimetype=job.api_output_mimetype or "application/octet-stream"
    )


@api_bp.route("/history", methods=["GET"])
def get_history():
    """Obtenir l'historique des conversions."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    try:
        limit = int(request.args.get("limit", "20"))
    except ValueError:
        return jsonify({"error": "Le paramètre limit doit être un entier."}), 400
    
    return jsonify(history_service.get_recent(limit))


@api_bp.route("/profiles", methods=["GET"])
def get_profiles():
    """Obtenir les profils de conversion."""
    conversion_type = request.args.get("type", "").lower().strip()
    
    if conversion_type:
        if conversion_type not in config.FORMATS_CIBLES_AUTORISES:
            return jsonify({"error": "Type de conversion invalide."}), 400
        return jsonify(profile_service.get_profiles(conversion_type))
    
    return jsonify(profile_service.get_profiles())


@api_bp.route("/profiles", methods=["POST"])
def add_profile():
    """Créer un nouveau profil."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    try:
        data = request.get_json()
        conversion_type = data.get("type", "").lower().strip()
        name = data.get("name", "").strip()
        source = data.get("source", "").lower().strip()
        target = data.get("target", "").lower().strip()
        
        if not all([conversion_type, name, source, target]):
            return jsonify({"error": "Paramètres manquants (type, name, source, target)."}), 400
        
        if conversion_type not in config.FORMATS_CIBLES_AUTORISES:
            return jsonify({"error": "Type de conversion invalide."}), 400
        
        new_profile = profile_service.add_profile(conversion_type, name, source, target)
        return jsonify(new_profile), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/profiles/<conversion_type>/<profile_id>", methods=["DELETE"])
def delete_profile(conversion_type: str, profile_id: str):
    """Supprimer un profil."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    conversion_type = conversion_type.lower().strip()
    
    if conversion_type not in config.FORMATS_CIBLES_AUTORISES:
        return jsonify({"error": "Type de conversion invalide."}), 400
    
    if profile_service.delete_profile(conversion_type, profile_id):
        return jsonify({"message": "Profil supprimé."}), 200
    else:
        return jsonify({"error": "Profil introuvable."}), 404


@api_bp.route("/convert", methods=["POST"])
def convert():
    """Convertir des fichiers (API)."""
    is_valid, error = check_api_key()
    if not is_valid:
        return error
    
    target_format = request.form.get("target_format", "").lower().strip()
    conversion_type = request.form.get("conversion_type", "data").lower().strip()
    txt_encoding = request.form.get("txt_encoding", "utf-8").lower().strip()
    files = [f for f in request.files.getlist("file") if f and f.filename]
    
    if not files:
        return jsonify({"error": "Aucun fichier sélectionné."}), 400
    
    # Valider la requête
    try:
        utils.validate_conversion_request(conversion_type, target_format)
    except ConversionError as e:
        return jsonify({"error": str(e)}), 400
    
    # Vérifier la taille totale
    total_size = utils.get_total_upload_size(files)
    if total_size > config.TAILLE_MAX_GLOBALE:
        return jsonify({"error": "Taille totale des fichiers au-delà de la limite autorisée."}), 413
    
    # Créer un job
    job_id = job_service.create_job(conversion_type, target_format, len(files))
    job_service.update_job(job_id, status="en_cours")
    
    outputs = []
    errors = []
    source_formats = set()
    
    try:
        for file in files:
            original_name = secure_filename(file.filename or "")
            ext_source = Path(original_name).suffix.lower().lstrip(".")
            if ext_source:
                source_formats.add(utils.normalize_image_format(ext_source))
            
            input_bytes = file.read()
            if not input_bytes:
                errors.append(f"{original_name}: fichier vide")
                continue
            
            try:
                output_bytes, output_format, mimetype = conversion_service.convert_file(
                    conversion_type=conversion_type,
                    target_format=target_format,
                    original_filename=original_name,
                    input_bytes=input_bytes,
                    mimetype_input=file.mimetype or "",
                    txt_encoding=txt_encoding,
                )
                
                # Sauvegarder le fichier
                output_name = f"{Path(original_name).stem or 'converted'}_{__import__('uuid').uuid4().hex[:8]}.{output_format}"
                output_path = config.REP_API_EXPORTS / f"{job_id}_{output_name}"
                output_path.write_bytes(output_bytes)
                outputs.append((output_name, output_path, mimetype))
            except ConversionError as e:
                errors.append(f"{original_name}: {str(e)}")
            except Exception:
                errors.append(f"{original_name}: erreur inattendue pendant la conversion")
        
        # Traiter les résultats
        if not outputs:
            job_service.update_job(
                job_id,
                status="erreur",
                success_count=0,
                error_count=len(errors),
                message="Toutes les conversions ont échoué"
            )
            history_service.add_entry(
                job_id=job_id,
                conversion_type=conversion_type,
                target_format=target_format,
                source_formats=source_formats,
                total_size=total_size,
                files_count=len(files),
                success_count=0,
                error_count=len(errors),
                status="erreur",
            )
            return jsonify({
                "job_id": job_id,
                "status": "erreur",
                "errors": errors,
                "status_url": url_for("api.get_job_status", job_id=job_id, _external=False),
            }), 400
        
        if len(outputs) == 1 and not errors:
            # Un seul fichier sans erreur
            output_name, output_path, mimetype = outputs[0]
            job_service.update_job(
                job_id,
                status="termine",
                success_count=1,
                error_count=0,
                message="Conversion terminée",
                api_output_path=str(output_path),
                api_output_name=output_name,
                api_output_mimetype=mimetype,
            )
            status = "termine"
        else:
            # Plusieurs fichiers ou erreurs: créer un ZIP
            zip_name = f"api_batch_{job_id[:8]}.zip"
            zip_path = config.REP_API_EXPORTS / zip_name
            with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                for output_name, output_path, _ in outputs:
                    zf.write(output_path, arcname=output_name)
                if errors:
                    zf.writestr("errors.txt", "\n".join(errors) + "\n")
            
            # Nettoyer les fichiers individuels
            for _, output_path, _ in outputs:
                utils.delete_file(str(output_path))
            
            status = "erreur" if errors else "termine"
            job_service.update_job(
                job_id,
                status=status,
                success_count=len(outputs),
                error_count=len(errors),
                message="Lot terminé avec erreurs" if errors else "Lot terminé",
                api_output_path=str(zip_path),
                api_output_name=zip_name,
                api_output_mimetype="application/zip",
            )
        
        # Enregistrer dans l'historique
        history_service.add_entry(
            job_id=job_id,
            conversion_type=conversion_type,
            target_format=target_format,
            source_formats=source_formats,
            total_size=total_size,
            files_count=len(files),
            success_count=len(outputs),
            error_count=len(errors),
            status=status,
        )
        
        return jsonify({
            "job_id": job_id,
            "status": status,
            "success_count": len(outputs),
            "error_count": len(errors),
            "errors": errors,
            "status_url": url_for("api.get_job_status", job_id=job_id, _external=False),
            "download_url": url_for("api.download_job", job_id=job_id, _external=False),
        }), 201
    except Exception:
        job_service.update_job(
            job_id,
            status="erreur",
            success_count=len(outputs),
            error_count=max(1, len(errors)),
            message="Erreur inattendue"
        )
        history_service.add_entry(
            job_id=job_id,
            conversion_type=conversion_type,
            target_format=target_format,
            source_formats=source_formats,
            total_size=total_size,
            files_count=len(files),
            success_count=len(outputs),
            error_count=max(1, len(errors)),
            status="erreur",
        )
        return jsonify({"error": "Une erreur inattendue est survenue."}), 500
