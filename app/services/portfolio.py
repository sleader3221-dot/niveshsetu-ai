from __future__ import annotations

from math import pow
from typing import Any, Dict, List

ASSET_MODELS = {
    "Conservative": {
        "Liquid / emergency instruments": 25,
        "Fixed deposits / recurring deposits": 35,
        "Short-duration debt-style exposure": 25,
        "Broad-market index equity": 10,
        "Gold / defensive allocation": 5,
    },
    "Balanced": {
        "Liquid / emergency instruments": 12,
        "Fixed deposits / recurring deposits": 18,
        "Short-duration debt-style exposure": 20,
        "Broad-market index equity": 30,
        "Flexi-cap / large-cap equity": 15,
        "Gold / defensive allocation": 5,
    },
    "Growth": {
        "Liquid / emergency instruments": 8,
        "Fixed deposits / recurring deposits": 7,
        "Short-duration debt-style exposure": 15,
        "Broad-market index equity": 38,
        "Flexi-cap / large-cap equity": 22,
        "Gold / defensive allocation": 5,
        "Innovation / thematic satellite cap": 5,
    },
}

EXPECTED_RETURN = {
    "Liquid / emergency instruments": 0.045,
    "Fixed deposits / recurring deposits": 0.065,
    "Short-duration debt-style exposure": 0.070,
    "Broad-market index equity": 0.115,
    "Flexi-cap / large-cap equity": 0.125,
    "Gold / defensive allocation": 0.075,
    "Innovation / thematic satellite cap": 0.140,
}

RISK_VOLATILITY = {
    "Liquid / emergency instruments": 0.010,
    "Fixed deposits / recurring deposits": 0.015,
    "Short-duration debt-style exposure": 0.035,
    "Broad-market index equity": 0.180,
    "Flexi-cap / large-cap equity": 0.220,
    "Gold / defensive allocation": 0.140,
    "Innovation / thematic satellite cap": 0.300,
}


def weighted_return(allocation: Dict[str, int]) -> float:
    return sum(EXPECTED_RETURN[k] * (v / 100) for k, v in allocation.items())


def weighted_volatility(allocation: Dict[str, int]) -> float:
    return sum(RISK_VOLATILITY[k] * (v / 100) for k, v in allocation.items())


def future_value_sip(monthly_sip: float, annual_return: float, months: int) -> float:
    monthly_rate = annual_return / 12
    if monthly_rate <= 0:
        return monthly_sip * months
    return monthly_sip * ((pow(1 + monthly_rate, months) - 1) / monthly_rate)


def required_sip(goal_amount: float, annual_return: float, months: int) -> float:
    monthly_rate = annual_return / 12
    if monthly_rate <= 0:
        return goal_amount / max(months, 1)
    return goal_amount / ((pow(1 + monthly_rate, months) - 1) / monthly_rate)


def recommend_portfolio(risk_bucket: str, monthly_sip: float, goal_amount: float, horizon_years: float) -> Dict[str, Any]:
    allocation = ASSET_MODELS.get(risk_bucket, ASSET_MODELS["Balanced"])
    annual_return = weighted_return(allocation)
    volatility = weighted_volatility(allocation)
    months = max(1, int(horizon_years * 12))
    projected = future_value_sip(monthly_sip, annual_return, months)
    needed = required_sip(goal_amount, annual_return, months)
    gap = goal_amount - projected

    plan = []
    for asset, pct in allocation.items():
        plan.append({
            "asset": asset,
            "allocation_pct": pct,
            "monthly_amount": round(monthly_sip * pct / 100, 2),
            "expected_return_pct": round(EXPECTED_RETURN[asset] * 100, 2),
            "volatility_pct": round(RISK_VOLATILITY[asset] * 100, 2),
            "why": _why_asset(asset, risk_bucket),
        })

    return {
        "risk_bucket": risk_bucket,
        "monthly_sip": round(monthly_sip, 2),
        "goal_amount": round(goal_amount, 2),
        "horizon_years": horizon_years,
        "expected_annual_return": round(annual_return * 100, 2),
        "estimated_portfolio_volatility": round(volatility * 100, 2),
        "projected_value": round(projected, 2),
        "goal_gap": round(gap, 2),
        "goal_completion_pct": round(min(100, projected / goal_amount * 100), 2),
        "required_sip_for_goal": round(needed, 2),
        "monthly_sip_gap": round(max(0, needed - monthly_sip), 2),
        "allocation": plan,
        "rebalancing_rule": "Review monthly cash-flow changes; rebalance if any asset drifts ±5% from target or risk profile changes.",
        "human_review_required": risk_bucket == "Growth" or volatility > 0.14 or goal_amount > 5000000,
        "customer_consent_required": True,
        "product_positioning": "Product-neutral demo allocation; bank production version maps to approved product shelf after governance review.",
    }


def scenario_stress(plan: Dict[str, Any]) -> Dict[str, Any]:
    base = float(plan["projected_value"])
    volatility = float(plan["estimated_portfolio_volatility"]) / 100
    drawdown = min(0.35, volatility * 1.45)
    income_shock = float(plan["monthly_sip"]) * 0.55
    return {
        "market_drawdown_case": {
            "assumed_drawdown_pct": round(drawdown * 100, 2),
            "stressed_value": round(base * (1 - drawdown), 2),
            "recovery_note": "Show drawdown before consent; do not hide volatility from customer.",
        },
        "income_shock_case": {
            "reduced_sip": round(income_shock, 2),
            "action": "Pause satellite/high-risk allocation first; protect emergency fund and essential payments.",
        },
        "liquidity_case": {
            "rule": "Never use emergency corpus for long-lock-in growth allocation.",
        },
    }


def optimize_goal_ladder(monthly_surplus: float, emergency_gap: float, risk_bucket: str) -> List[Dict[str, Any]]:
    liquid_first = min(monthly_surplus * 0.45, max(0, emergency_gap))
    rd_amount = monthly_surplus * (0.25 if risk_bucket == "Conservative" else 0.15)
    sip_amount = max(0, monthly_surplus - liquid_first - rd_amount)
    return [
        {"step": 1, "destination": "Emergency buffer", "monthly_amount": round(liquid_first, 2), "why": "Liquidity before market risk."},
        {"step": 2, "destination": "IDBI RD/FD-style safe bucket", "monthly_amount": round(rd_amount, 2), "why": "Predictable goal discipline."},
        {"step": 3, "destination": "Goal-linked diversified SIP", "monthly_amount": round(sip_amount, 2), "why": "Long-term wealth creation after safeguards."},
    ]


def _why_asset(asset: str, risk_bucket: str) -> str:
    reasons = {
        "Liquid / emergency instruments": "Keeps instant liquidity for shocks and avoids forced selling.",
        "Fixed deposits / recurring deposits": "Provides predictable capital preservation for near-term goals.",
        "Short-duration debt-style exposure": "Adds moderate yield with lower duration risk.",
        "Broad-market index equity": "Low-cost diversified market exposure for long-term wealth creation.",
        "Flexi-cap / large-cap equity": "Adds managed equity growth while limiting concentration.",
        "Gold / defensive allocation": "Acts as a portfolio diversifier during macro stress.",
        "Innovation / thematic satellite cap": "Small capped exposure for higher-growth appetite without dominating portfolio risk.",
    }
    return f"{reasons.get(asset, 'Diversification component.')} Suitability bucket: {risk_bucket}."
