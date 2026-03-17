

def prevention_recommendation(risk_level: str) -> str:
    """Map risk class to preventive engineering guidance."""
    mapping = {
        "critical": "Immediate shutdown inspection, cathodic protection validation, and material replacement planning.",
        "high": "Increase inspection cadence, apply protective coating maintenance, and evaluate inhibitor dosing.",
        "moderate": "Schedule near-term maintenance and monitor environmental chemistry trends.",
        "low": "Continue baseline monitoring and annual condition assessment.",
    }
    return mapping.get(risk_level, "Perform engineering review for context-specific mitigation.")
