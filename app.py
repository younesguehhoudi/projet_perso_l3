import os
import uuid
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect,
    url_for,
    flash,
    after_this_request,
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    fichier = request.files.get("file")
    format_cible = request.form.get("target_format", "").lower()
    type_conversion = request.form.get("conversion_type", "data").lower()
    txt_encoding = request.form.get("txt_encoding", "utf-8").lower().strip()

    if not fichier or fichier.filename == "":
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for("index"))

    nom_original = secure_filename(fichier.filename)
    prefixe_unique = uuid.uuid4().hex
    nom_sauvegarde = f"{prefixe_unique}_{nom_original or 'upload'}"
    chemin_sauvegarde = REP_UPLOADS / nom_sauvegarde

    # Sauvegarder le fichier uploadé sur disque
    fichier.save(chemin_sauvegarde)

    # Gérer la conversion d'image
    if type_conversion == "image":
        # Détecter le format source depuis l'extension du fichier
        ext_source = Path(nom_original).suffix.lower().lstrip(".")
        if not ext_source:
            flash("Impossible de détecter le format du fichier image.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        
        # Normaliser les formats pour comparaison
        source_normalise = "jpg" if ext_source in {"jpg", "jpeg"} else ext_source
        cible_normalise = "jpg" if format_cible in {"jpg", "jpeg"} else format_cible
        
        if source_normalise == cible_normalise and ext_source != "svg":
            flash(f"L'image est déjà au format {format_cible.upper()}. Choisissez un autre format de sortie.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        
        if format_cible not in {"png", "jpg", "jpeg", "webp"}:
            flash("Format de sortie invalide pour les images (choisissez PNG, JPG ou WebP).", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        
        # Conversion SVG → PNG (canal dédié)
        if ext_source == "svg":
            if format_cible != "png":
                flash("Pour les SVG, seul le format PNG est supporté.", "error")
                chemin_sauvegarde.unlink(missing_ok=True)
                return redirect(url_for("index"))
            try:
                octets_sortie = convertir_svg_vers_png(chemin_sauvegarde.read_bytes())
            except ConversionError as e:
                flash(str(e), "error")
                chemin_sauvegarde.unlink(missing_ok=True)
                return redirect(url_for("index"))
            except Exception:
                flash("Une erreur inattendue est survenue pendant la conversion SVG.", "error")
                chemin_sauvegarde.unlink(missing_ok=True)
                return redirect(url_for("index"))

            base_nom = Path(nom_original).stem or "converted"
            nom_sortie = f"{base_nom}_{prefixe_unique}.png"
            chemin_sortie = REP_UPLOADS / nom_sortie
            chemin_sortie.write_bytes(octets_sortie)

            @after_this_request
            def nettoyage_temp(reponse):
                try:
                    chemin_sauvegarde.unlink(missing_ok=True)
                except Exception:
                    pass
                try:
                    chemin_sortie.unlink(missing_ok=True)
                except Exception:
                    pass
                return reponse

            return send_file(
                chemin_sortie,
                as_attachment=True,
                download_name=nom_sortie,
                mimetype="image/png",
            )
        
        try:
            octets_entree = chemin_sauvegarde.read_bytes()
            octets_sortie = convertir_image(octets_entree, ext_source, format_cible)
        except ConversionError as e:
            flash(str(e), "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        except Exception:
            flash("Une erreur inattendue est survenue pendant la conversion.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        
        # Construire le nom du fichier de sortie
        base_nom = Path(nom_original).stem or "converted"
        ext_sortie = f".{format_cible}" if format_cible != "jpeg" else ".jpg"
        nom_sortie = f"{base_nom}_{prefixe_unique}{ext_sortie}"
        chemin_sortie = REP_UPLOADS / nom_sortie
        chemin_sortie.write_bytes(octets_sortie)
        
        # Nettoyage et envoi
        @after_this_request
        def nettoyage_temp(reponse):
            try:
                chemin_sauvegarde.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                chemin_sortie.unlink(missing_ok=True)
            except Exception:
                pass
            return reponse
        
        carte_mimetype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
        mimetype = carte_mimetype.get(format_cible, "application/octet-stream")
        return send_file(chemin_sortie, as_attachment=True, download_name=nom_sortie, mimetype=mimetype)

    # Gérer la conversion audio (MP4 → MP3, MP3 → WAV)
    if type_conversion == "audio":
        ext_source = Path(nom_original).suffix.lower().lstrip(".")
        if not ext_source:
            flash("Impossible de détecter le format du fichier audio.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if ext_source not in {"mp4", "mp3"}:
            flash("Format audio source non supporté (MP4 ou MP3).", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if format_cible not in {"mp3", "wav"}:
            flash("Format de sortie invalide pour l'audio (MP3 ou WAV).", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if ext_source == "mp4" and format_cible != "mp3":
            flash("Pour les MP4, seul le format MP3 est supporté.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if ext_source == "mp3" and format_cible != "wav":
            flash("Pour les MP3, seul le format WAV est supporté.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        
        if ext_source == format_cible:
            flash(f"Le fichier est déjà au format {format_cible.upper()}. Choisissez un autre format de sortie.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        try:
            octets_entree = chemin_sauvegarde.read_bytes()
            octets_sortie = convertir_audio(octets_entree, ext_source, format_cible)
        except ConversionError as e:
            flash(str(e), "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        except Exception:
            flash("Une erreur inattendue est survenue pendant la conversion audio.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        base_nom = Path(nom_original).stem or "converted"
        nom_sortie = f"{base_nom}_{prefixe_unique}.{format_cible}"
        chemin_sortie = REP_UPLOADS / nom_sortie
        chemin_sortie.write_bytes(octets_sortie)

        @after_this_request
        def nettoyage_temp(reponse):
            try:
                chemin_sauvegarde.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                chemin_sortie.unlink(missing_ok=True)
            except Exception:
                pass
            return reponse

        carte_mimetype_audio = {"mp3": "audio/mpeg", "wav": "audio/wav"}
        mimetype = carte_mimetype_audio.get(format_cible, "application/octet-stream")
        return send_file(chemin_sortie, as_attachment=True, download_name=nom_sortie, mimetype=mimetype)

    # Gérer la conversion de documents (PDF/DOCX/TXT)
    if type_conversion == "document":
        ext_source = Path(nom_original).suffix.lower().lstrip(".")
        if not ext_source:
            flash("Impossible de détecter le format du document.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        formats_docs = {"pdf", "docx", "txt"}
        if ext_source not in formats_docs:
            flash("Format document source non supporté (PDF, DOCX ou TXT).", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if format_cible not in formats_docs:
            flash("Format de sortie invalide pour les documents (PDF, DOCX ou TXT).", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        if ext_source == format_cible:
            flash(f"Le fichier est déjà au format {format_cible.upper()}. Choisissez un autre format de sortie.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        mime_attendus = {
            "pdf": {"application/pdf"},
            "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            "txt": {"text/plain"},
        }
        mimetype_entree = (fichier.mimetype or "").lower().split(";")[0].strip()
        if mimetype_entree and mimetype_entree != "application/octet-stream":
            if mimetype_entree not in mime_attendus.get(ext_source, set()):
                flash("Le type MIME du document ne correspond pas à l'extension.", "error")
                chemin_sauvegarde.unlink(missing_ok=True)
                return redirect(url_for("index"))

        try:
            octets_entree = chemin_sauvegarde.read_bytes()
            octets_sortie = convertir_document(octets_entree, ext_source, format_cible, txt_encoding=txt_encoding)
        except ConversionError as e:
            flash(str(e), "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))
        except Exception:
            flash("Une erreur inattendue est survenue pendant la conversion document.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

        base_nom = Path(nom_original).stem or "converted"
        nom_sortie = f"{base_nom}_{prefixe_unique}.{format_cible}"
        chemin_sortie = REP_UPLOADS / nom_sortie
        chemin_sortie.write_bytes(octets_sortie)

        @after_this_request
        def nettoyage_temp(reponse):
            try:
                chemin_sauvegarde.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                chemin_sortie.unlink(missing_ok=True)
            except Exception:
                pass
            return reponse

        carte_mimetype_docs = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
        }
        mimetype = carte_mimetype_docs.get(format_cible, "application/octet-stream")
        return send_file(chemin_sortie, as_attachment=True, download_name=nom_sortie, mimetype=mimetype)

    # Gérer la conversion de données (JSON/YAML) - code existant
    if format_cible not in {"json", "yaml"}:
        flash("Format de sortie invalide (choisissez JSON ou YAML).", "error")
        chemin_sauvegarde.unlink(missing_ok=True)
        return redirect(url_for("index"))
    
    # Détecter le format source
    ext_source_data = Path(nom_original).suffix.lower().lstrip(".")
    if ext_source_data in {"json", "yaml", "yml"}:
        source_normalise = "json" if ext_source_data == "json" else "yaml"
        if source_normalise == format_cible:
            flash(f"Le fichier est déjà au format {format_cible.upper()}. Choisissez un autre format de sortie.", "error")
            chemin_sauvegarde.unlink(missing_ok=True)
            return redirect(url_for("index"))

    try:
        texte = chemin_sauvegarde.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        flash("Le fichier doit être un texte UTF-8 (JSON/YAML).", "error")
        chemin_sauvegarde.unlink(missing_ok=True)
        return redirect(url_for("index"))

    # Effectuer la conversion
    try:
        texte_sortie = convertir_donnees(texte, format_cible)
    except ConversionError as e:
        flash(str(e), "error")
        chemin_sauvegarde.unlink(missing_ok=True)
        return redirect(url_for("index"))
    except Exception:
        flash("Une erreur inattendue est survenue pendant la conversion.", "error")
        chemin_sauvegarde.unlink(missing_ok=True)
        return redirect(url_for("index"))

    # Construire le nom du fichier de sortie (préserver le nom de base, changer l'extension, assurer l'unicité)
    base_nom = Path(nom_original).stem or "converted"
    ext_sortie = ".json" if format_cible == "json" else ".yaml"
    nom_sortie = f"{base_nom}_{prefixe_unique}{ext_sortie}"
    chemin_sortie = REP_UPLOADS / nom_sortie
    chemin_sortie.write_text(texte_sortie, encoding="utf-8")

    # S'assurer que les fichiers temporaires sont nettoyés après l'envoi de la réponse
    @after_this_request
    def nettoyage_temp(reponse):
        try:
            chemin_sauvegarde.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            chemin_sortie.unlink(missing_ok=True)
        except Exception:
            pass
        return reponse

    # Envoyer le fichier pour téléchargement
    mimetype = "application/json" if format_cible == "json" else "application/x-yaml"
    return send_file(chemin_sortie, as_attachment=True, download_name=nom_sortie, mimetype=mimetype)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # Par défaut, l'app n'est pas exposée sur le réseau (usage local uniquement)
    host = os.environ.get("BIND", "127.0.0.1")
    app.run(debug=True, host=host, port=port)
