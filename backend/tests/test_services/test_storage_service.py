from io import BytesIO

import pytest

from app.core.exceptions import ExternalServiceError
from app.services.storage_service import StorageService


class _FakeBucket:
    def __init__(self):
        self.uploaded = []
        self.removed = []
        self.fail_upload = False
        self.fail_download = False
        self.fail_signed = False
        self.fail_list = False
        self.download_payload = b"%PDF-fake"
        self.signed_payload = {"signedURL": "/object/sign/documents/path.pdf"}
        self.list_payload = [{"name": "doc.pdf"}]

    def upload(self, path, file, file_options):
        if self.fail_upload:
            raise RuntimeError("upload failed")
        self.uploaded.append((path, file, file_options))

    def get_public_url(self, file_path):
        return f"https://storage.local/{file_path}"

    def download(self, file_path):
        if self.fail_download:
            raise RuntimeError("download failed")
        return self.download_payload

    def remove(self, paths):
        self.removed.append(paths)

    def create_signed_url(self, file_path, expires_in):
        if self.fail_signed:
            raise RuntimeError("signed failed")
        return self.signed_payload

    def list(self, path=""):
        if self.fail_list:
            raise RuntimeError("list failed")
        return [{"path": path, **item} for item in self.list_payload]


class _FakeStorage:
    def __init__(self):
        self.bucket = _FakeBucket()
        self.buckets = [{"id": "documents"}]
        self.fail_bucket_listing = False
        self.fail_bucket_create = False
        self.created_bucket = None

    def from_(self, _bucket_name):
        return self.bucket

    def list_buckets(self):
        if self.fail_bucket_listing:
            raise RuntimeError("list buckets failed")
        return self.buckets

    def create_bucket(self, id=None, options=None, **kwargs):
        if self.fail_bucket_create:
            raise RuntimeError("create bucket failed")
        self.created_bucket = (id, options)


class _FakeClient:
    def __init__(self):
        self.storage = _FakeStorage()


@pytest.fixture
def service(monkeypatch):
    fake_client = _FakeClient()
    monkeypatch.setattr("app.services.storage_service.create_client", lambda *_args, **_kwargs: fake_client)
    return StorageService()


@pytest.mark.asyncio
async def test_upload_and_download_roundtrip(service):
    upload_url = await service.upload_file("quitus/test.pdf", b"file-bytes", "application/pdf")
    assert upload_url == "https://storage.local/quitus/test.pdf"

    payload = await service.download_file("quitus/test.pdf")
    assert payload == b"%PDF-fake"


@pytest.mark.asyncio
async def test_upload_pdf_reads_buffer(service):
    buffer = BytesIO(b"buffer-pdf")
    url = await service.upload_pdf("quitus/buffer.pdf", buffer)
    assert url == "https://storage.local/quitus/buffer.pdf"


@pytest.mark.asyncio
async def test_get_file_url(service):
    url = await service.get_file_url("quitus/simple.pdf")
    assert url == "https://storage.local/quitus/simple.pdf"


@pytest.mark.asyncio
async def test_delete_file_success(service):
    deleted = await service.delete_file("quitus/remove.pdf")
    assert deleted is True


@pytest.mark.asyncio
async def test_create_signed_url_dict_relative(service):
    url = await service.create_signed_url("quitus/path.pdf", expires_in=300)
    assert url.endswith("/storage/v1/object/sign/documents/path.pdf")


@pytest.mark.asyncio
async def test_create_signed_url_string_relative(service):
    service.client.storage.bucket.signed_payload = "/object/sign/documents/path.pdf"
    url = await service.create_signed_url("quitus/path.pdf", expires_in=300)
    assert url.endswith("/storage/v1/object/sign/documents/path.pdf")


@pytest.mark.asyncio
async def test_create_signed_url_absolute(service):
    service.client.storage.bucket.signed_payload = "https://cdn.example.com/signed/path.pdf"
    url = await service.create_signed_url("quitus/path.pdf", expires_in=300)
    assert url == "https://cdn.example.com/signed/path.pdf"


@pytest.mark.asyncio
async def test_create_signed_url_empty_payload_raises(service):
    service.client.storage.bucket.signed_payload = {}
    with pytest.raises(ExternalServiceError):
        await service.create_signed_url("quitus/path.pdf", expires_in=300)


@pytest.mark.asyncio
async def test_create_bucket_if_not_exists_existing(service):
    assert await service.create_bucket_if_not_exists() is True


@pytest.mark.asyncio
async def test_create_bucket_if_not_exists_creation(service):
    service.client.storage.buckets = []
    assert await service.create_bucket_if_not_exists() is True
    assert service.client.storage.created_bucket == ("documents", {"public": False})


@pytest.mark.asyncio
async def test_list_files_success(service):
    files = await service.list_files("quitus/user-1")
    assert files == [{"path": "quitus/user-1", "name": "doc.pdf"}]


@pytest.mark.asyncio
async def test_signed_url_errors_are_wrapped(service):
    service.client.storage.bucket.fail_signed = True
    with pytest.raises(ExternalServiceError):
        await service.create_signed_url("quitus/path.pdf")


@pytest.mark.asyncio
async def test_bucket_listing_error_is_wrapped(service):
    service.client.storage.fail_bucket_listing = True
    with pytest.raises(ExternalServiceError):
        await service.create_bucket_if_not_exists()


@pytest.mark.asyncio
async def test_bucket_creation_error_is_wrapped(service):
    service.client.storage.buckets = []
    service.client.storage.fail_bucket_create = True
    with pytest.raises(ExternalServiceError):
        await service.create_bucket_if_not_exists()
