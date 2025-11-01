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

from converter import convert_data, ConversionError


BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOADS_DIR)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    file = request.files.get("file")
    target_format = request.form.get("target_format", "").lower()

    if not file or file.filename == "":
        flash("Aucun fichier sélectionné.", "error")
        return redirect(url_for("index"))

    if target_format not in {"json", "yaml"}:
        flash("Format de sortie invalide (choisissez JSON ou YAML).", "error")
        return redirect(url_for("index"))

    original_name = secure_filename(file.filename)
    unique_prefix = uuid.uuid4().hex
    saved_name = f"{unique_prefix}_{original_name or 'upload'}"
    saved_path = UPLOADS_DIR / saved_name

    # Save uploaded file to disk
    file.save(saved_path)

    try:
        text = saved_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        flash("Le fichier doit être un texte UTF-8 (JSON/YAML).", "error")
        saved_path.unlink(missing_ok=True)
        return redirect(url_for("index"))

    # Perform conversion
    try:
        output_text = convert_data(text, target_format)
    except ConversionError as e:
        flash(str(e), "error")
        saved_path.unlink(missing_ok=True)
        return redirect(url_for("index"))
    except Exception:
        flash("Une erreur inattendue est survenue pendant la conversion.", "error")
        saved_path.unlink(missing_ok=True)
        return redirect(url_for("index"))

    # Build output filename (preserve base name, change extension, ensure uniqueness)
    base_stem = Path(original_name).stem or "converted"
    out_ext = ".json" if target_format == "json" else ".yaml"
    out_name = f"{base_stem}_{unique_prefix}{out_ext}"
    out_path = UPLOADS_DIR / out_name
    out_path.write_text(output_text, encoding="utf-8")

    # Ensure temporary files are cleaned up after response is sent
    @after_this_request
    def cleanup_temp(response):
        try:
            saved_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        return response

    # Send file for download
    mimetype = "application/json" if target_format == "json" else "application/x-yaml"
    return send_file(out_path, as_attachment=True, download_name=out_name, mimetype=mimetype)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    # Par défaut, l'app n'est pas exposée sur le réseau (usage local uniquement)
    host = os.environ.get("BIND", "127.0.0.1")
    app.run(debug=True, host=host, port=port)
