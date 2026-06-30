from app.services.risk_engine import calculate_risk_profile
from app.services.portfolio import recommend_portfolio
from app.services.anomaly import detect_spend_anomalies


def test_risk_profile_growth_case():
    profile = calculate_risk_profile({
        "age": 24,
        "monthly_income": 100000,
        "monthly_expenses": 35000,
        "dependents": 0,
        "horizon_years": 12,
        "emergency_months": 8,
        "volatility_comfort": 5,
        "debt_to_income": 0.05,
        "goal_priority": "wealth_growth",
    })
    assert profile.bucket == "Growth"
    assert profile.score >= 70
    assert len(profile.reasons) >= 5


def test_risk_profile_conservative_case():
    profile = calculate_risk_profile({
        "age": 60,
        "monthly_income": 50000,
        "monthly_expenses": 48000,
        "dependents": 4,
        "horizon_years": 1,
        "emergency_months": 1,
        "volatility_comfort": 1,
        "debt_to_income": 0.6,
        "goal_priority": "capital_protection",
    })
    assert profile.bucket == "Conservative"
    assert profile.score < 35


def test_portfolio_allocation_sums_to_100():
    plan = recommend_portfolio("Balanced", 10000, 1000000, 10)
    assert sum(item["allocation_pct"] for item in plan["allocation"]) == 100
    assert plan["projected_value"] > 0


def test_anomaly_detection_flags_obvious_outlier():
    txns = [
        {"id": "1", "category": "Shopping", "amount": 1000, "merchant": "A", "hour": 12},
        {"id": "2", "category": "Shopping", "amount": 1200, "merchant": "A", "hour": 13},
        {"id": "3", "category": "Shopping", "amount": 99999, "merchant": "unknown", "hour": 2},
    ]
    anomalies = detect_spend_anomalies(txns)
    assert anomalies
    assert anomalies[0]["id"] == "3"
