"""Tests for app.schemas.declarations — targeting >80% coverage.

Covers all Pydantic models/schemas in declarations.py:
- BilanActifSchema (including .total property)
- BilanPassifSchema (including .total property, with optional fields)
- Declaration2065Schema
- Declaration2065Create
- Declaration2065Response
- Declaration2072Schema
- Declaration2072Create
"""

from __future__ import annotations

from datetime import date

import pytest

from app.schemas.declarations import (
    BilanActifSchema,
    BilanPassifSchema,
    Declaration2065Create,
    Declaration2065Response,
    Declaration2065Schema,
    Declaration2072Create,
    Declaration2072Schema,
)


# ---------------------------------------------------------------------------
# BilanActifSchema
# ---------------------------------------------------------------------------


class TestBilanActifSchema:

    def test_minimal_required_fields(self):
        actif = BilanActifSchema(
            immobilisations_corporelles=150_000.0,
            creances_clients=1_500.0,
            tresorerie_actif=5_000.0,
        )
        assert actif.immobilisations_corporelles == 150_000.0
        assert actif.creances_clients == 1_500.0
        assert actif.tresorerie_actif == 5_000.0
        # Optional fields default to None
        assert actif.travaux_en_cours is None
        assert actif.autres_creances is None

    def test_total_without_optionals(self):
        """Total = immobilisations + creances + tresorerie when optionals are None."""
        actif = BilanActifSchema(
            immobilisations_corporelles=100_000.0,
            creances_clients=2_000.0,
            tresorerie_actif=3_000.0,
        )
        # 100_000 + 0 + 2_000 + 0 + 3_000 = 105_000
        assert actif.total == 105_000.0

    def test_total_with_all_fields(self):
        """Total includes travaux_en_cours and autres_creances when provided."""
        actif = BilanActifSchema(
            immobilisations_corporelles=200_000.0,
            travaux_en_cours=10_000.0,
            creances_clients=3_000.0,
            autres_creances=500.0,
            tresorerie_actif=8_000.0,
        )
        expected = 200_000.0 + 10_000.0 + 3_000.0 + 500.0 + 8_000.0
        assert actif.total == expected

    def test_total_with_zero_optionals(self):
        """Explicit zero for optional fields is included in total (not treated as None)."""
        actif = BilanActifSchema(
            immobilisations_corporelles=50_000.0,
            travaux_en_cours=0.0,
            creances_clients=1_000.0,
            autres_creances=0.0,
            tresorerie_actif=2_000.0,
        )
        # 50_000 + 0 + 1_000 + 0 + 2_000 = 53_000
        assert actif.total == 53_000.0

    def test_validation_error_missing_required(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(Exception):
            BilanActifSchema(
                immobilisations_corporelles=100_000.0,
                # missing creances_clients and tresorerie_actif
            )

    def test_from_dict(self):
        """Instantiation from dict (simulating DB row)."""
        data = {
            "immobilisations_corporelles": 75_000.0,
            "creances_clients": 500.0,
            "tresorerie_actif": 4_000.0,
        }
        actif = BilanActifSchema(**data)
        assert actif.total == 79_500.0


# ---------------------------------------------------------------------------
# BilanPassifSchema
# ---------------------------------------------------------------------------


class TestBilanPassifSchema:

    def test_minimal_required_fields(self):
        passif = BilanPassifSchema(
            capital_social=10_000.0,
            resultat_exercice=5_000.0,
            emprunts=80_000.0,
        )
        assert passif.capital_social == 10_000.0
        assert passif.resultat_exercice == 5_000.0
        assert passif.emprunts == 80_000.0
        # Optional fields default to None
        assert passif.reserves is None
        assert passif.report_a_nouveau is None
        assert passif.dettes_fournisseurs is None
        assert passif.autres_dettes is None

    def test_total_without_optionals(self):
        """Total = capital + resultat + emprunts when all optionals are None."""
        passif = BilanPassifSchema(
            capital_social=10_000.0,
            resultat_exercice=2_000.0,
            emprunts=90_000.0,
        )
        # capitaux = 10_000 + 0 + 0 + 2_000 = 12_000
        # dettes = 90_000 + 0 + 0 = 90_000
        # total = 102_000
        assert passif.total == 102_000.0

    def test_total_with_all_optional_fields(self):
        """Total includes all optional fields when provided."""
        passif = BilanPassifSchema(
            capital_social=10_000.0,
            reserves=3_000.0,
            report_a_nouveau=-500.0,
            resultat_exercice=2_500.0,
            emprunts=120_000.0,
            dettes_fournisseurs=1_200.0,
            autres_dettes=800.0,
        )
        capitaux = 10_000 + 3_000 + (-500) + 2_500
        dettes = 120_000 + 1_200 + 800
        assert passif.total == capitaux + dettes

    def test_total_with_negative_report(self):
        """report_a_nouveau can be negative (accumulated losses)."""
        passif = BilanPassifSchema(
            capital_social=20_000.0,
            report_a_nouveau=-5_000.0,
            resultat_exercice=1_000.0,
            emprunts=50_000.0,
        )
        capitaux = 20_000 + 0 + (-5_000) + 1_000  # 16_000
        dettes = 50_000
        assert passif.total == capitaux + dettes

    def test_validation_error_missing_emprunts(self):
        """Missing emprunts raises ValidationError."""
        with pytest.raises(Exception):
            BilanPassifSchema(
                capital_social=10_000.0,
                resultat_exercice=2_000.0,
                # missing emprunts (required)
            )


# ---------------------------------------------------------------------------
# Declaration2065Schema
# ---------------------------------------------------------------------------


class TestDeclaration2065Schema:

    def _make_actif(self, **kwargs):
        defaults = dict(
            immobilisations_corporelles=150_000.0,
            creances_clients=2_000.0,
            tresorerie_actif=5_000.0,
        )
        defaults.update(kwargs)
        return BilanActifSchema(**defaults)

    def _make_passif(self, **kwargs):
        defaults = dict(
            capital_social=10_000.0,
            resultat_exercice=3_000.0,
            emprunts=140_000.0,
        )
        defaults.update(kwargs)
        return BilanPassifSchema(**defaults)

    def test_valid_declaration(self):
        actif = self._make_actif()
        passif = self._make_passif()
        decl = Declaration2065Schema(
            sci_id="sci-abc-123",
            exercice=2025,
            date_cloture=date(2025, 12, 31),
            actif=actif,
            passif=passif,
            ecart=0.0,
        )
        assert decl.sci_id == "sci-abc-123"
        assert decl.exercice == 2025
        assert decl.ecart == 0.0

    def test_exercice_bounds_valid(self):
        """Exercice must be between 2000 and 2100."""
        actif = self._make_actif()
        passif = self._make_passif()
        decl = Declaration2065Schema(
            sci_id="sci-1",
            exercice=2000,  # lower bound
            date_cloture=date(2000, 12, 31),
            actif=actif,
            passif=passif,
        )
        assert decl.exercice == 2000

        decl2 = Declaration2065Schema(
            sci_id="sci-1",
            exercice=2100,  # upper bound
            date_cloture=date(2100, 12, 31),
            actif=actif,
            passif=passif,
        )
        assert decl2.exercice == 2100

    def test_exercice_below_min_fails(self):
        """Exercice < 2000 raises ValidationError."""
        actif = self._make_actif()
        passif = self._make_passif()
        with pytest.raises(Exception):
            Declaration2065Schema(
                sci_id="sci-1",
                exercice=1999,
                date_cloture=date(1999, 12, 31),
                actif=actif,
                passif=passif,
            )

    def test_exercice_above_max_fails(self):
        """Exercice > 2100 raises ValidationError."""
        actif = self._make_actif()
        passif = self._make_passif()
        with pytest.raises(Exception):
            Declaration2065Schema(
                sci_id="sci-1",
                exercice=2101,
                date_cloture=date(2101, 12, 31),
                actif=actif,
                passif=passif,
            )

    def test_default_ecart(self):
        """ecart defaults to 0.0 when not provided."""
        actif = self._make_actif()
        passif = self._make_passif()
        decl = Declaration2065Schema(
            sci_id="sci-1",
            exercice=2024,
            date_cloture=date(2024, 12, 31),
            actif=actif,
            passif=passif,
        )
        assert decl.ecart == 0.0


# ---------------------------------------------------------------------------
# Declaration2065Create
# ---------------------------------------------------------------------------


class TestDeclaration2065Create:

    def test_minimal_required(self):
        """Only exercice is required."""
        create = Declaration2065Create(exercice=2025)
        assert create.exercice == 2025
        assert create.tresorerie is None
        assert create.reserves is None

    def test_with_optional_fields(self):
        create = Declaration2065Create(
            exercice=2024,
            tresorerie=12_000.0,
            reserves=5_000.0,
        )
        assert create.tresorerie == 12_000.0
        assert create.reserves == 5_000.0

    def test_exercice_ge_2000(self):
        """exercice ge=2000 constraint."""
        with pytest.raises(Exception):
            Declaration2065Create(exercice=1999)

    def test_exercice_le_2100(self):
        """exercice le=2100 constraint."""
        with pytest.raises(Exception):
            Declaration2065Create(exercice=2101)

    def test_exercice_at_bounds(self):
        low = Declaration2065Create(exercice=2000)
        assert low.exercice == 2000
        high = Declaration2065Create(exercice=2100)
        assert high.exercice == 2100


# ---------------------------------------------------------------------------
# Declaration2065Response
# ---------------------------------------------------------------------------


class TestDeclaration2065Response:

    def test_basic_response(self):
        resp = Declaration2065Response(
            sci_id="sci-1",
            exercice=2025,
            date_cloture="2025-12-31",
            actif={"immobilisations_corporelles": 200_000.0, "total": 205_000.0},
            passif={"capital_social": 10_000.0, "total": 205_000.0},
            ecart=0.0,
        )
        assert resp.sci_id == "sci-1"
        assert resp.exercice == 2025
        assert resp.message == "Bilan équilibré"  # default

    def test_custom_message(self):
        resp = Declaration2065Response(
            sci_id="sci-2",
            exercice=2024,
            date_cloture="2024-12-31",
            actif={"total": 100_000.0},
            passif={"total": 95_000.0},
            ecart=5_000.0,
            message="Bilan déséquilibré",
        )
        assert resp.message == "Bilan déséquilibré"
        assert resp.ecart == 5_000.0

    def test_actif_passif_as_dicts(self):
        """actif and passif are plain dicts in the response."""
        resp = Declaration2065Response(
            sci_id="sci-1",
            exercice=2025,
            date_cloture="2025-12-31",
            actif={"key": "value"},
            passif={"key2": "value2"},
            ecart=0.0,
        )
        assert isinstance(resp.actif, dict)
        assert isinstance(resp.passif, dict)


# ---------------------------------------------------------------------------
# Declaration2072Schema
# ---------------------------------------------------------------------------


class TestDeclaration2072Schema:

    def test_valid_2072(self):
        decl = Declaration2072Schema(
            sci_id="sci-xyz",
            exercice=2025,
            revenus_fonciers=24_000.0,
            charges_deductibles=5_000.0,
            interets_emprunt=3_600.0,
            resultat_fiscal=15_400.0,
        )
        assert decl.sci_id == "sci-xyz"
        assert decl.exercice == 2025
        assert decl.revenus_fonciers == 24_000.0
        assert decl.resultat_fiscal == 15_400.0

    def test_negative_resultat_fiscal(self):
        """Deficit case: resultat_fiscal can be negative."""
        decl = Declaration2072Schema(
            sci_id="sci-1",
            exercice=2024,
            revenus_fonciers=12_000.0,
            charges_deductibles=15_000.0,
            interets_emprunt=4_000.0,
            resultat_fiscal=-7_000.0,
        )
        assert decl.resultat_fiscal == -7_000.0

    def test_zero_revenus(self):
        """Zero revenus (vacant property scenario)."""
        decl = Declaration2072Schema(
            sci_id="sci-1",
            exercice=2024,
            revenus_fonciers=0.0,
            charges_deductibles=2_000.0,
            interets_emprunt=1_000.0,
            resultat_fiscal=-3_000.0,
        )
        assert decl.revenus_fonciers == 0.0

    def test_missing_required_field_fails(self):
        """Missing revenus_fonciers raises ValidationError."""
        with pytest.raises(Exception):
            Declaration2072Schema(
                sci_id="sci-1",
                exercice=2025,
                # missing revenus_fonciers
                charges_deductibles=5_000.0,
                interets_emprunt=1_000.0,
                resultat_fiscal=4_000.0,
            )


# ---------------------------------------------------------------------------
# Declaration2072Create
# ---------------------------------------------------------------------------


class TestDeclaration2072Create:

    def test_minimal_required(self):
        create = Declaration2072Create(exercice=2025)
        assert create.exercice == 2025

    def test_exercice_ge_constraint(self):
        with pytest.raises(Exception):
            Declaration2072Create(exercice=1999)

    def test_exercice_le_constraint(self):
        with pytest.raises(Exception):
            Declaration2072Create(exercice=2101)

    def test_exercice_at_lower_bound(self):
        c = Declaration2072Create(exercice=2000)
        assert c.exercice == 2000

    def test_exercice_at_upper_bound(self):
        c = Declaration2072Create(exercice=2100)
        assert c.exercice == 2100
