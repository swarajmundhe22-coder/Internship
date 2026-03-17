

def classify_failure_risk(corrosion_rate_mm_per_year: float, lifespan_years: float) -> str:
    """Classify risk using corrosion severity and remaining life."""
    if corrosion_rate_mm_per_year > 0.30 or lifespan_years < 3:
        return "critical"
    if corrosion_rate_mm_per_year > 0.10 or lifespan_years < 8:
        return "high"
    if corrosion_rate_mm_per_year > 0.03 or lifespan_years < 15:
        return "moderate"
    return "low"
