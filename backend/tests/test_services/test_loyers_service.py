from app.services import loyers_service
from app.schemas.loyers import LoyerCreate


def test_loyers_service_list_and_create():
    assert loyers_service.list_loyers() == []

    payload = LoyerCreate(id_bien="00000000-0000-0000-0000-000000000000", date_loyer="2025-02-01", montant=800)
    created = loyers_service.create_loyer(payload)
    assert created.montant == 800

    results = loyers_service.list_loyers()
    assert len(results) == 1
    assert results[0].montant == 800
