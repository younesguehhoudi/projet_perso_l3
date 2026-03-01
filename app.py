import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    after_this_request,
    jsonify,
)
from werkzeug.utils import secure_filename

from converter import (
    convertir_donnees,
    convertir_image,
    convertir_svg_vers_png,
    convertir_audio,
    convertir_document,
    ConversionError,
)


REP_BASE = Path(__file__).resolve().parent
REP_UPLOADS = REP_BASE / "uploads"
REP_UPLOADS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(REP_UPLOADS)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 Mo
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")


JOBS: dict[str, dict] = {}
JOB_ORDER: list[str] = []
JOBS_LOCK = Lock()
MAX_JOBS_MEMOIRE = 200

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _creer_job(type_conversion: str, format_cible: str, nb_fichiers: int) -> str:
    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "type": type_conversion,
        "target_format": format_cible,
        "status": "en_attente",
        "files_count": nb_fichiers,
        "success_count": 0,
        "error_count": 0,
        "message": "",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
        JOB_ORDER.append(job_id)
        while len(JOB_ORDER) > MAX_JOBS_MEMOIRE:
            ancien = JOB_ORDER.pop(0)
            JOBS.pop(ancien, None)
    return job_id


def _maj_job(job_id: str, **kwargs) -> None:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            return
        job.update(kwargs)
        job["updated_at"] = _now_iso()


def _normaliser_image(fmt: str) -> str:
    return "jpg" if fmt in {"jpg", "jpeg"} else fmt


def _valider_mime_et_extension(type_conversion: str, extension: str, mimetype_entree: str) -> None:
    attendus = MIME_ATTENDUS_PAR_TYPE.get(type_conversion, {}).get(extension, set())
    mime = (mimetype_entree or "").lower().split(";")[0].strip()

    if not mime or mime == "application/octet-stream" or not attendus:
        return
    if mime not in attendus:
        raise ConversionError("Le type MIME du fichier ne correspond pas à l'extension.")


def _convertir_un_fichier(
    *,
    type_conversion: str,
    format_cible: str,
    nom_original: str,
    octets_entree: bytes,
    txt_encoding: str,
    mimetype_entree: str,
) -> tuple[bytes, str, str]:
    ext_source = Path(nom_original).suffix.lower().lstrip(".")
    if not ext_source:
        raise ConversionError("Impossible de détecter le format du fichier.")

    _valider_mime_et_extension(type_conversion, ext_source, mimetype_entree)

    if type_conversion == "image":
        if ext_source not in {"png", "jpg", "jpeg", "webp", "svg"}:
            raise ConversionError("Format image source non supporté (PNG, JPG, WebP, SVG).")

        source_normalise = _normaliser_image(ext_source)
        cible_normalise = _normaliser_image(format_cible)

        if source_normalise == cible_normalise and ext_source != "svg":
            raise ConversionError(f"L'image est déjà au format {format_cible.upper()}.")

        if format_cible not in {"png", "jpg", "jpeg", "webp"}:
            raise ConversionError("Format de sortie invalide pour les images (PNG, JPG, WebP).")

        if ext_source == "svg":
            if format_cible != "png":
                raise ConversionError("Pour les SVG, seul le format PNG est supporté.")
            return convertir_svg_vers_png(octets_entree), "png", "image/png"

        octets_sortie = convertir_image(octets_entree, ext_source, format_cible)
        ext_sortie = "jpg" if format_cible == "jpeg" else format_cible
        carte_mimetype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
        return octets_sortie, ext_sortie, carte_mimetype.get(format_cible, "application/octet-stream")

    if type_conversion == "audio":
        if ext_source not in {"mp4", "mp3"}:
            raise ConversionError("Format audio source non supporté (MP4 ou MP3).")
        if format_cible not in {"mp3", "wav"}:
            raise ConversionError("Format de sortie invalide pour l'audio (MP3 ou WAV).")
        if ext_source == "mp4" and format_cible != "mp3":
            raise ConversionError("Pour les MP4, seul le format MP3 est supporté.")
        if ext_source == "mp3" and format_cible != "wav":
            raise ConversionError("Pour les MP3, seul le format WAV est supporté.")
        if ext_source == format_cible:
            raise ConversionError(f"Le fichier est déjà au format {format_cible.upper()}.")

        octets_sortie = convertir_audio(octets_entree, ext_source, format_cible)
        carte_mimetype_audio = {"mp3": "audio/mpeg", "wav": "audio/wav"}
        return octets_sortie, format_cible, carte_mimetype_audio.get(format_cible, "application/octet-stream")

    if type_conversion == "document":
        formats_docs = {"pdf", "docx", "txt"}
        if ext_source not in formats_docs:
            raise ConversionError("Format document source non supporté (PDF, DOCX ou TXT).")
        if format_cible not in formats_docs:
            raise ConversionError("Format de sortie invalide pour les documents (PDF, DOCX ou TXT).")
        if ext_source == format_cible:
            raise ConversionError(f"Le fichier est déjà au format {format_cible.upper()}.")

        octets_sortie = convertir_document(octets_entree, ext_source, format_cible, txt_encoding=txt_encoding)
        carte_mimetype_docs = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
        }
        return octets_sortie, format_cible, carte_mimetype_docs.get(format_cible, "application/octet-stream")

    if format_cible not in {"json", "yaml"}:
        raise ConversionError("Format de sortie invalide (JSON ou YAML).")

    if ext_source not in {"json", "yaml", "yml", "txt", "conf"}:
        raise ConversionError("Format de fichier source non supporté pour les données.")

    if ext_source in {"json", "yaml", "yml"}:
        source_normalise = "json" if ext_source == "json" else "yaml"
        if source_normalise == format_cible:
            raise ConversionError(f"Le fichier est déjà au format {format_cible.upper()}.")

    try:
        texte = octets_entree.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ConversionError("Le fichier doit être un texte UTF-8 (JSON/YAML).") from e

    texte_sortie = convertir_donnees(texte, format_cible)
    mimetype = "application/json" if format_cible == "json" else "application/x-yaml"
    return texte_sortie.encode("utf-8"), ("json" if format_cible == "json" else "yaml"), mimetype


@app.route("/")
def index():
    return redirect(url_for("page_data"))


@app.route("/data")
def page_data():
    return render_template("data.html", active_page="data")


@app.route("/images")
def page_images():
    return render_template("images.html", active_page="images")


@app.route("/audio")
def page_audio():
    return render_template("audio.html", active_page="audio")


@app.route("/documents")
def page_documents():
    return render_template("documents.html", active_page="documents")


@app.route("/jobs", methods=["GET"])
def jobs():
    with JOBS_LOCK:
        data = [JOBS[job_id] for job_id in reversed(JOB_ORDER[-30:]) if job_id in JOBS]
    return jsonify(data)


@app.route("/convert", methods=["POST"])
def convert():
    format_cible = request.form.get("target_format", "").lower()
    type_conversion = request.form.get("conversion_type", "data").lower()
    txt_encoding = request.form.get("txt_encoding", "utf-8").lower().strip()
    fichiers = [f for f in request.files.getlist("file") if f and f.filename]

    if not fichiers:
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for("index"))

    if type_conversion not in {"data", "image", "audio", "document"}:
        flash("Type de conversion invalide.", "error")
        return redirect(url_for("index"))

    job_id = _creer_job(type_conversion, format_cible, len(fichiers))
    _maj_job(job_id, status="en_cours")

    temp_paths: list[Path] = []
    sorties: list[tuple[str, Path, str]] = []
    erreurs: list[str] = []

    @after_this_request
    def nettoyage_temp(reponse):
        for chemin in temp_paths:
            try:
                chemin.unlink(missing_ok=True)
            except Exception:
                pass
        return reponse

    try:
        for fichier in fichiers:
            nom_original = secure_filename(fichier.filename)
            prefixe_unique = uuid.uuid4().hex
            nom_sauvegarde = f"{prefixe_unique}_{nom_original or 'upload'}"
            chemin_sauvegarde = REP_UPLOADS / nom_sauvegarde
            fichier.save(chemin_sauvegarde)
            temp_paths.append(chemin_sauvegarde)

            try:
                octets_entree = chemin_sauvegarde.read_bytes()
                octets_sortie, ext_sortie, mimetype_sortie = _convertir_un_fichier(
                    type_conversion=type_conversion,
                    format_cible=format_cible,
                    nom_original=nom_original,
                    octets_entree=octets_entree,
                    txt_encoding=txt_encoding,
                    mimetype_entree=fichier.mimetype or "",
                )

                base_nom = Path(nom_original).stem or "converted"
                nom_sortie = f"{base_nom}_{prefixe_unique}.{ext_sortie}"
                chemin_sortie = REP_UPLOADS / nom_sortie
                chemin_sortie.write_bytes(octets_sortie)
                temp_paths.append(chemin_sortie)
                sorties.append((nom_sortie, chemin_sortie, mimetype_sortie))
            except ConversionError as e:
                erreurs.append(f"{nom_original}: {str(e)}")
            except Exception:
                erreurs.append(f"{nom_original}: erreur inattendue pendant la conversion")

        if not sorties:
            _maj_job(job_id, status="erreur", success_count=0, error_count=len(erreurs), message="Toutes les conversions ont échoué")
            flash("Aucun fichier n'a pu être converti. Vérifiez les formats et réessayez.", "error")
            return redirect(url_for("index"))

        if len(fichiers) == 1 and not erreurs:
            _maj_job(job_id, status="termine", success_count=1, error_count=0, message="Conversion terminée")
            nom_sortie, chemin_sortie, mimetype = sorties[0]
            return send_file(chemin_sortie, as_attachment=True, download_name=nom_sortie, mimetype=mimetype)

        nom_zip = f"batch_{job_id[:8]}.zip"
        chemin_zip = REP_UPLOADS / nom_zip
        with zipfile.ZipFile(chemin_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for nom_sortie, chemin_sortie, _ in sorties:
                zipf.write(chemin_sortie, arcname=nom_sortie)
            if erreurs:
                zipf.writestr("errors.txt", "\n".join(erreurs) + "\n")
        temp_paths.append(chemin_zip)

        if erreurs:
            _maj_job(
                job_id,
                status="erreur",
                success_count=len(sorties),
                error_count=len(erreurs),
                message="Lot terminé avec erreurs",
            )
            flash(f"Lot converti avec {len(erreurs)} erreur(s). Voir errors.txt dans le ZIP.", "warning")
        else:
            _maj_job(
                job_id,
                status="termine",
                success_count=len(sorties),
                error_count=0,
                message="Lot terminé",
            )

        return send_file(chemin_zip, as_attachment=True, download_name=nom_zip, mimetype="application/zip")
    except Exception:
        _maj_job(job_id, status="erreur", success_count=len(sorties), error_count=max(1, len(erreurs)), message="Erreur inattendue")
        flash("Une erreur inattendue est survenue pendant le traitement du lot.", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    # Par défaut, l'app n'est pas exposée sur le réseau (usage local uniquement)
    host = os.environ.get("BIND", "127.0.0.1")
    app.run(debug=True, host=host, port=port)
