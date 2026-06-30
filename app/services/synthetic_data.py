from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Dict, List

MERCHANTS = {
    "Groceries": ["D-Mart", "Reliance Smart", "Local Kirana", "BigBasket"],
    "Transport": ["Metro", "Uber", "Rapido", "Fuel Station"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Local Store"],
    "Bills": ["BESCOM", "Airtel", "Jio", "Rent"],
    "Entertainment": ["BookMyShow", "Netflix", "Cafe", "Gaming"],
    "Investments": ["IDBI SIP", "RD Deposit", "Index Fund", "Gold ETF"],
}


def sample_transactions(seed: int = 42, days: int = 90) -> List[Dict]:
    random.seed(seed)
    txns: List[Dict] = []
    start = datetime.now() - timedelta(days=days)
    for i in range(220):
        category = random.choices(
            list(MERCHANTS.keys()),
            weights=[28, 18, 14, 15, 12, 13],
            k=1,
        )[0]
        base = {
            "Groceries": 650,
            "Transport": 280,
            "Shopping": 1600,
            "Bills": 2200,
            "Entertainment": 800,
            "Investments": 5000,
        }[category]
        amount = max(50, random.gauss(base, base * 0.35))
        dt = start + timedelta(days=random.randint(0, days), hours=random.randint(7, 23), minutes=random.randint(0, 59))
        txns.append({
            "id": f"TXN-{i+1:04d}",
            "date": dt.strftime("%Y-%m-%d"),
            "hour": dt.hour,
            "merchant": random.choice(MERCHANTS[category]),
            "category": category,
            "amount": round(amount, 2),
            "type": "debit" if category != "Investments" else "investment",
        })

    # Inject demo anomalies that judges can see instantly.
    txns.extend([
        {"id": "TXN-ANOM-1", "date": datetime.now().strftime("%Y-%m-%d"), "hour": 2, "merchant": "Unknown", "category": "Shopping", "amount": 49999, "type": "debit"},
        {"id": "TXN-ANOM-2", "date": datetime.now().strftime("%Y-%m-%d"), "hour": 3, "merchant": "wallet-load", "category": "Entertainment", "amount": 24999, "type": "debit"},
    ])
    return sorted(txns, key=lambda x: x["date"], reverse=True)


def spend_summary(transactions: List[Dict]) -> Dict:
    categories: Dict[str, float] = {}
    total_spend = 0.0
    investments = 0.0
    for t in transactions:
        amount = float(t["amount"])
        categories[t["category"]] = categories.get(t["category"], 0) + amount
        if t["type"] == "investment":
            investments += amount
        else:
            total_spend += amount
    return {
        "total_spend": round(total_spend, 2),
        "total_investments": round(investments, 2),
        "category_breakdown": {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda item: item[1], reverse=True)},
        "savings_nudge": "Move repeated entertainment overspend into a goal-linked IDBI SIP/RD sweep.",
    }
