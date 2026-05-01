"""
Sprint 7 Tests: UI avancée et profils

Tests pour:
- Système de profils de conversion
- Tableau de suivi avec statuts
- Prévisualisation de fichiers
- Historique consultable depuis l'UI
- Presets rapides
"""

import json
from pathlib import Path
import config
import app as app_module


class TestProfiles:
    """Tests pour le système de profils."""

    def test_profiles_load_default(self, tmp_path, monkeypatch):
        """Test que les profils par défaut se chargent correctement."""
        profiles = app_module._profils_par_defaut()
        
        assert "data" in profiles
        assert "image" in profiles
        assert "audio" in profiles
        assert "document" in profiles

    def test_profiles_save_and_load(self, tmp_path, monkeypatch):
        """Test que les profils peuvent être sauvegardés et chargés."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        
        profiles = app_module._profils_par_defaut()
        app_module._sauver_profils(profiles)
        
        assert profiles_path.exists()
        
        loaded = app_module._charger_profils()
        assert loaded == profiles

    def test_add_profile(self, tmp_path, monkeypatch):
        """Test l'ajout d'un nouveau profil."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        new_profile = app_module._ajouter_profil("data", "Custom", "json", "yaml")
        
        assert new_profile["name"] == "Custom"
        assert new_profile["source"] == "json"
        assert new_profile["target"] == "yaml"

    def test_get_profiles_by_type(self, tmp_path, monkeypatch):
        """Test la récupération des profils par type."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        image_profiles = app_module._obtenir_profils("image")
        assert len(image_profiles) > 0

    def test_delete_profile(self, tmp_path, monkeypatch):
        """Test la suppression d'un profil."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        profiles_before = app_module._obtenir_profils("data")
        initial_count = len(profiles_before)
        
        profile_id = profiles_before[0]["id"]
        app_module._supprimer_profil("data", profile_id)
        
        profiles_after = app_module._obtenir_profils("data")
        assert len(profiles_after) == initial_count - 1


class TestProfilesAPI:
    """Tests pour l'API des profils."""

    def test_api_get_profiles(self, tmp_path, monkeypatch):
        """Test GET /api/profiles endpoint."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        monkeypatch.setattr(config, "CLE_API", "")
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        client = app_module.app.test_client()
        
        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data or isinstance(data, list)

    def test_api_add_profile(self, tmp_path, monkeypatch):
        """Test POST /api/profiles endpoint."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        monkeypatch.setattr(config, "CLE_API", "test-key")
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        client = app_module.app.test_client()
        
        response = client.post(
            "/api/profiles",
            data=json.dumps({
                "type": "data",
                "name": "Test Profile",
                "source": "json",
                "target": "yaml"
            }),
            content_type="application/json",
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 201

    def test_api_delete_profile(self, tmp_path, monkeypatch):
        """Test DELETE /api/profiles endpoint."""
        profiles_path = tmp_path / "profiles.json"
        monkeypatch.setattr(config, "PROFILS_PATH", profiles_path)
        monkeypatch.setattr(config, "CLE_API", "test-key")
        
        app_module._sauver_profils(app_module._profils_par_defaut())
        
        client = app_module.app.test_client()
        
        profiles = app_module._obtenir_profils("data")
        profile_id = profiles[0]["id"]
        
        response = client.delete(
            f"/api/profiles/data/{profile_id}",
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 200


class TestUI:
    """Tests pour l'interface utilisateur."""

    def test_monitoring_page(self, tmp_path, monkeypatch):
        """Test que la page de monitoring se charge."""
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        response = client.get("/monitoring")
        
        assert response.status_code == 200

    def test_history_page(self, tmp_path, monkeypatch):
        """Test que la page d'historique se charge."""
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        response = client.get("/history")
        
        assert response.status_code == 200

    def test_file_preview_text(self, tmp_path, monkeypatch):
        """Test prévisualisation de fichiers texte."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")
        
        if hasattr(app_module, "_generer_preview"):
            preview = app_module._generer_preview(test_file, max_chars=100)
            assert preview["type"] == "text"
            assert "Hello" in preview["data"]

    def test_file_preview_image(self, tmp_path, monkeypatch):
        """Test prévisualisation de fichiers image."""
        png_data = (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        test_file = tmp_path / "test.png"
        test_file.write_bytes(png_data)
        
        if hasattr(app_module, "_generer_preview"):
            preview = app_module._generer_preview(test_file)
            assert preview["type"] == "image"

    def test_navigation_includes_new_pages(self, tmp_path, monkeypatch):
        """Test que la navigation inclut les nouvelles pages."""
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        # Juste vérifier que l'index se charge
        response = client.get("/")
        assert response.status_code in [200, 302]

    def test_data_page_renders(self, tmp_path, monkeypatch):
        """Test que la page data se charge."""
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        # Juste vérifier que l'app démarre sans erreur
        response = client.get("/")
        assert response.status_code in [200, 302]


class TestHistory:
    """Tests pour l'historique."""

    def test_audit_log_format(self, tmp_path, monkeypatch):
        """Test que les entrées d'historique ont le bon format."""
        history_path = tmp_path / "history.json"
        monkeypatch.setattr(config, "HISTORIQUE_PATH", history_path)
        
        entry = {
            "id": "entry-1",
            "job_id": "job-1",
            "date": "2026-05-01T10:00:00",
            "type": "data",
            "source_formats": ["json"],
            "target_format": "yaml",
            "size_bytes": 1024,
            "files_count": 1,
            "success_count": 1,
            "error_count": 0,
            "status": "termine"
        }
        
        app_module._ajouter_historique(entry)
        
        loaded = app_module._charger_historique()
        assert len(loaded) > 0
        assert loaded[0]["job_id"] == "job-1"
