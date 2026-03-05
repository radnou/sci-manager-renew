from app.api.v1 import files


def test_upload_quitus_success(client, auth_headers, monkeypatch):
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "quitus/user-123/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["url"] == "https://storage.local/quitus/user-123/sample.pdf"


def test_upload_quitus_failure(client, auth_headers, monkeypatch):
    async def fake_get_file_url(_file_path: str):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.post(
        "/api/v1/files/upload-quitus",
        params={"file_path": "quitus/user-123/sample.pdf"},
        headers=auth_headers,
    )
    assert response.status_code == 500
    assert "Failed to upload quitus" in response.json()["detail"]


def test_download_file_success(client, auth_headers, monkeypatch):
    async def fake_get_file_url(file_path: str):
        return f"https://storage.local/{file_path}"

    monkeypatch.setattr(files.storage_service, "get_file_url", fake_get_file_url)

    response = client.get(
        "/api/v1/files/download/quitus/user-123/sample.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["url"] == "https://storage.local/quitus/user-123/sample.pdf"


def test_delete_file_success(client, auth_headers, monkeypatch):
    async def fake_delete_file(_file_path: str):
        return True

    monkeypatch.setattr(files.storage_service, "delete_file", fake_delete_file)

    response = client.delete(
        "/api/v1/files/delete/quitus/user-123/sample.pdf",
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
        "/api/v1/files/delete/quitus/user-123/sample.pdf",
        headers=auth_headers,
    )
    assert response.status_code == 500
    assert "Failed to delete file" in response.json()["detail"]


def test_list_files_success(client, auth_headers, monkeypatch):
    async def fake_list_files(folder: str):
        return [{"name": "sample.pdf", "folder": folder}]

    monkeypatch.setattr(files.storage_service, "list_files", fake_list_files)

    response = client.get("/api/v1/files/list/quitus/user-123", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["files"] == [{"name": "sample.pdf", "folder": "quitus/user-123"}]


def test_list_files_failure(client, auth_headers, monkeypatch):
    async def fake_list_files(_folder: str):
        raise RuntimeError("listing failed")

    monkeypatch.setattr(files.storage_service, "list_files", fake_list_files)

    response = client.get("/api/v1/files/list/quitus/user-123", headers=auth_headers)
    assert response.status_code == 500
    assert "Failed to list files" in response.json()["detail"]
