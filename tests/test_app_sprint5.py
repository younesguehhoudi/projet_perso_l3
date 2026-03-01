import io
import zipfile

import app as app_module



def _multipart_files(*entries):
    return [(io.BytesIO(content), name) for content, name in entries]


def test_batch_convert_returns_zip_and_updates_jobs():
    app_module.JOBS.clear()
    app_module.JOB_ORDER.clear()

    client = app_module.app.test_client()

    response = client.post(
        "/convert",
        data={
            "conversion_type": "data",
            "target_format": "yaml",
            "file": _multipart_files(
                (b'{"name":"alice"}', "a.json"),
                (b'{"name":"bob"}', "b.json"),
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert response.mimetype == "application/zip"

    archive = zipfile.ZipFile(io.BytesIO(response.data))
    names = archive.namelist()
    assert any(name.endswith(".yaml") for name in names)
    assert len([name for name in names if name.endswith(".yaml")]) == 2

    jobs_response = client.get("/jobs")
    assert jobs_response.status_code == 200
    jobs = jobs_response.get_json()
    assert jobs[0]["status"] == "termine"
    assert jobs[0]["files_count"] == 2
    assert jobs[0]["success_count"] == 2
    assert jobs[0]["error_count"] == 0


def test_batch_partial_failure_keeps_zip_with_errors_file():
    app_module.JOBS.clear()
    app_module.JOB_ORDER.clear()

    client = app_module.app.test_client()

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

    archive = zipfile.ZipFile(io.BytesIO(response.data))
    names = archive.namelist()
    assert any(name.endswith(".yaml") for name in names)
    assert "errors.txt" in names

    jobs = client.get("/jobs").get_json()
    assert jobs[0]["status"] == "erreur"
    assert jobs[0]["success_count"] == 1
    assert jobs[0]["error_count"] == 1


def test_document_mime_mismatch_redirects_with_error():
    app_module.JOBS.clear()
    app_module.JOB_ORDER.clear()

    client = app_module.app.test_client()

    response = client.post(
        "/convert",
        data={
            "conversion_type": "document",
            "target_format": "txt",
            "file": [(io.BytesIO(b"%PDF-1.4\n"), "doc.pdf", "image/png")],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )

    assert response.status_code == 302

    jobs = client.get("/jobs").get_json()
    assert jobs[0]["status"] == "erreur"
    assert jobs[0]["error_count"] == 1
