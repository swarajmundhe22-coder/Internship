

from app.services.copilot_service import CopilotService


def _asset_guidance(asset_key: str | None) -> list[str]:
    key = (asset_key or "").strip().lower()

    if key.startswith("pipeline"):
        return [
            "Verify coating condition, cathodic protection output, and wall-thickness readings along high-risk spans.",
            "Prioritize elbows, welds, supports, and low-drain points for close inspection.",
        ]
    if key.startswith("bridge"):
        return [
            "Check connection details, drainage, and coating breakdown at joints and splash-exposed locations.",
            "Inspect gusset plates, bearings, and fatigue-prone members before the next service window.",
        ]
    if key.startswith("marine_vessel") or key.startswith("offshore"):
        return [
            "Inspect the splash zone, seawater-facing surfaces, anodes, and coating holidays.",
            "Schedule close visual inspection of weld seams, penetrations, and repair history.",
        ]
    if key.startswith("storage_tank"):
        return [
            "Check shell courses, nozzle regions, bottom plates, and water-draw points for active corrosion.",
            "Confirm coating integrity and corrosion allowance against the current service interval.",
        ]
    if key == "cooling_tower":
        return [
            "Inspect fill, drift-exposed surfaces, fasteners, and basin areas for chemical attack or scaling.",
            "Review water chemistry control and cleaning frequency before the next operating cycle.",
        ]
    if key == "reinforced_concrete":
        return [
            "Inspect for cracking, spalling, rebar exposure, and chloride ingress at wet or sheltered zones.",
            "Validate cover depth, drainage, and any prior patch repairs against the current condition rating.",
        ]
    if key.startswith("wind_turbine"):
        return [
            "Inspect the tower base, flange joints, internal humidity, and anchor bolts for early deterioration.",
            "Review access logs and maintenance history before scheduling the next shutdown window.",
        ]

    return [
        "Review the predicted hotspots against site inspection notes and maintenance history.",
        "Schedule a targeted field inspection before the next service interval.",
    ]


def prevention_recommendation(risk_level: str, asset_key: str | None = None) -> str:
    """Map risk class and asset type to preventive engineering guidance."""
    prompt = (
        f"Generate a brief, highly technical, and advanced preventive engineering "
        f"recommendation for a {asset_key or 'generic asset'} with a {risk_level} corrosion risk level. "
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


def operational_guidance(risk_level: str, asset_key: str | None = None, fallback_applied: bool = False) -> list[str]:
    guidance = _asset_guidance(asset_key)

    if risk_level.lower() in {"critical", "high"}:
        guidance.insert(0, "Escalate to an engineer-of-record review before the next operating decision.")
    elif risk_level.lower() == "moderate" and guidance:
        guidance.insert(0, "Maintain normal service but bring forward the next inspection interval.")

    if fallback_applied:
        guidance.append("Confidence was low, so use the conservative output for planning until recalibration completes.")

    return guidance[:4]
