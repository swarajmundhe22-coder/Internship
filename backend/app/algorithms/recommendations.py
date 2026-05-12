

from app.services.copilot_service import CopilotService

def prevention_recommendation(risk_level: str) -> str:
    """Map risk class to preventive engineering guidance using advanced reasoning."""
    prompt = (
        f"Generate a brief, highly technical, and advanced preventive engineering "
        f"recommendation for a pipeline or asset with a {risk_level} corrosion risk level. "
        "Provide specific procedural actions to mitigate further structural degradation. "
        "Keep the output between 1 and 3 sentences."
    )
    
    try:
        copilot = CopilotService()
        response, _ = copilot.query(prompt)
        # Check if the fallback message was returned
        if "NVIDIA copilot key is not configured" in response or "request failed" in response:
            raise ValueError("Copilot service unavailable")
        return response.strip()
    except Exception:
        mapping = {
            "critical": "Immediate shutdown inspection, cathodic protection validation, and material replacement planning.",
            "high": "Increase inspection cadence, apply protective coating maintenance, and evaluate inhibitor dosing.",
            "moderate": "Schedule near-term maintenance and monitor environmental chemistry trends.",
            "low": "Continue baseline monitoring and annual condition assessment.",
        }
        return mapping.get(risk_level, "Perform engineering review for context-specific mitigation.")
