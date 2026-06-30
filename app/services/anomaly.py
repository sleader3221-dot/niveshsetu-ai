from __future__ import annotations

from statistics import mean, pstdev
from typing import Dict, Iterable, List


def detect_spend_anomalies(transactions: Iterable[Dict]) -> List[Dict]:
    txns = list(transactions)
    by_category: Dict[str, List[float]] = {}
    for t in txns:
        by_category.setdefault(t["category"], []).append(float(t["amount"]))

    stats = {}
    for category, values in by_category.items():
        stats[category] = {
            "mean": mean(values),
            "std": pstdev(values) if len(values) > 1 else 0.0,
        }

    anomalies = []
    for t in txns:
        s = stats[t["category"]]
        std = s["std"] or 1.0
        z_score = (float(t["amount"]) - s["mean"]) / std
        is_round_trip = str(t.get("merchant", "")).lower() in {"unknown", "cash", "wallet-load"} and float(t["amount"]) > 10000
        unusual_time = int(t.get("hour", 12)) in {0, 1, 2, 3, 4}
        if z_score > 2.2 or is_round_trip or unusual_time:
            anomalies.append({
                **t,
                "risk_score": round(min(99, max(10, 40 + z_score * 15 + (20 if is_round_trip else 0) + (10 if unusual_time else 0))), 2),
                "explanation": _explain(z_score, is_round_trip, unusual_time),
            })
    return sorted(anomalies, key=lambda x: x["risk_score"], reverse=True)


def _explain(z_score: float, is_round_trip: bool, unusual_time: bool) -> str:
    reasons = []
    if z_score > 2.2:
        reasons.append("amount is unusually high compared with this customer/category history")
    if is_round_trip:
        reasons.append("large transaction to vague/unknown merchant pattern")
    if unusual_time:
        reasons.append("transaction happened during high-risk late-night window")
    return "; ".join(reasons) or "pattern requires review"
