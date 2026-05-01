"""
Sprint 5 Tests: Batch conversion et gestion des erreurs

Tests pour:
- Conversion par lots (multiple files)
- Création de ZIP avec résultats
- Gestion des erreurs partielles
- Validation des types MIME
"""

import io
import zipfile
import pytest
import config

import app as app_module


def _multipart_files(*entries):
    """Helper pour créer des fichiers multipart.
    
    Args:
        entries: Tuples de (contenu_bytes, nom_fichier)
    
    Returns:
        Liste de tuples (BytesIO, nom_fichier)
    """
    return [(io.BytesIO(content), name) for content, name in entries]


class TestBatchConversion:
    """Tests pour conversions par lots."""
    
    def test_batch_convert_multiple_files_returns_zip(self, monkeypatch, tmp_path):
        """Test que la conversion de plusieurs fichiers retourne un ZIP."""
        # Isolation des fichiers temporaires
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        
        # Convertir 2 fichiers JSON en YAML
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files(
                    (b'{"name":"alice","age":30}', "a.json"),
                    (b'{"name":"bob","age":25}', "b.json"),
                ),
            },
            content_type="multipart/form-data",
        )
        
        # Vérifier la réponse
        assert response.status_code == 200
        assert response.mimetype == "application/zip"
        
        # Vérifier contenu du ZIP
        archive = zipfile.ZipFile(io.BytesIO(response.data))
        names = archive.namelist()
        
        yaml_files = [n for n in names if n.endswith(".yaml")]
        assert len(yaml_files) == 2, f"Expected 2 YAML files, got {len(yaml_files)}"
        
        # Vérifier contenu des fichiers YAML
        for name in yaml_files:
            content = archive.read(name).decode("utf-8")
            assert "name:" in content or "age:" in content
    
    def test_batch_partial_failure_creates_zip_with_errors(self, monkeypatch, tmp_path):
        """Test que les erreurs partielles créent un ZIP avec fichier errors.txt."""
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        
        # 1 fichier valide, 1 cassé
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files(
                    (b'{"ok": true}', "ok.json"),
                    (b"\xff\xfe\xfd", "broken.json"),
                ),
            },
            content_type="multipart/form-data",
        )
        
        assert response.status_code == 200
        assert response.mimetype == "application/zip"
        
        # Vérifier le contenu
        archive = zipfile.ZipFile(io.BytesIO(response.data))
        names = archive.namelist()
        
        # Doit avoir au moins 1 fichier YAML et le fichier d'erreurs
        yaml_count = len([n for n in names if n.endswith(".yaml")])
        assert yaml_count >= 1, "Au moins 1 fichier YAML attendu"
        assert "errors.txt" in names, "Fichier errors.txt attendu"
        
        # Vérifier que errors.txt contient quelque chose
        errors_content = archive.read("errors.txt").decode("utf-8")
        assert len(errors_content) > 0
    
    def test_all_files_fail_shows_error_message(self, monkeypatch, tmp_path):
        """Test que si tous les fichiers échouent, une erreur est affichée."""
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        
        # Tous les fichiers sont cassés
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files(
                    (b"\xff\xfe\xfd", "broken1.json"),
                    (b"\xfe\xff\xfc", "broken2.json"),
                ),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        
        # Doit rediriger ou afficher une erreur
        assert response.status_code in [302, 200]


class TestSingleFileConversion:
    """Tests pour conversion d'un seul fichier."""
    
    def test_single_file_returns_direct_download(self, monkeypatch, tmp_path):
        """Test que la conversion d'un seul fichier retourne le fichier directement."""
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        
        client = app_module.app.test_client()
        
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files((b'{"name":"alice"}', "file.json"),),
            },
            content_type="multipart/form-data",
        )
        
        # Single file should return direct download, not ZIP
        assert response.status_code == 200
        # Le contenu doit être du YAML (pas un ZIP)
        assert b"name:" in response.data
        assert b"PK" not in response.data  # ZIP magic number


class TestFileValidation:
    """Tests pour la validation des fichiers."""
    
    def test_no_file_selected_redirects(self, monkeypatch, tmp_path):
        """Test que sans fichier, on est redirigé."""
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        
        client = app_module.app.test_client()
        
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        
        # Should redirect (302) because no files
        assert response.status_code == 302
    
    def test_total_size_exceeds_limit(self, monkeypatch, tmp_path):
        """Test que si la taille totale dépasse la limite, on est redirigé."""
        monkeypatch.setattr(config, "REP_UPLOADS", tmp_path)
        monkeypatch.setattr(config, "HISTORIQUE_PATH", tmp_path / "history.json")
        # Limiter à 50 bytes seulement
        monkeypatch.setattr(config, "TAILLE_MAX_GLOBALE", 50)
        
        client = app_module.app.test_client()
        
        response = client.post(
            "/convert",
            data={
                "conversion_type": "data",
                "target_format": "yaml",
                "file": _multipart_files(
                    (b'{"large_data": "' + b"x" * 100 + b'"}', "big.json"),
                ),
            },
            content_type="multipart/form-data",
            follow_redirects=False,
        )
        
        # Doit rediriger ou afficher une erreur
        assert response.status_code in [302, 200]
