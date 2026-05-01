"""Routes du projet."""

from routes.pages import pages_bp
from routes.api import api_bp
from routes.conversion import convert_bp

__all__ = ["pages_bp", "api_bp", "convert_bp"]
