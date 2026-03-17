

def galvanic_current_density(
    anode_potential_v: float,
    cathode_potential_v: float,
    polarization_resistance_ohm_m2: float,
) -> float:
    """
    Simplified galvanic current density placeholder.

    i_galvanic ~= (E_cathode - E_anode) / R_p
    """
    potential_delta = cathode_potential_v - anode_potential_v
    if polarization_resistance_ohm_m2 <= 0:
        raise ValueError("polarization_resistance_ohm_m2 must be greater than 0")
    return max(potential_delta / polarization_resistance_ohm_m2, 0.0)
