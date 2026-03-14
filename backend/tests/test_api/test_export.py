"""Tests for export API endpoints — CSV export for loyers and biens."""

from __future__ import annotations


def test_export_loyers_csv_requires_auth(client):
    """Request without auth returns 401."""
    response = client.get("/api/v1/export/loyers/csv")
    assert response.status_code in (401, 403)


def test_export_biens_csv_requires_auth(client):
    """Request without auth returns 401."""
    response = client.get("/api/v1/export/biens/csv")
    assert response.status_code in (401, 403)


def test_export_loyers_csv_returns_csv(client, auth_headers, fake_supabase):
    """Export loyers returns a valid CSV response with data."""
    fake_supabase.store["loyers"] = [
        {
            "id": "loyer-1",
            "id_sci": "sci-1",
            "id_bien": "bien-1",
            "date_loyer": "2026-03-01",
            "montant": 1200,
            "statut": "paye",
        },
    ]

    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "1200" in resp.text


def test_export_loyers_csv_empty(client, auth_headers, fake_supabase):
    """Export loyers for user with no SCIs returns header-only CSV."""
    fake_supabase.store["associes"] = []

    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "date_loyer" in resp.text


def test_export_biens_csv_returns_csv(client, auth_headers, fake_supabase):
    """Export biens returns a valid CSV response with data."""
    fake_supabase.store["biens"] = [
        {
            "id": "bien-1",
            "id_sci": "sci-1",
            "adresse": "1 rue Seed",
            "ville": "Lyon",
            "code_postal": "69001",
            "type_locatif": "appartement",
            "loyer_cc": 900,
            "charges": 100,
            "surface_m2": 45,
            "nb_pieces": 2,
            "dpe_classe": "C",
        },
    ]

    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
    assert "1 rue Seed" in resp.text
    assert "Lyon" in resp.text


def test_get_user_sci_ids_returns_ids(fake_supabase):
    """Unit test _get_user_sci_ids helper directly."""
    from app.api.v1.export import _get_user_sci_ids

    sci_ids = _get_user_sci_ids(fake_supabase, "user-123")
    assert "sci-1" in sci_ids
    assert "sci-2" in sci_ids


def test_get_user_sci_ids_empty_for_unknown_user(fake_supabase):
    """Unknown user returns empty list."""
    from app.api.v1.export import _get_user_sci_ids

    sci_ids = _get_user_sci_ids(fake_supabase, "unknown-user")
    assert sci_ids == []


def test_get_user_sci_ids_filters_none_values(fake_supabase):
    """Rows with no id_sci are filtered out."""
    from app.api.v1.export import _get_user_sci_ids

    fake_supabase.store["associes"].append(
        {"id": "a-x", "id_sci": None, "user_id": "user-123", "role": "associe"}
    )
    sci_ids = _get_user_sci_ids(fake_supabase, "user-123")
    assert None not in sci_ids
    assert "sci-1" in sci_ids
    assert "sci-2" in sci_ids


# ── _period_to_date unit tests ──────────────────────────────────────────


def test_period_to_date_none():
    """None input returns None."""
    from app.api.v1.export import _period_to_date

    assert _period_to_date(None) is None


def test_period_to_date_empty_string():
    """Empty string returns None."""
    from app.api.v1.export import _period_to_date

    assert _period_to_date("") is None


def test_period_to_date_6m():
    """'6m' returns a date roughly 6 months ago."""
    from datetime import datetime, timedelta
    from app.api.v1.export import _period_to_date

    result = _period_to_date("6m")
    assert result is not None
    expected = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
    assert result == expected


def test_period_to_date_12m():
    """'12m' returns a date roughly 12 months ago."""
    from datetime import datetime, timedelta
    from app.api.v1.export import _period_to_date

    result = _period_to_date("12m")
    assert result is not None
    expected = (datetime.now() - timedelta(days=360)).strftime("%Y-%m-%d")
    assert result == expected


def test_period_to_date_24m():
    """'24m' returns a date roughly 24 months ago."""
    from datetime import datetime, timedelta
    from app.api.v1.export import _period_to_date

    result = _period_to_date("24m")
    assert result is not None
    expected = (datetime.now() - timedelta(days=720)).strftime("%Y-%m-%d")
    assert result == expected


def test_period_to_date_invalid():
    """Invalid period string returns None."""
    from app.api.v1.export import _period_to_date

    assert _period_to_date("3m") is None
    assert _period_to_date("abc") is None
    assert _period_to_date("1y") is None


# ── Loyers CSV content validation ────────────────────────────────────────


def _parse_csv(text: str) -> list[list[str]]:
    """Parse CSV text into a list of rows (each a list of fields)."""
    import csv as _csv
    import io as _io
    reader = _csv.reader(_io.StringIO(text))
    return list(reader)


def test_export_loyers_csv_header_columns(client, auth_headers, fake_supabase):
    """Loyers CSV contains the expected header columns."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 500, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert rows[0] == ["date_loyer", "montant", "statut", "id_bien", "id_sci"]


def test_export_loyers_csv_data_rows(client, auth_headers, fake_supabase):
    """Loyers CSV data rows contain correct field values in order."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-02-01", "montant": 1500, "statut": "impaye"},
        {"id": "l2", "id_sci": "sci-2", "id_bien": "bien-9",
         "date_loyer": "2026-03-01", "montant": 980, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    # header + 2 data rows
    assert len(rows) == 3
    # Check each data row has the right fields (order: date_loyer, montant, statut, id_bien, id_sci)
    data_values = {(r[0], r[2], r[3], r[4]) for r in rows[1:]}
    assert ("2026-02-01", "impaye", "bien-1", "sci-1") in data_values
    assert ("2026-03-01", "paye", "bien-9", "sci-2") in data_values


def test_export_loyers_csv_content_disposition(client, auth_headers, fake_supabase):
    """Loyers CSV response has Content-Disposition with filename."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 100, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "loyers_" in cd
    assert ".csv" in cd


def test_export_loyers_csv_empty_content_disposition(client, auth_headers, fake_supabase):
    """Loyers CSV for user with no SCIs has static filename."""
    fake_supabase.store["associes"] = []
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    cd = resp.headers.get("content-disposition", "")
    assert "loyers_export.csv" in cd


# ── Period filtering tests ───────────────────────────────────────────────


def test_export_loyers_csv_period_6m_filters(client, auth_headers, fake_supabase):
    """Period=6m filters out loyers older than ~6 months."""
    from datetime import datetime, timedelta

    recent_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    old_date = (datetime.now() - timedelta(days=250)).strftime("%Y-%m-%d")

    fake_supabase.store["loyers"] = [
        {"id": "l-recent", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": recent_date, "montant": 1000, "statut": "paye"},
        {"id": "l-old", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": old_date, "montant": 900, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?period=6m", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    # header + only the recent loyer (old one is >6m ago)
    assert len(rows) == 2
    assert rows[1][0] == recent_date
    assert rows[1][1] == "1000"


def test_export_loyers_csv_period_12m_filters(client, auth_headers, fake_supabase):
    """Period=12m includes loyers within 12 months, excludes older."""
    from datetime import datetime, timedelta

    within_date = (datetime.now() - timedelta(days=300)).strftime("%Y-%m-%d")
    outside_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")

    fake_supabase.store["loyers"] = [
        {"id": "l-in", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": within_date, "montant": 1100, "statut": "paye"},
        {"id": "l-out", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": outside_date, "montant": 700, "statut": "impaye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?period=12m", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1][1] == "1100"


def test_export_loyers_csv_period_24m_filters(client, auth_headers, fake_supabase):
    """Period=24m includes loyers within 24 months, excludes older."""
    from datetime import datetime, timedelta

    within_date = (datetime.now() - timedelta(days=700)).strftime("%Y-%m-%d")
    outside_date = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")

    fake_supabase.store["loyers"] = [
        {"id": "l-in", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": within_date, "montant": 600, "statut": "paye"},
        {"id": "l-out", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": outside_date, "montant": 500, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?period=24m", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1][1] == "600"


def test_export_loyers_csv_invalid_period_returns_all(client, auth_headers, fake_supabase):
    """An invalid period value is ignored and all loyers are returned."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2020-01-01", "montant": 100, "statut": "paye"},
        {"id": "l2", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 200, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?period=99x", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    # header + both rows (invalid period is ignored)
    assert len(rows) == 3


def test_export_loyers_csv_no_period_returns_all(client, auth_headers, fake_supabase):
    """Without period param, all loyers are returned."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2020-01-01", "montant": 100, "statut": "paye"},
        {"id": "l2", "id_sci": "sci-2", "id_bien": "bien-9",
         "date_loyer": "2026-01-01", "montant": 200, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 3


def test_export_loyers_csv_period_empty_result(client, auth_headers, fake_supabase):
    """Period filter that excludes all loyers returns header-only CSV."""
    fake_supabase.store["loyers"] = [
        {"id": "l-old", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2020-01-01", "montant": 100, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?period=6m", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    # Only header row, no data
    assert len(rows) == 1
    assert rows[0] == ["date_loyer", "montant", "statut", "id_bien", "id_sci"]


def test_export_loyers_csv_missing_fields_default_empty(client, auth_headers, fake_supabase):
    """Loyer rows with missing fields export as empty strings."""
    fake_supabase.store["loyers"] = [
        {"id": "l-sparse", "id_sci": "sci-1"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    # All fields except id_sci should be empty
    assert rows[1] == ["", "", "", "", "sci-1"]


# ── Biens CSV content validation ─────────────────────────────────────────


def test_export_biens_csv_header_columns(client, auth_headers, fake_supabase):
    """Biens CSV contains the expected header columns."""
    fake_supabase.store["biens"] = []
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert rows[0] == [
        "adresse", "ville", "code_postal", "type_locatif",
        "loyer_cc", "charges", "surface_m2", "nb_pieces", "dpe_classe", "id_sci",
    ]


def test_export_biens_csv_data_rows_all_columns(client, auth_headers, fake_supabase):
    """Biens CSV data rows map all columns correctly."""
    fake_supabase.store["biens"] = [
        {
            "id": "b1", "id_sci": "sci-1",
            "adresse": "10 rue Test", "ville": "Marseille",
            "code_postal": "13001", "type_locatif": "studio",
            "loyer_cc": 750, "charges": 50,
            "surface_m2": 25, "nb_pieces": 1, "dpe_classe": "D",
        },
    ]
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1] == [
        "10 rue Test", "Marseille", "13001", "studio",
        "750", "50", "25", "1", "D", "sci-1",
    ]


def test_export_biens_csv_multiple_rows(client, auth_headers, fake_supabase):
    """Biens CSV exports multiple biens across different SCIs."""
    fake_supabase.store["biens"] = [
        {"id": "b1", "id_sci": "sci-1", "adresse": "A rue", "ville": "Paris",
         "code_postal": "75001", "type_locatif": "T2", "loyer_cc": 1000,
         "charges": 100, "surface_m2": 40, "nb_pieces": 2, "dpe_classe": "B"},
        {"id": "b2", "id_sci": "sci-2", "adresse": "B avenue", "ville": "Lyon",
         "code_postal": "69001", "type_locatif": "T3", "loyer_cc": 1500,
         "charges": 150, "surface_m2": 65, "nb_pieces": 3, "dpe_classe": "C"},
    ]
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 3
    addresses = {r[0] for r in rows[1:]}
    assert "A rue" in addresses
    assert "B avenue" in addresses


def test_export_biens_csv_content_disposition(client, auth_headers, fake_supabase):
    """Biens CSV response has Content-Disposition with timestamped filename."""
    fake_supabase.store["biens"] = [
        {"id": "b1", "id_sci": "sci-1", "adresse": "1 rue X", "ville": "Paris",
         "code_postal": "75001", "type_locatif": "T1", "loyer_cc": 500,
         "charges": 30, "surface_m2": 20, "nb_pieces": 1, "dpe_classe": "E"},
    ]
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "biens_" in cd
    assert ".csv" in cd


def test_export_biens_csv_empty_no_scis(client, auth_headers, fake_supabase):
    """Biens CSV for user with no SCIs returns header-only CSV with static filename."""
    fake_supabase.store["associes"] = []
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1  # header only
    cd = resp.headers.get("content-disposition", "")
    assert "biens_export.csv" in cd


def test_export_biens_csv_missing_fields_default_empty(client, auth_headers, fake_supabase):
    """Bien rows with missing fields export as empty strings."""
    fake_supabase.store["biens"] = [
        {"id": "b-sparse", "id_sci": "sci-1", "adresse": "Sparse Addr"},
    ]
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1][0] == "Sparse Addr"
    # Other columns should be empty strings
    assert rows[1][1] == ""  # ville
    assert rows[1][9] == "sci-1"  # id_sci is last


def test_export_biens_csv_no_biens_for_user(client, auth_headers, fake_supabase):
    """User with SCIs but no biens returns header-only CSV."""
    fake_supabase.store["biens"] = []
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1  # header only


def test_export_loyers_csv_no_loyers_for_user(client, auth_headers, fake_supabase):
    """User with SCIs but no loyers returns header-only CSV."""
    fake_supabase.store["loyers"] = []
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1  # header only


def test_export_loyers_csv_only_user_scis(client, auth_headers, fake_supabase):
    """Loyers export only includes loyers for the user's own SCIs."""
    fake_supabase.store["loyers"] = [
        {"id": "l-mine", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 1000, "statut": "paye"},
        {"id": "l-other", "id_sci": "sci-other", "id_bien": "bien-other",
         "date_loyer": "2026-01-01", "montant": 9999, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    # Only sci-1 loyer should appear (sci-other not in user's SCIs)
    assert len(rows) == 2
    assert rows[1][1] == "1000"
    assert "9999" not in resp.text


def test_export_biens_csv_only_user_scis(client, auth_headers, fake_supabase):
    """Biens export only includes biens for the user's own SCIs."""
    fake_supabase.store["biens"] = [
        {"id": "b-mine", "id_sci": "sci-1", "adresse": "My Addr", "ville": "Paris",
         "code_postal": "75001", "type_locatif": "T1", "loyer_cc": 800,
         "charges": 50, "surface_m2": 30, "nb_pieces": 1, "dpe_classe": "C"},
        {"id": "b-other", "id_sci": "sci-other", "adresse": "Foreign Addr", "ville": "Rome",
         "code_postal": "00100", "type_locatif": "T4", "loyer_cc": 5000,
         "charges": 200, "surface_m2": 100, "nb_pieces": 4, "dpe_classe": "A"},
    ]
    resp = client.get("/api/v1/export/biens/csv", headers=auth_headers)
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1][0] == "My Addr"
    assert "Foreign Addr" not in resp.text


# ── sci_id filter parameter tests (lines 52-55, 118-121) ─────────────────


def test_export_loyers_csv_sci_id_filter_valid(client, auth_headers, fake_supabase):
    """sci_id param narrows loyers to a single SCI the user belongs to."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 500, "statut": "paye"},
        {"id": "l2", "id_sci": "sci-2", "id_bien": "bien-9",
         "date_loyer": "2026-02-01", "montant": 800, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?sci_id=sci-1", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 2  # header + 1 row (only sci-1)
    assert rows[1][4] == "sci-1"


def test_export_loyers_csv_sci_id_filter_invalid(client, auth_headers, fake_supabase):
    """sci_id param with a SCI the user doesn't belong to returns header-only."""
    fake_supabase.store["loyers"] = [
        {"id": "l1", "id_sci": "sci-1", "id_bien": "bien-1",
         "date_loyer": "2026-01-01", "montant": 500, "statut": "paye"},
    ]
    resp = client.get("/api/v1/export/loyers/csv?sci_id=sci-unknown", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1  # header only


def test_export_biens_csv_sci_id_filter_valid(client, auth_headers, fake_supabase):
    """sci_id param narrows biens to a single SCI the user belongs to."""
    fake_supabase.store["biens"] = [
        {"id": "b1", "id_sci": "sci-1", "adresse": "Rue A", "ville": "Paris",
         "code_postal": "75001", "type_locatif": "T1", "loyer_cc": 500,
         "charges": 50, "surface_m2": 30, "nb_pieces": 1, "dpe_classe": "C"},
        {"id": "b2", "id_sci": "sci-2", "adresse": "Rue B", "ville": "Lyon",
         "code_postal": "69001", "type_locatif": "T2", "loyer_cc": 700,
         "charges": 60, "surface_m2": 40, "nb_pieces": 2, "dpe_classe": "D"},
    ]
    resp = client.get("/api/v1/export/biens/csv?sci_id=sci-1", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    assert rows[1][0] == "Rue A"


def test_export_biens_csv_sci_id_filter_invalid(client, auth_headers, fake_supabase):
    """sci_id param with a SCI the user doesn't belong to returns header-only."""
    fake_supabase.store["biens"] = [
        {"id": "b1", "id_sci": "sci-1", "adresse": "Rue A", "ville": "Paris",
         "code_postal": "75001", "type_locatif": "T1", "loyer_cc": 500,
         "charges": 50, "surface_m2": 30, "nb_pieces": 1, "dpe_classe": "C"},
    ]
    resp = client.get("/api/v1/export/biens/csv?sci_id=sci-unknown", headers=auth_headers)
    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1  # header only
