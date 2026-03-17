import math


def faraday_mass_loss(
    current_a: float,
    duration_s: float,
    molar_mass_g_mol: float,
    electrons_exchanged: int,
    faraday_constant_c_mol: float = 96485.33212,
) -> float:
    """
    Faraday's Law mass loss estimate:
        m = (I * t * M) / (n * F)

    Returns grams of material dissolved.
    """
    return (current_a * duration_s * molar_mass_g_mol) / (
        electrons_exchanged * faraday_constant_c_mol
    )


def nernst_potential(
    standard_potential_v: float,
    temperature_k: float,
    reaction_quotient: float,
    electrons_exchanged: int,
    gas_constant_j_mol_k: float = 8.314462618,
    faraday_constant_c_mol: float = 96485.33212,
) -> float:
    """
    Nernst equation:
        E = E0 - (R * T / (n * F)) * ln(Q)

    Returns electrode potential in volts.
    """
    if reaction_quotient <= 0:
        raise ValueError("reaction_quotient must be greater than 0")

    return standard_potential_v - (
        (gas_constant_j_mol_k * temperature_k) / (electrons_exchanged * faraday_constant_c_mol)
    ) * math.log(reaction_quotient)
