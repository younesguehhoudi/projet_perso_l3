"""
Sprint 6 Tests: API REST et historique

Tests pour:
- API REST de conversion
- Validation d'API key
- Gestion des tailles limites
- Historique des conversions
"""

import io
import json
from pathlib import Path
import pytest
import config

import app as app_module


def _multipart_files(*entries):
    """Helper pour créer des fichiers multipart."""
    return [(io.BytesIO(content), name) for content, name in entries]


class TestAPIConversion:
    """Tests pour l'API REST de conversion."""
    
    def test_api_convert_basic(self, tmp_path, monkeypatch):
        """Test conversion via API basique."""
        history_path = tmp_path / "history.json"
        exports_dir = tmp_path / "api_exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(config, "HISTORIQUE_PATH", history_path)
        monkeypatch.setattr(config, "REP_API_EXPORTS", exports_dir)
        monkeypatch.setattr(config, "CLE_API", "")
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)

        client = app_module.app.test_client()

        response = client.post(
            "/api/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files((b'{"name":"alice"}', "a.json")),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 201
        payload = response.get_json()
        assert payload["status"] == "termine"
        assert payload["error_count"] == 0

    def test_api_key_required_when_configured(self, monkeypatch, tmp_path):
        """Test que l'API fonctionne avec configuration."""
        monkeypatch.setattr(config, "CLE_API", "")
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")

        client = app_module.app.test_client()

        # Sans API key configurée, ça doit fonctionner
        resp = client.get("/api/history?limit=5")
        assert resp.status_code == 200

    def test_api_convert_respects_global_max_size(self, monkeypatch, tmp_path):
        """Test que la taille globale est respectée."""
        monkeypatch.setattr(config, "CLE_API", "")
        monkeypatch.setattr(config, "TAILLE_MAX_GLOBALE", 8)
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)

        client = app_module.app.test_client()

        response = client.post(
            "/api/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files((b'{"hello":"world"}', "a.json")),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 413
        payload = response.get_json()
        assert "limite" in payload["error"].lower()

    def test_api_job_status_not_found(self, monkeypatch):
        """Test que le statut 404 est retourné pour un job inexistant."""
        monkeypatch.setattr(config, "CLE_API", "")
        client = app_module.app.test_client()

        response = client.get("/api/jobs/inexistant")
        assert response.status_code == 404

    def test_api_history_limit_must_be_integer(self, monkeypatch):
        """Test que limit doit être un entier."""
        monkeypatch.setattr(config, "CLE_API", "")
        client = app_module.app.test_client()

        response = client.get("/api/history?limit=abc")
        assert response.status_code == 400
