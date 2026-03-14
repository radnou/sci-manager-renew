def test_get_scis_requires_auth(client):
    response = client.get("/api/v1/scis/")
    assert response.status_code == 401


def test_get_scis_returns_portfolio_overview(client, auth_headers):
    response = client.get("/api/v1/scis/", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["nom"] == "SCI Horizon Lyon"
    assert data[1]["nom"] == "SCI Mosa Belleville"
    assert data[1]["associes_count"] == 2
    assert data[1]["user_role"] == "gerant"


def test_get_sci_detail_returns_identity_card(client, auth_headers, fake_supabase):
    fake_supabase.store["biens"] = [
        {
            "id": "bien-1",
            "id_sci": "sci-1",
            "adresse": "1 rue Seed",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 1200,
            "charges": 150,
            "tmi": 30,
            "rentabilite_brute": 5.8,
            "rentabilite_nette": 4.9,
            "cashflow_annuel": 12600,
        },
        {
            "id": "bien-2",
            "id_sci": "sci-1",
            "adresse": "42 avenue QA",
            "ville": "Lyon",
            "code_postal": "69002",
            "type_locatif": "meuble",
            "loyer_cc": 1650,
            "charges": 120,
            "tmi": 28,
            "rentabilite_brute": 6.1,
            "rentabilite_nette": 5.5,
            "cashflow_annuel": 18360,
        },
    ]
    fake_supabase.store["loyers"] = [
        {
            "id": "loyer-1",
            "id_bien": "bien-1",
            "id_sci": "sci-1",
            "id_locataire": "loc-1",
            "date_loyer": "2026-03-01",
            "montant": 1200,
            "statut": "paye",
            "quitus_genere": True,
        },
        {
            "id": "loyer-2",
            "id_bien": "bien-2",
            "id_sci": "sci-1",
            "id_locataire": "loc-2",
            "date_loyer": "2026-03-05",
            "montant": 1650,
            "statut": "en_attente",
            "quitus_genere": False,
        },
    ]
    fake_supabase.store["charges"] = [
        {
            "id": "charge-1",
            "id_bien": "bien-1",
            "type_charge": "assurance",
            "montant": 240,
            "date_paiement": "2026-02-10",
        },
        {
            "id": "charge-2",
            "id_bien": "bien-2",
            "type_charge": "travaux",
            "montant": 600,
            "date_paiement": "2026-03-02",
        },
    ]
    fake_supabase.store["fiscalite"] = [
        {
            "id": "fisc-1",
            "id_sci": "sci-1",
            "annee": 2025,
            "total_revenus": 34200,
            "total_charges": 5400,
            "resultat_fiscal": 28800,
        }
    ]

    response = client.get("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["nom"] == "SCI Mosa Belleville"
    assert data["associes_count"] == 2
    assert data["biens_count"] == 2
    assert data["loyers_count"] == 2
    assert data["charges_count"] == 2
    assert data["total_monthly_rent"] == 2850
    assert data["total_monthly_property_charges"] == 270
    assert data["paid_loyers_total"] == 1200
    assert data["pending_loyers_total"] == 1650
    assert data["recent_loyers"][0]["id"] == "loyer-2"
    assert data["recent_charges"][0]["id"] == "charge-2"
    assert data["fiscalite"][0]["annee"] == 2025


def test_create_sci_creates_membership(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "active",
            "is_active": True,
            "max_scis": 10,
            "max_biens": 20,
            "features": {
                "multi_sci_enabled": True,
                "charges_enabled": True,
                "fiscalite_enabled": True,
                "quitus_enabled": True,
                "cerfa_enabled": True,
                "priority_support": True,
            },
        }
    ]
    response = client.post(
        "/api/v1/scis/",
        json={"nom": "SCI Delta Paris", "siren": "111222333", "regime_fiscal": "IR"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["nom"] == "SCI Delta Paris"

    associes = fake_supabase.store["associes"]
    created_membership = next(row for row in associes if row["id_sci"] == payload["id"])
    assert created_membership["user_id"] == "user-123"
    assert created_membership["role"] == "gerant"


def test_update_sci_patch(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-1",
        json={"nom": "SCI Mosa Belleville Renommée"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "SCI Mosa Belleville Renommée"


def test_update_sci_empty_payload(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-1",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_sci_requires_gerant(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-2",
        json={"nom": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_delete_sci(client, auth_headers):
    response = client.delete("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 204


def test_delete_sci_requires_gerant(client, auth_headers):
    response = client.delete("/api/v1/scis/sci-2", headers=auth_headers)
    assert response.status_code == 403


# ──────────────────────────────────────────────────────────────
# Coverage boost: helper functions, edge cases, error paths
# ──────────────────────────────────────────────────────────────


def test_list_scis_no_memberships(client, auth_headers, fake_supabase):
    """User with no associes rows gets empty list."""
    fake_supabase.store["associes"] = []
    response = client.get("/api/v1/scis/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_sci_detail_not_member(client, auth_headers, fake_supabase):
    """Accessing a SCI the user is not a member of returns 404."""
    response = client.get("/api/v1/scis/sci-nonexistent", headers=auth_headers)
    assert response.status_code == 404


def test_get_sci_detail_sci_row_missing(client, auth_headers, fake_supabase):
    """SCI row deleted from DB after membership exists -> 404."""
    fake_supabase.store["associes"].append(
        {"id": "assoc-ghost", "id_sci": "sci-ghost", "user_id": "user-123", "nom": "Ghost", "role": "gerant", "part": 100}
    )
    fake_supabase.store["sci"] = [s for s in fake_supabase.store["sci"] if s["id"] != "sci-ghost"]
    response = client.get("/api/v1/scis/sci-ghost", headers=auth_headers)
    assert response.status_code == 404


def test_get_sci_detail_loyers_fallback_by_bien(client, auth_headers, fake_supabase):
    """When loyers have no id_sci, the endpoint falls back to fetching by bien IDs."""
    fake_supabase.store["biens"] = [
        {"id": "bien-fb", "id_sci": "sci-1", "adresse": "Addr", "ville": "V", "code_postal": "00000",
         "type_bien": "appartement", "surface_m2": 30, "loyer_cc": 500, "statut": "loue", "tmi": 30},
    ]
    # loyers with no id_sci match — force fallback path
    fake_supabase.store["loyers"] = [
        {"id": "loyer-fb", "id_bien": "bien-fb", "date_loyer": "2026-01-01", "montant": 500, "statut": "paye"},
    ]
    response = client.get("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # The loyer should be enriched with id_sci from the path
    assert data["loyers_count"] >= 1


def test_get_sci_detail_statut_configuration(client, auth_headers, fake_supabase):
    """SCI with zero biens => statut 'configuration'."""
    fake_supabase.store["biens"] = []
    fake_supabase.store["loyers"] = []
    response = client.get("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["statut"] == "configuration"


def test_get_sci_detail_statut_mise_en_service(client, auth_headers, fake_supabase):
    """SCI with biens but zero loyers => statut 'mise_en_service'."""
    fake_supabase.store["biens"] = [
        {"id": "bien-ms", "id_sci": "sci-1", "adresse": "A", "ville": "V", "code_postal": "00000",
         "loyer_cc": 500, "statut": "loue", "tmi": 30},
    ]
    fake_supabase.store["loyers"] = []
    response = client.get("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["statut"] == "mise_en_service"


def test_create_sci_upgrade_required(client, auth_headers, fake_supabase):
    """Creating a second SCI without multi_sci_enabled raises 402."""
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {"multi_sci_enabled": False},
        }
    ]
    # user-123 already has 2 SCIs via seed associes -> current_scis > 0
    response = client.post(
        "/api/v1/scis/",
        json={"nom": "SCI Third", "siren": "333333333", "regime_fiscal": "IR"},
        headers=auth_headers,
    )
    assert response.status_code == 402


def test_delete_sci_non_member(client, auth_headers, fake_supabase):
    """Deleting a SCI the user is not a member of returns 404."""
    fake_supabase.store["associes"] = [
        a for a in fake_supabase.store["associes"] if a.get("user_id") != "user-123"
    ]
    response = client.delete("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 404


def test_delete_sci_cascades_child_tables(client, auth_headers, fake_supabase):
    """Delete SCI cascade: biens, baux, bail_locataires, charges, loyers, documents, etc."""
    # Seed a full hierarchy
    fake_supabase.store["biens"] = [
        {"id": "bien-del", "id_sci": "sci-1", "adresse": "D", "ville": "V", "code_postal": "00000",
         "loyer_cc": 500, "statut": "loue", "tmi": 30},
    ]
    fake_supabase.store["baux"] = [
        {"id": "bail-del", "id_bien": "bien-del", "statut": "en_cours"},
    ]
    fake_supabase.store["bail_locataires"] = [
        {"id_bail": "bail-del", "id_locataire": "loc-del"},
    ]
    fake_supabase.store["charges"] = [
        {"id": "charge-del", "id_bien": "bien-del", "type_charge": "taxe", "montant": 100, "date_paiement": "2026-01-01"},
    ]
    fake_supabase.store["loyers"] = [
        {"id": "loyer-del", "id_bien": "bien-del", "id_sci": "sci-1", "date_loyer": "2026-01-01", "montant": 500, "statut": "paye"},
    ]
    fake_supabase.store["documents"] = [
        {"id": "doc-del", "id_bien": "bien-del"},
    ]
    fake_supabase.store["assurance_pno"] = [
        {"id": "pno-del", "id_bien": "bien-del"},
    ]
    fake_supabase.store["frais_agence"] = [
        {"id": "frais-del", "id_bien": "bien-del"},
    ]
    fake_supabase.store["fiscalite"] = [
        {"id": "fisc-del", "id_sci": "sci-1", "annee": 2025},
    ]
    fake_supabase.store["notifications"] = [
        {"id": "notif-del", "id_sci": "sci-1"},
    ]

    response = client.delete("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 204

    # Verify child tables cleaned
    assert not any(b["id"] == "bien-del" for b in fake_supabase.store.get("biens", []))
    assert not any(c["id"] == "charge-del" for c in fake_supabase.store.get("charges", []))


_ASSOC_SCI_UUID = "11111111-1111-1111-1111-111111111111"
_ASSOC_SCI_UUID_RO = "22222222-2222-2222-2222-222222222222"


def _setup_uuid_scis(fake_supabase):
    """Setup SCI data with proper UUIDs for associes endpoints (require UUID sci_id)."""
    fake_supabase.store["sci"].extend([
        {"id": _ASSOC_SCI_UUID, "nom": "SCI UUID Test", "siren": "111111111", "regime_fiscal": "IR"},
        {"id": _ASSOC_SCI_UUID_RO, "nom": "SCI UUID RO", "siren": "222222222", "regime_fiscal": "IS"},
    ])
    fake_supabase.store["associes"].extend([
        {"id": "assoc-uuid-g", "id_sci": _ASSOC_SCI_UUID, "user_id": "user-123", "nom": "Gerant UUID", "email": "g@t.com", "part": 60, "role": "gerant"},
        {"id": "assoc-uuid-a", "id_sci": _ASSOC_SCI_UUID, "user_id": "user-456", "nom": "Assoc UUID", "email": "a@t.com", "part": 40, "role": "associe"},
        {"id": "assoc-uuid-ro", "id_sci": _ASSOC_SCI_UUID_RO, "user_id": "user-123", "nom": "RO User", "email": "ro@t.com", "part": 100, "role": "associe"},
    ])


def test_list_sci_associes(client, auth_headers, fake_supabase):
    """GET /scis/{sci_id}/associes returns associes for the SCI."""
    _setup_uuid_scis(fake_supabase)
    response = client.get(f"/api/v1/scis/{_ASSOC_SCI_UUID}/associes", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    noms = {a["nom"] for a in data}
    assert "Gerant UUID" in noms


def test_list_sci_associes_requires_auth(client):
    response = client.get(f"/api/v1/scis/{_ASSOC_SCI_UUID}/associes")
    assert response.status_code == 401


def test_invite_associe_as_gerant(client, auth_headers, fake_supabase):
    """POST /scis/{sci_id}/associes creates a new associe."""
    _setup_uuid_scis(fake_supabase)
    response = client.post(
        f"/api/v1/scis/{_ASSOC_SCI_UUID}/associes",
        json={"nom": "Nouvel Associe", "email": "new@sci.local", "part": 10, "role": "associe"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nom"] == "Nouvel Associe"
    assert data["part"] == 10


def test_invite_associe_requires_auth(client):
    response = client.post(
        f"/api/v1/scis/{_ASSOC_SCI_UUID}/associes",
        json={"nom": "X", "part": 5},
    )
    assert response.status_code == 401


def test_invite_associe_as_non_gerant_returns_403(client, auth_headers, fake_supabase):
    """Only gerant can invite associes."""
    _setup_uuid_scis(fake_supabase)
    response = client.post(
        f"/api/v1/scis/{_ASSOC_SCI_UUID_RO}/associes",
        json={"nom": "Intrus", "part": 5, "role": "associe"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_sum_numeric_with_non_numeric_values():
    """_sum_numeric should gracefully skip non-numeric values."""
    from app.api.v1.scis import _sum_numeric
    rows = [
        {"montant": 100},
        {"montant": "not-a-number"},
        {"montant": None},
        {"montant": 200.5},
    ]
    result = _sum_numeric(rows, "montant")
    assert result == 300.5


def test_build_sci_overview_no_id():
    """_build_sci_overview returns None when sci_row has no id."""
    from app.api.v1.scis import _build_sci_overview
    result = _build_sci_overview({"nom": "X"}, [], [], [], [])
    assert result is None


def test_derive_sci_status():
    """_derive_sci_status returns correct statuses."""
    from app.api.v1.scis import _derive_sci_status
    assert _derive_sci_status(0, 0) == "configuration"
    assert _derive_sci_status(1, 0) == "mise_en_service"
    assert _derive_sci_status(1, 1) == "exploitation"


def test_sort_rows_desc():
    """_sort_rows_desc sorts by key descending, handling missing keys."""
    from app.api.v1.scis import _sort_rows_desc
    rows = [{"date": "2025-01-01"}, {"date": "2026-01-01"}, {}]
    result = _sort_rows_desc(rows, "date")
    assert result[0]["date"] == "2026-01-01"
    assert result[-1] == {}


def test_select_by_field_values_empty():
    """_select_by_field_values with empty list returns empty."""
    from app.api.v1.scis import _select_by_field_values
    result = _select_by_field_values(None, "table", "field", [])
    assert result == []
