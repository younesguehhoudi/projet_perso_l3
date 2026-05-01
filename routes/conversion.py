"""Routes de conversion (formulaire web)."""

import zipfile
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import (
    Blueprint,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    after_this_request,
)

from models import ConversionError
import config
import utils
from services import JobService, ConversionService, HistoryService
import uuid

# Importer les instances partagées du conteneur
from services.services_container import job_service, history_service, conversion_service

convert_bp = Blueprint("convert", __name__)


@convert_bp.route("/convert", methods=["POST"])
def convert():
    """Convertir des fichiers depuis le formulaire web."""
    target_format = request.form.get("target_format", "").lower()
    conversion_type = request.form.get("conversion_type", "data").lower()
    txt_encoding = request.form.get("txt_encoding", "utf-8").lower().strip()
    files = [f for f in request.files.getlist("file") if f and f.filename]
    
    if not files:
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for("pages.index"))
    
    try:
        utils.validate_conversion_request(conversion_type, target_format)
    except ConversionError as e:
        flash(str(e), "error")
        return redirect(url_for("pages.index"))
    
    total_size = utils.get_total_upload_size(files)
    if total_size > config.TAILLE_MAX_GLOBALE:
        flash("Taille totale des fichiers au-delà de la limite autorisée.", "error")
        return redirect(url_for("pages.index"))
    
    # Créer un job
    job_id = job_service.create_job(conversion_type, target_format, len(files))
    job_service.update_job(job_id, status="en_cours")
    
    temp_paths = []
    outputs = []
    errors = []
    source_formats = set()
    total_converted_size = 0
    
    @after_this_request
    def cleanup_temp(response):
        """Nettoyer les fichiers temporaires."""
        for path in temp_paths:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        return response
    
    try:
        for file in files:
            original_name = secure_filename(file.filename or "")
            unique_prefix = uuid.uuid4().hex
            save_name = f"{unique_prefix}_{original_name or 'upload'}"
            save_path = config.REP_UPLOADS / save_name
            file.save(save_path)
            temp_paths.append(save_path)
            
            # Tracker le format source
            ext = Path(original_name).suffix.lstrip('.').lower()
            if ext:
                source_formats.add(ext)
            
            try:
                input_bytes = save_path.read_bytes()
                output_bytes, output_format, mimetype = conversion_service.convert_file(
                    conversion_type=conversion_type,
                    target_format=target_format,
                    original_filename=original_name,
                    input_bytes=input_bytes,
                    mimetype_input=file.mimetype or "",
                    txt_encoding=txt_encoding,
                )
                
                base_name = Path(original_name).stem or "converted"
                output_name = f"{base_name}_{unique_prefix}.{output_format}"
                output_path = config.REP_UPLOADS / output_name
                output_path.write_bytes(output_bytes)
                temp_paths.append(output_path)
                total_converted_size += len(output_bytes)
                outputs.append((output_name, output_path, mimetype))
            except ConversionError as e:
                errors.append(f"{original_name}: {str(e)}")
            except Exception:
                errors.append(f"{original_name}: erreur inattendue pendant la conversion")
        
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
            flash("Aucun fichier n'a pu être converti. Vérifiez les formats et réessayez.", "error")
            return redirect(url_for("pages.index"))
        
        # Cas simple: un seul fichier, pas d'erreur
        if len(files) == 1 and not errors:
            job_service.update_job(
                job_id,
                status="termine",
                success_count=1,
                error_count=0,
                message="Conversion terminée",
            )
            history_service.add_entry(
                job_id=job_id,
                conversion_type=conversion_type,
                target_format=target_format,
                source_formats=source_formats,
                total_size=total_converted_size,
                files_count=1,
                success_count=1,
                error_count=0,
                status="termine",
            )
            output_name, output_path, mimetype = outputs[0]
            return send_file(
                output_path,
                as_attachment=True,
                download_name=output_name,
                mimetype=mimetype
            )
        
        # Cas multiple: créer un ZIP
        zip_name = f"batch_{job_id[:8]}.zip"
        zip_path = config.REP_UPLOADS / zip_name
        with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for output_name, output_path, _ in outputs:
                zf.write(output_path, arcname=output_name)
            if errors:
                zf.writestr("errors.txt", "\n".join(errors) + "\n")
        temp_paths.append(zip_path)
        
        if errors:
            job_service.update_job(
                job_id,
                status="erreur",
                success_count=len(outputs),
                error_count=len(errors),
                message="Lot terminé avec erreurs",
            )
            history_service.add_entry(
                job_id=job_id,
                conversion_type=conversion_type,
                target_format=target_format,
                source_formats=source_formats,
                total_size=total_converted_size,
                files_count=len(files),
                success_count=len(outputs),
                error_count=len(errors),
                status="erreur",
            )
            flash(f"Lot converti avec {len(errors)} erreur(s). Voir errors.txt dans le ZIP.", "warning")
        else:
            job_service.update_job(
                job_id,
                status="termine",
                success_count=len(outputs),
                error_count=0,
                message="Lot terminé",
            )
            history_service.add_entry(
                job_id=job_id,
                conversion_type=conversion_type,
                target_format=target_format,
                source_formats=source_formats,
                total_size=total_converted_size,
                files_count=len(files),
                success_count=len(outputs),
                error_count=0,
                status="termine",
            )
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=zip_name,
            mimetype="application/zip"
        )
    except Exception:
        job_service.update_job(
            job_id,
            status="erreur",
            success_count=len(outputs),
            error_count=max(1, len(errors)),
            message="Erreur inattendue",
        )
        history_service.add_entry(
            job_id=job_id,
            conversion_type=conversion_type,
            target_format=target_format,
            source_formats=source_formats,
            total_size=total_converted_size,
            files_count=len(files),
            success_count=len(outputs),
            error_count=max(1, len(errors)),
            status="erreur",
        )
        flash("Une erreur inattendue est survenue pendant le traitement du lot.", "error")
        return redirect(url_for("pages.index"))
