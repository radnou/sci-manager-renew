import pytest
from pydantic import ValidationError

from app.models.biens import BienCreate


def test_bien_model_validation_success():
    payload = BienCreate(
        id_sci="sci-123",
        adresse="12 avenue Victor Hugo",
        ville="Paris",
        code_postal="75016",
        type_locatif="nu",
        loyer_cc=1200,
        charges=150,
        tmi=30,
        prix_acquisition=250000,
    )
    assert payload.code_postal == "75016"


def test_bien_model_validation_invalid_postcode():
    with pytest.raises(ValidationError):
        BienCreate(
            id_sci="sci-123",
            adresse="12 avenue Victor Hugo",
            ville="Paris",
            code_postal="75A16",
            type_locatif="nu",
            loyer_cc=1200,
        )
