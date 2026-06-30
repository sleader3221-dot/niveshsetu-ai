from app.services.advisor import answer_question
from app.services.anomaly import anomaly_summary, detect_spend_anomalies, transaction_risk_score
from app.services.audit import audit_stats, log_event, verify_audit_chain
from app.services.governance import drift_report, governance_scorecard, validation_report
from app.services.portfolio import optimize_goal_ladder, recommend_portfolio, scenario_stress
from app.services.risk_engine import calculate_risk_profile
from app.services.synthetic_data import sample_transactions, spend_summary


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
        "prior_market_experience": 4,
        "income_stability": 5,
    })
    assert profile.bucket == "Growth"
    assert profile.score >= 72
    assert profile.component_scores["goal_horizon"] >= 80
    assert len(profile.reasons) >= 7


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
        "prior_market_experience": 0,
        "income_stability": 2,
    })
    assert profile.bucket == "Conservative"
    assert profile.score < 38


def test_portfolio_allocation_sums_to_100_and_stress():
    plan = recommend_portfolio("Balanced", 10000, 1000000, 10)
    assert sum(item["allocation_pct"] for item in plan["allocation"]) == 100
    assert plan["projected_value"] > 0
    stress = scenario_stress(plan)
    assert stress["market_drawdown_case"]["stressed_value"] < plan["projected_value"]


def test_goal_ladder_uses_surplus():
    ladder = optimize_goal_ladder(30000, 60000, "Balanced")
    assert len(ladder) == 3
    assert round(sum(item["monthly_amount"] for item in ladder), 2) == 30000


def test_anomaly_detection_flags_obvious_outlier():
    txns = [
        {"id": "1", "category": "Shopping", "amount": 1000, "merchant": "A", "hour": 12, "is_new_payee": False, "geo_distance_km": 2, "device_id": "trusted", "velocity_10m": 1},
        {"id": "2", "category": "Shopping", "amount": 1200, "merchant": "A", "hour": 13, "is_new_payee": False, "geo_distance_km": 3, "device_id": "trusted", "velocity_10m": 1},
        {"id": "3", "category": "Shopping", "amount": 99999, "merchant": "unknown", "hour": 2, "is_new_payee": True, "geo_distance_km": 900, "device_id": "new-device-x", "velocity_10m": 6},
    ]
    anomalies = detect_spend_anomalies(txns)
    assert anomalies
    assert anomalies[0]["id"] == "3"
    assert anomalies[0]["risk_score"] >= 75


def test_transaction_risk_score_recommends_step_up():
    risk = transaction_risk_score({"amount": 50000, "merchant": "Unknown", "hour": 2, "is_new_payee": True, "geo_distance_km": 1000, "device_id": "new-device-1", "velocity_10m": 5}, 2000, 1000)
    assert risk["recommended_action"] == "block_or_step_up_auth"


def test_synthetic_summary_and_anomaly_summary():
    txns = sample_transactions(seed=7)
    summary = spend_summary(txns)
    anomalies = detect_spend_anomalies(txns)
    alerts = anomaly_summary(anomalies)
    assert summary["total_spend_90d"] > 0
    assert alerts["total_alerts"] >= 3


def test_advisor_guardrails():
    result = answer_question("How much emergency fund before SIP?", "Balanced")
    assert result["confidence"] > 0.7
    assert "No trade" in result["guardrail"]


def test_governance_reports_are_present():
    assert validation_report()["metrics"]["kill_switch_test"] == "passed"
    assert drift_report()["threshold"] > 0
    assert governance_scorecard()["score"] >= 90


def test_audit_chain_verifies_after_log():
    log_event("test", "unit_test_event", {"ok": True})
    stats = audit_stats()
    result = verify_audit_chain(limit=1000)
    assert stats["total_events"] >= 1
    assert result["verified"] is True
