from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class RiskProfile:
    score: int
    bucket: str
    reasons: List[str]
    suitability_guardrails: List[str]


def calculate_risk_profile(input_data: Dict) -> RiskProfile:
    """Transparent suitability engine for demo robo-advisory.

    It is intentionally explainable: every point addition/subtraction is captured in reasons.
    The result should be treated as a decision-support output, not regulated investment advice.
    """

    age = int(input_data.get("age", 30))
    income = float(input_data.get("monthly_income", 50000))
    expenses = float(input_data.get("monthly_expenses", 25000))
    dependents = int(input_data.get("dependents", 0))
    horizon_years = float(input_data.get("horizon_years", 5))
    emergency_months = float(input_data.get("emergency_months", 3))
    volatility_comfort = int(input_data.get("volatility_comfort", 3))
    debt_to_income = float(input_data.get("debt_to_income", 0.2))
    goal_priority = str(input_data.get("goal_priority", "balanced")).lower()

    score = 50
    reasons: List[str] = ["Base suitability score starts at 50."]

    savings_rate = max(0.0, min(1.0, (income - expenses) / max(income, 1)))
    if age < 30:
        score += 8; reasons.append("Younger age allows longer recovery time from market volatility: +8.")
    elif age > 55:
        score -= 10; reasons.append("Near-retirement age needs stronger capital preservation: -10.")

    if horizon_years >= 10:
        score += 15; reasons.append("Long investment horizon supports higher equity allocation: +15.")
    elif horizon_years < 3:
        score -= 18; reasons.append("Short horizon requires capital protection and liquidity: -18.")

    if savings_rate >= 0.35:
        score += 10; reasons.append("Strong savings rate improves risk capacity: +10.")
    elif savings_rate < 0.10:
        score -= 14; reasons.append("Low savings buffer reduces loss absorption capacity: -14.")

    if emergency_months >= 6:
        score += 7; reasons.append("Emergency fund above six months improves resilience: +7.")
    elif emergency_months < 3:
        score -= 12; reasons.append("Emergency fund below three months limits investment risk suitability: -12.")

    score += (volatility_comfort - 3) * 6
    reasons.append(f"Declared volatility comfort ({volatility_comfort}/5) adjusts score by {(volatility_comfort - 3) * 6:+d}.")

    if dependents >= 3:
        score -= 8; reasons.append("Multiple dependents increase cash-flow responsibility: -8.")
    elif dependents == 0:
        score += 3; reasons.append("No dependents provides slightly higher flexibility: +3.")

    if debt_to_income > 0.45:
        score -= 15; reasons.append("High debt-to-income ratio needs debt reduction before high-risk investing: -15.")
    elif debt_to_income < 0.15:
        score += 5; reasons.append("Low debt burden improves risk capacity: +5.")

    if goal_priority == "capital_protection":
        score -= 10; reasons.append("Goal priority is capital protection: -10.")
    elif goal_priority == "wealth_growth":
        score += 8; reasons.append("Goal priority is wealth growth: +8.")

    score = max(0, min(100, round(score)))

    if score < 35:
        bucket = "Conservative"
        guardrails = [
            "Avoid high-volatility products until emergency fund and debt profile improve.",
            "Prefer liquid funds, fixed deposits, short-duration debt, and goal-linked safe instruments.",
            "Any equity exposure should be capped and reviewed by a human adviser.",
        ]
    elif score < 70:
        bucket = "Balanced"
        guardrails = [
            "Use diversified hybrid allocation with rebalancing and downside guardrails.",
            "Keep emergency fund separate from investment corpus.",
            "Avoid concentrated product recommendations.",
        ]
    else:
        bucket = "Growth"
        guardrails = [
            "Diversify equity allocation across index, flexi-cap, and international exposure where allowed.",
            "Run scenario stress tests before final recommendation.",
            "Keep stop-loss-style alerts for sharp drawdowns and income shocks.",
        ]

    return RiskProfile(score=score, bucket=bucket, reasons=reasons, suitability_guardrails=guardrails)


def explain_suitability(profile: RiskProfile) -> Dict:
    return {
        "risk_score": profile.score,
        "risk_bucket": profile.bucket,
        "top_factors": profile.reasons[:8],
        "guardrails": profile.suitability_guardrails,
        "compliance_note": "Decision-support only. Final investment advice requires SEBI-registered adviser review and customer consent.",
    }
