from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class RiskProfile:
    score: int
    bucket: str
    confidence: float
    reasons: List[str]
    suitability_guardrails: List[str]
    component_scores: Dict[str, int]
    required_disclosures: List[str]


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def calculate_risk_profile(input_data: Dict[str, Any]) -> RiskProfile:
    """Explainable suitability engine for bank advisory decision support.

    The engine intentionally avoids black-box behavior. Every major score movement is preserved
    as a reason so a bank adviser, customer, or judge can inspect why the recommendation changed.
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
    prior_market_experience = int(input_data.get("prior_market_experience", 2))
    income_stability = int(input_data.get("income_stability", 4))

    savings_rate = _clip((income - expenses) / max(income, 1), 0, 1)
    components = {
        "age_capacity": 50,
        "goal_horizon": 50,
        "cashflow_resilience": 50,
        "liquidity_buffer": 50,
        "behavioral_tolerance": 50,
        "debt_burden": 50,
        "dependency_load": 50,
        "experience_and_stability": 50,
    }
    reasons: List[str] = ["Base suitability starts from a neutral bank advisory score."]

    if age < 30:
        components["age_capacity"] += 20; reasons.append("Younger age increases long-term recovery capacity: +20 age capacity.")
    elif age > 55:
        components["age_capacity"] -= 25; reasons.append("Near-retirement age needs capital preservation: -25 age capacity.")
    elif age > 45:
        components["age_capacity"] -= 10; reasons.append("Mid/late-career stage slightly reduces loss tolerance: -10 age capacity.")

    if horizon_years >= 10:
        components["goal_horizon"] += 30; reasons.append("Goal horizon above 10 years supports growth allocation: +30 horizon.")
    elif horizon_years < 3:
        components["goal_horizon"] -= 35; reasons.append("Short horizon makes risky assets unsuitable for this goal: -35 horizon.")
    elif horizon_years >= 5:
        components["goal_horizon"] += 12; reasons.append("Medium horizon supports diversified balanced exposure: +12 horizon.")

    if savings_rate >= 0.35:
        components["cashflow_resilience"] += 25; reasons.append("Strong savings rate improves loss absorption capacity: +25 cashflow.")
    elif savings_rate < 0.10:
        components["cashflow_resilience"] -= 30; reasons.append("Low savings rate weakens investment suitability: -30 cashflow.")
    elif savings_rate < 0.20:
        components["cashflow_resilience"] -= 12; reasons.append("Moderate-low savings rate needs cautious allocation: -12 cashflow.")

    if emergency_months >= 6:
        components["liquidity_buffer"] += 22; reasons.append("Emergency buffer above six months protects the investment plan: +22 liquidity.")
    elif emergency_months < 3:
        components["liquidity_buffer"] -= 30; reasons.append("Emergency buffer below three months requires liquidity-first advice: -30 liquidity.")

    components["behavioral_tolerance"] += (volatility_comfort - 3) * 15
    reasons.append(f"Declared volatility comfort {volatility_comfort}/5 changes behavioral tolerance by {(volatility_comfort - 3) * 15:+d}.")

    if debt_to_income > 0.45:
        components["debt_burden"] -= 35; reasons.append("High debt-to-income requires debt reduction before high-risk investing: -35 debt.")
    elif debt_to_income < 0.15:
        components["debt_burden"] += 15; reasons.append("Low debt burden improves advisory suitability: +15 debt.")

    if dependents >= 3:
        components["dependency_load"] -= 25; reasons.append("Multiple dependents increase liquidity and insurance needs: -25 dependency.")
    elif dependents == 0:
        components["dependency_load"] += 8; reasons.append("No dependents improves financial flexibility: +8 dependency.")

    components["experience_and_stability"] += (prior_market_experience - 2) * 8 + (income_stability - 3) * 7
    reasons.append("Market experience and income stability adjust suitability for product complexity.")

    if goal_priority == "capital_protection":
        components["goal_horizon"] -= 18; reasons.append("Capital-protection goal lowers growth suitability: -18.")
    elif goal_priority == "wealth_growth":
        components["goal_horizon"] += 12; reasons.append("Wealth-growth goal supports higher long-term allocation: +12.")

    components = {k: round(_clip(v, 0, 100)) for k, v in components.items()}
    weights = {
        "age_capacity": 0.10,
        "goal_horizon": 0.18,
        "cashflow_resilience": 0.18,
        "liquidity_buffer": 0.16,
        "behavioral_tolerance": 0.16,
        "debt_burden": 0.11,
        "dependency_load": 0.06,
        "experience_and_stability": 0.05,
    }
    score = round(sum(components[k] * weights[k] for k in components))
    score = int(_clip(score, 0, 100))

    if score < 38:
        bucket = "Conservative"
        guardrails = [
            "Avoid high-volatility recommendations until liquidity and debt profile improve.",
            "Prefer emergency buffer, FD/RD, liquid instruments, and short-duration debt-style exposure.",
            "Route any equity-heavy recommendation to mandatory human review.",
        ]
    elif score < 72:
        bucket = "Balanced"
        guardrails = [
            "Use diversified allocation with emergency fund separated from investment corpus.",
            "Avoid concentration and enforce rebalancing drift checks.",
            "Show scenario risk before customer consent.",
        ]
    else:
        bucket = "Growth"
        guardrails = [
            "Limit thematic exposure through satellite caps and clear volatility warnings.",
            "Run stress test and income-shock simulation before final consent.",
            "Keep adviser override available for unsuitable product pushes.",
        ]

    confidence = round(0.72 + min(0.21, abs(score - 50) / 250), 2)
    disclosures = [
        "Decision-support only; this demo does not execute trades or guarantee returns.",
        "Customer consent and authorized adviser review are required for regulated personalized advice.",
        "Recommended allocation must be reviewed when income, goal horizon, debt, or risk appetite changes.",
    ]
    return RiskProfile(
        score=score,
        bucket=bucket,
        confidence=confidence,
        reasons=reasons,
        suitability_guardrails=guardrails,
        component_scores=components,
        required_disclosures=disclosures,
    )


def explain_suitability(profile: RiskProfile) -> Dict[str, Any]:
    return {
        "risk_score": profile.score,
        "risk_bucket": profile.bucket,
        "confidence": profile.confidence,
        "top_factors": profile.reasons[:10],
        "component_scores": profile.component_scores,
        "guardrails": profile.suitability_guardrails,
        "required_disclosures": profile.required_disclosures,
        "compliance_note": "Risk profiling and suitability are visible by design; final action requires consent and authorized human review.",
    }
