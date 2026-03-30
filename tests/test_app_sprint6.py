import io
import json
from pathlib import Path

import app as app_module


def _multipart_files(*entries):
    return [(io.BytesIO(content), name) for content, name in entries]


def test_api_convert_status_download_and_history(tmp_path, monkeypatch):
    app_module.JOBS.clear()
    app_module.JOB_ORDER.clear()

    history_path = tmp_path / "history.json"
    exports_dir = tmp_path / "api_exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(app_module, "HISTORIQUE_PATH", history_path)
    monkeypatch.setattr(app_module, "REP_API_EXPORTS", exports_dir)
    monkeypatch.setattr(app_module, "CLE_API", "")

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
    job_id = payload["job_id"]

    status_resp = client.get(f"/api/jobs/{job_id}")
    assert status_resp.status_code == 200
    status_payload = status_resp.get_json()
    assert status_payload["status"] == "termine"
    assert status_payload["success_count"] == 1

    download_resp = client.get(f"/api/jobs/{job_id}/download")
    assert download_resp.status_code == 200
    assert b"name: alice" in download_resp.data

    history_resp = client.get("/api/history?limit=5")
    assert history_resp.status_code == 200
    history = history_resp.get_json()
    assert len(history) == 1
    assert history[0]["job_id"] == job_id
    assert history[0]["target_format"] == "yaml"

    saved_history = json.loads(history_path.read_text(encoding="utf-8"))
    assert saved_history[0]["status"] == "termine"


def test_api_key_required_when_configured(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "CLE_API", "sprint6-key")
    monkeypatch.setattr(app_module, "HISTORIQUE_PATH", tmp_path / "history.json")

    client = app_module.app.test_client()

    resp_unauthorized = client.get("/api/history")
    assert resp_unauthorized.status_code == 401

    resp_authorized = client.get("/api/history", headers={"X-API-Key": "sprint6-key"})
    assert resp_authorized.status_code == 200


def test_api_convert_respects_global_max_size(monkeypatch):
    app_module.JOBS.clear()
    app_module.JOB_ORDER.clear()

    monkeypatch.setattr(app_module, "CLE_API", "")
    monkeypatch.setattr(app_module, "TAILLE_MAX_GLOBALE", 8)

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


def test_api_job_status_not_found(monkeypatch):
    monkeypatch.setattr(app_module, "CLE_API", "")
    client = app_module.app.test_client()

    response = client.get("/api/jobs/inexistant")
    assert response.status_code == 404


def test_api_history_limit_must_be_integer(monkeypatch):
    monkeypatch.setattr(app_module, "CLE_API", "")
    client = app_module.app.test_client()

    response = client.get("/api/history?limit=abc")
    assert response.status_code == 400
