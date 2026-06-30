from __future__ import annotations

from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List


def transaction_risk_score(t: Dict[str, Any], category_mean: float, category_std: float) -> Dict[str, Any]:
    amount = float(t.get("amount", 0))
    std = category_std or 1.0
    z_score = (amount - category_mean) / std
    merchant = str(t.get("merchant", "")).lower()
    hour = int(t.get("hour", 12))
    is_unknown_payee = merchant in {"unknown", "cash", "wallet-load", "crypto exchange"} or bool(t.get("is_new_payee", False))
    unusual_time = hour in {0, 1, 2, 3, 4}
    geo_jump = float(t.get("geo_distance_km", 0)) > 500
    device_risk = str(t.get("device_id", "")).startswith("new-device")
    velocity_risk = int(t.get("velocity_10m", 0)) >= 4

    score = 12
    reasons = []
    if z_score > 2.2:
        score += min(32, z_score * 12)
        reasons.append("amount is unusually high compared with customer/category history")
    if is_unknown_payee:
        score += 18
        reasons.append("new or vague merchant/payee requires step-up verification")
    if unusual_time:
        score += 13
        reasons.append("transaction happened during high-risk late-night window")
    if geo_jump:
        score += 14
        reasons.append("location is far from normal customer pattern")
    if device_risk:
        score += 16
        reasons.append("new device detected")
    if velocity_risk:
        score += 12
        reasons.append("high transaction velocity within short time window")

    score = round(min(99, max(0, score)), 2)
    if score >= 75:
        action = "block_or_step_up_auth"
    elif score >= 50:
        action = "step_up_auth_and_monitor"
    elif score >= 35:
        action = "soft_alert"
    else:
        action = "allow"

    return {
        "risk_score": score,
        "risk_level": "high" if score >= 75 else "medium" if score >= 50 else "low",
        "recommended_action": action,
        "z_score": round(z_score, 2),
        "explanation": "; ".join(reasons) or "normal pattern",
    }


def detect_spend_anomalies(transactions: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    txns = list(transactions)
    by_category: Dict[str, List[float]] = {}
    for t in txns:
        by_category.setdefault(t["category"], []).append(float(t["amount"]))

    stats = {category: {"mean": mean(values), "std": pstdev(values) if len(values) > 1 else 0.0} for category, values in by_category.items()}
    anomalies = []
    for t in txns:
        s = stats[t["category"]]
        risk = transaction_risk_score(t, s["mean"], s["std"])
        if risk["risk_score"] >= 50 or risk["recommended_action"] != "allow":
            anomalies.append({**t, **risk})
    return sorted(anomalies, key=lambda x: x["risk_score"], reverse=True)


def anomaly_summary(anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
    high = [a for a in anomalies if a["risk_level"] == "high"]
    medium = [a for a in anomalies if a["risk_level"] == "medium"]
    blocked_value = sum(float(a["amount"]) for a in anomalies if a["recommended_action"] == "block_or_step_up_auth")
    return {
        "total_alerts": len(anomalies),
        "high_risk": len(high),
        "medium_risk": len(medium),
        "protected_value": round(blocked_value, 2),
        "top_controls": ["step-up auth", "new-device challenge", "payee cooling period", "human fraud desk review"],
    }
