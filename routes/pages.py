"""Routes pour les pages HTML."""

from flask import Blueprint, render_template, redirect, url_for

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    """Rediriger vers la page data."""
    return redirect(url_for("pages.page_data"))


@pages_bp.route("/data")
def page_data():
    """Page de conversion de données."""
    return render_template("data.html", active_page="data")


@pages_bp.route("/images")
def page_images():
    """Page de conversion d'images."""
    return render_template("images.html", active_page="images")


@pages_bp.route("/audio")
def page_audio():
    """Page de conversion audio."""
    return render_template("audio.html", active_page="audio")


@pages_bp.route("/documents")
def page_documents():
    """Page de conversion de documents."""
    return render_template("documents.html", active_page="documents")


@pages_bp.route("/monitoring")
def page_monitoring():
    """Page de suivi des jobs."""
    return render_template("monitoring.html", active_page="monitoring")


@pages_bp.route("/history")
def page_history():
    """Page d'historique."""
    return render_template("history.html", active_page="history")
