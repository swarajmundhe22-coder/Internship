

def corrosion_rate_mm_per_year(
    mass_loss_g: float,
    density_g_cm3: float,
    area_cm2: float,
    exposure_time_h: float,
    conversion_constant: float = 87600.0,
) -> float:
    """
    Uniform corrosion penetration rate placeholder:
        CR (mm/year) = K * W / (rho * A * t)

    Where K=87600 when W is grams, rho g/cm^3, A cm^2, t hours.
    """
    if any(x <= 0 for x in [density_g_cm3, area_cm2, exposure_time_h]):
        raise ValueError("density_g_cm3, area_cm2, and exposure_time_h must be > 0")
    return max((conversion_constant * mass_loss_g) / (density_g_cm3 * area_cm2 * exposure_time_h), 0.0)
