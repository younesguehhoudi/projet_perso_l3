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

from converter import convertir_donnees, convertir_image, convertir_svg_vers_png, ConversionError


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

    # Gérer la conversion de données (JSON/YAML) - code existant
    if format_cible not in {"json", "yaml"}:
        flash("Format de sortie invalide (choisissez JSON ou YAML).", "error")
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
