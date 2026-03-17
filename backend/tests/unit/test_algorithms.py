import math

import pytest

from app.algorithms.degradation import corrosion_rate_mm_per_year
from app.algorithms.electrochemistry import faraday_mass_loss, nernst_potential
from app.algorithms.environmental_risk import calculate_environmental_risk
from app.algorithms.lifespan import estimate_lifespan_years
from app.algorithms.risk_classification import classify_failure_risk
from app.models.environment import EnvironmentInput


def test_environmental_risk_score_high_marine_profile() -> None:
    profile = EnvironmentInput(
        temperature_c=25,
        relative_humidity_pct=92,
        chloride_ppm=19000,
        ph=8,
        dissolved_oxygen_mg_l=7.8,
    )
    result = calculate_environmental_risk(profile)
    assert result.risk_score > 70
    assert result.risk_band == "high"


def test_nernst_equation_reference_case() -> None:
    # For Q=10 at 298.15 K and n=2, the correction is about 0.02958 V.
    potential = nernst_potential(
        standard_potential_v=0.50,
        temperature_k=298.15,
        reaction_quotient=10.0,
        electrons_exchanged=2,
    )
    assert potential == pytest.approx(0.4704, abs=1e-3)


def test_faraday_mass_loss_reference_case() -> None:
    # 2 A for 1 hour dissolving Fe (55.845 g/mol, n=2) yields ~2.08 g.
    mass_loss = faraday_mass_loss(
        current_a=2.0,
        duration_s=3600.0,
        molar_mass_g_mol=55.845,
        electrons_exchanged=2,
    )
    assert mass_loss == pytest.approx(2.08, abs=0.02)


def test_corrosion_rate_calculation() -> None:
    rate = corrosion_rate_mm_per_year(
        mass_loss_g=0.75,
        density_g_cm3=7.85,
        area_cm2=100.0,
        exposure_time_h=240.0,
    )
    expected = (87600.0 * 0.75) / (7.85 * 100.0 * 240.0)
    assert rate == pytest.approx(expected)


def test_lifespan_prediction() -> None:
    lifespan = estimate_lifespan_years(
        initial_thickness_mm=12.0,
        minimum_safe_thickness_mm=6.0,
        corrosion_rate_mm_per_year=0.12,
    )
    assert lifespan == pytest.approx(50.0)


def test_risk_classification_logic() -> None:
    assert classify_failure_risk(0.4, 2.0) == "critical"
    assert classify_failure_risk(0.15, 12.0) == "high"
    assert classify_failure_risk(0.04, 20.0) == "moderate"
    assert classify_failure_risk(0.01, 20.0) == "low"


def test_nernst_rejects_nonpositive_reaction_quotient() -> None:
    with pytest.raises(ValueError):
        _ = nernst_potential(0.2, 298.15, 0.0, 2)
