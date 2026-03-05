from app.models.biens import BienCreate as BienCreateModel
from app.models.biens import BienResponse as BienModel
from app.models.biens import BienUpdate as BienUpdateModel
from app.models.loyers import LoyerCreate as LoyerCreateModel
from app.models.loyers import LoyerResponse as LoyerModel
from app.models.loyers import LoyerUpdate as LoyerUpdateModel
from app.schemas import Bien, BienCreate, BienUpdate, Loyer, LoyerCreate, LoyerUpdate


def test_schema_aliases_point_to_models():
    assert Bien is BienModel
    assert BienCreate is BienCreateModel
    assert BienUpdate is BienUpdateModel
    assert Loyer is LoyerModel
    assert LoyerCreate is LoyerCreateModel
    assert LoyerUpdate is LoyerUpdateModel
