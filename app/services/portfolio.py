from __future__ import annotations

from typing import Dict, List

ASSET_MODELS = {
    "Conservative": {
        "Liquid / emergency instruments": 25,
        "Fixed deposits / recurring deposits": 35,
        "Short-duration debt funds": 25,
        "Index equity fund": 10,
        "Gold / defensive allocation": 5,
    },
    "Balanced": {
        "Liquid / emergency instruments": 12,
        "Fixed deposits / recurring deposits": 18,
        "Short-duration debt funds": 20,
        "Index equity fund": 30,
        "Flexi-cap / large-cap equity": 15,
        "Gold / defensive allocation": 5,
    },
    "Growth": {
        "Liquid / emergency instruments": 8,
        "Fixed deposits / recurring deposits": 7,
        "Short-duration debt funds": 15,
        "Index equity fund": 38,
        "Flexi-cap / large-cap equity": 22,
        "Gold / defensive allocation": 5,
        "Innovation / thematic satellite cap": 5,
    },
}

EXPECTED_RETURN = {
    "Liquid / emergency instruments": 0.045,
    "Fixed deposits / recurring deposits": 0.065,
    "Short-duration debt funds": 0.070,
    "Index equity fund": 0.115,
    "Flexi-cap / large-cap equity": 0.125,
    "Gold / defensive allocation": 0.075,
    "Innovation / thematic satellite cap": 0.140,
}

RISK_VOLATILITY = {
    "Liquid / emergency instruments": 0.01,
    "Fixed deposits / recurring deposits": 0.015,
    "Short-duration debt funds": 0.035,
    "Index equity fund": 0.18,
    "Flexi-cap / large-cap equity": 0.22,
    "Gold / defensive allocation": 0.14,
    "Innovation / thematic satellite cap": 0.30,
}


def recommend_portfolio(risk_bucket: str, monthly_sip: float, goal_amount: float, horizon_years: float) -> Dict:
    allocation = ASSET_MODELS.get(risk_bucket, ASSET_MODELS["Balanced"])
    weighted_return = sum(EXPECTED_RETURN[k] * (v / 100) for k, v in allocation.items())
    weighted_volatility = sum(RISK_VOLATILITY[k] * (v / 100) for k, v in allocation.items())

    months = max(1, int(horizon_years * 12))
    monthly_rate = weighted_return / 12
    future_value = monthly_sip * (((1 + monthly_rate) ** months - 1) / monthly_rate) if monthly_rate else monthly_sip * months
    target_gap = goal_amount - future_value
    required_sip = goal_amount / (((1 + monthly_rate) ** months - 1) / monthly_rate) if monthly_rate else goal_amount / months

    plan = []
    for asset, pct in allocation.items():
        plan.append({
            "asset": asset,
            "allocation_pct": pct,
            "monthly_amount": round(monthly_sip * pct / 100, 2),
            "why": _why_asset(asset, risk_bucket),
        })

    return {
        "risk_bucket": risk_bucket,
        "monthly_sip": round(monthly_sip, 2),
        "goal_amount": round(goal_amount, 2),
        "horizon_years": horizon_years,
        "expected_annual_return": round(weighted_return * 100, 2),
        "estimated_portfolio_volatility": round(weighted_volatility * 100, 2),
        "projected_value": round(future_value, 2),
        "goal_gap": round(target_gap, 2),
        "required_sip_for_goal": round(required_sip, 2),
        "allocation": plan,
        "rebalancing_rule": "Review monthly cash-flow changes; rebalance if any asset drifts ±5% from target.",
        "human_review_required": risk_bucket == "Growth" or weighted_volatility > 0.14,
    }


def _why_asset(asset: str, risk_bucket: str) -> str:
    reasons = {
        "Liquid / emergency instruments": "Keeps instant liquidity for shocks and avoids forced selling.",
        "Fixed deposits / recurring deposits": "Provides predictable capital preservation for near-term goals.",
        "Short-duration debt funds": "Adds moderate yield with lower duration risk.",
        "Index equity fund": "Low-cost diversified market exposure for long-term wealth creation.",
        "Flexi-cap / large-cap equity": "Adds managed equity growth while limiting concentration.",
        "Gold / defensive allocation": "Acts as portfolio diversifier during macro stress.",
        "Innovation / thematic satellite cap": "Small capped exposure for higher-growth appetite without dominating portfolio risk.",
    }
    return f"{reasons.get(asset, 'Diversification component.')} Suitability bucket: {risk_bucket}."
