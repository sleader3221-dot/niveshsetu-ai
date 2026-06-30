from __future__ import annotations

from typing import Any, Dict, List

JUDGE_STEPS: List[Dict[str, Any]] = [
    {"step": 1, "name": "Customer consent + 360 profile", "progress": 10, "proof": "Consent-gated mobile banking profile loaded."},
    {"step": 2, "name": "Risk profiling", "progress": 25, "proof": "Explainable suitability score with component factors."},
    {"step": 3, "name": "Goal optimization", "progress": 40, "proof": "Emergency buffer, RD/FD bucket, SIP ladder created."},
    {"step": 4, "name": "Portfolio recommendation", "progress": 55, "proof": "Product-neutral allocation with stress scenario."},
    {"step": 5, "name": "Fraud/anomaly scan", "progress": 70, "proof": "Real-time transaction risk signals produced."},
    {"step": 6, "name": "Advisor copilot", "progress": 82, "proof": "Guardrailed answer with human escalation policy."},
    {"step": 7, "name": "Human review + consent", "progress": 92, "proof": "Approval case generated for high-risk action."},
    {"step": 8, "name": "Audit verification", "progress": 100, "proof": "SHA-256 audit chain verifies the decision trail."},
]


def demo_progress() -> Dict[str, Any]:
    return {
        "status": "ready",
        "progress_pct": 100,
        "steps": JUDGE_STEPS,
        "message": "End-to-end banking PoC flow is integrated for judge demo.",
    }
