from app.api.v1 import files


# ── Existing functionality tests (updated paths to include SCI ownership) ──


def test_upload_quitus_success(client, auth_headers, monkeypatch):
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "sci-sci-1/quitus/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["url"] == "https://storage.local/sci-sci-1/quitus/sample.pdf"


def test_upload_quitus_failure(client, auth_headers, monkeypatch):
    async def fake_get_file_url(_file_path: str):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "sci-sci-1/quitus/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "external_service_error"
    assert "Failed to upload quitus" in payload["error"]


def test_download_file_success(client, auth_headers, monkeypatch):
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.get(
        "/api/v1/files/download/sci-sci-1/bien-1/sample.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["url"] == "https://storage.local/sci-sci-1/bien-1/sample.pdf"


def test_delete_file_success(client, auth_headers, monkeypatch):
    async def fake_delete_file(_file_path: str):
        return True

    monkeypatch.setattr(files.storage_service, "delete_file", fake_delete_file)

    response = client.delete(
        "/api/v1/files/delete/sci-sci-1/bien-1/sample.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"success": True, "message": "File deleted successfully"}


def test_delete_file_failure(client, auth_headers, monkeypatch):
    async def fake_delete_file(_file_path: str):
        return False

    monkeypatch.setattr(files.storage_service, "delete_file", fake_delete_file)

    response = client.delete(
        "/api/v1/files/delete/sci-sci-1/bien-1/sample.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "external_service_error"
    assert "Failed to delete file" in payload["error"]


def test_list_files_success(client, auth_headers, monkeypatch):
    async def fake_list_files(folder: str):
        return [{"name": "sample.pdf", "folder": folder}]

    monkeypatch.setattr(files.storage_service, "list_files", fake_list_files)

    response = client.get("/api/v1/files/list/sci-sci-1/bien-1", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["files"] == [{"name": "sample.pdf", "folder": "sci-sci-1/bien-1"}]


def test_list_files_failure(client, auth_headers, monkeypatch):
    async def fake_list_files(_folder: str):
        raise RuntimeError("listing failed")

    monkeypatch.setattr(files.storage_service, "list_files", fake_list_files)

    response = client.get("/api/v1/files/list/sci-sci-1/bien-1", headers=auth_headers)
    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "external_service_error"
    assert "Failed to list files" in payload["error"]


def test_upload_quitus_invalid_path(client, auth_headers):
    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "../secret.txt"},
        headers=auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "Chemin de fichier invalide."


# ── File ownership verification tests (S-2 security fix) ──


def test_download_file_requires_auth(client):
    """Unauthenticated request should be rejected."""
    response = client.get("/api/v1/files/download/sci-sci-1/doc.pdf")
    assert response.status_code == 401


def test_download_file_forbidden_wrong_user(client, auth_headers, fake_supabase):
    """User who is not an associe of the SCI should get 403."""
    response = client.get(
        "/api/v1/files/download/sci-unknown-id/doc.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_download_file_allowed_for_associe(client, auth_headers, fake_supabase, monkeypatch):
    """User who is an associe of the SCI should get access (not 403)."""
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.get(
        "/api/v1/files/download/sci-sci-1/bien-1/doc.pdf",
        headers=auth_headers,
    )
    assert response.status_code != 403
    assert response.status_code == 200


def test_delete_file_forbidden_wrong_user(client, auth_headers, fake_supabase):
    """Delete should be denied for non-associe user."""
    response = client.delete(
        "/api/v1/files/delete/sci-unknown-id/doc.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_list_files_forbidden_wrong_user(client, auth_headers, fake_supabase):
    """List should be denied for non-associe user."""
    response = client.get(
        "/api/v1/files/list/sci-unknown-id",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_upload_quitus_forbidden_wrong_user(client, auth_headers, fake_supabase):
    """Upload should be denied for non-associe user."""
    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "sci-unknown-id/quitus/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_download_non_sci_path_forbidden(client, auth_headers, fake_supabase):
    """Paths not matching sci-{uuid}/ pattern should be denied."""
    response = client.get(
        "/api/v1/files/download/random-folder/doc.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_upload_non_sci_path_forbidden(client, auth_headers, fake_supabase):
    """Upload with non-SCI path should be denied."""
    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "random-folder/quitus/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_access_second_sci_allowed(client, auth_headers, fake_supabase, monkeypatch):
    """user-123 is also associe of sci-2, should have access."""
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.get(
        "/api/v1/files/download/sci-sci-2/doc.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 200
