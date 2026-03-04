from app.services import biens_service
from app.schemas.biens import BienCreate


def test_biens_service_list_and_create():
    # at start fake client has no rows
    assert biens_service.list_biens() == []

    payload = BienCreate(id_sci="00000000-0000-0000-0000-000000000000", adresse="test addr")
    created = biens_service.create_bien(payload)
    assert created.adresse == "test addr"
    # list should now return the one created
    results = biens_service.list_biens()
    assert len(results) == 1
    assert results[0].adresse == "test addr"
