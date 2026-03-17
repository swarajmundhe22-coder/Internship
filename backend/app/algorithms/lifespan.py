

def estimate_lifespan_years(
    initial_thickness_mm: float,
    minimum_safe_thickness_mm: float,
    corrosion_rate_mm_per_year: float,
) -> float:
    """Estimate remaining lifespan from thickness loss rate."""
    if corrosion_rate_mm_per_year <= 0:
        return 9999.0

    consumable_thickness = max(initial_thickness_mm - minimum_safe_thickness_mm, 0.0)
    return consumable_thickness / corrosion_rate_mm_per_year
