"""Helpers for GererSCI document storage links."""

from __future__ import annotations

from urllib.parse import urlsplit

from app.core.config import settings
from app.core.exceptions import DatabaseError

_DOCUMENTS_URL_PREFIXES = (
    "/storage/v1/object/public/documents/",
    "/storage/v1/object/sign/documents/",
    "/object/public/documents/",
    "/object/sign/documents/",
)


def extract_document_storage_path(url: str | None) -> str | None:
    """Extract a documents bucket path from a public/signed URL or raw path."""
    if not url:
        return None

    if url.startswith("sci-"):
        return url

    parsed = urlsplit(url)
    candidate = parsed.path or url
    for prefix in _DOCUMENTS_URL_PREFIXES:
        idx = candidate.find(prefix)
        if idx != -1:
            path = candidate[idx + len(prefix):].lstrip("/")
            return path or None

    return None


def _normalize_storage_url(url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("/storage/v1"):
        return f"{settings.supabase_url.rstrip('/')}{url}"
    if url.startswith("/"):
        return f"{settings.supabase_url.rstrip('/')}/storage/v1{url}"
    return f"{settings.supabase_url.rstrip('/')}/storage/v1/{url.lstrip('/')}"


def create_document_signed_url(
    storage_bucket,
    current_url_or_path: str,
    expires_in: int = 86400,
) -> str:
    """Return a fresh signed URL when the path belongs to the internal documents bucket."""
    storage_path = extract_document_storage_path(current_url_or_path)
    if not storage_path:
        return current_url_or_path

    payload = storage_bucket.create_signed_url(storage_path, expires_in)
    if isinstance(payload, dict):
        signed_url = (
            payload.get("signedURL")
            or payload.get("signedUrl")
            or payload.get("signed_url")
        )
    else:
        signed_url = payload

    if not signed_url:
        raise DatabaseError("Failed to generate signed URL for document")

    return _normalize_storage_url(signed_url)
