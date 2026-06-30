from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

MERCHANTS = {
    "Groceries": ["D-Mart", "Reliance Smart", "Local Kirana", "BigBasket"],
    "Transport": ["Metro", "Uber", "Rapido", "Fuel Station"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Local Store"],
    "Bills": ["BESCOM", "Airtel", "Jio", "Rent"],
    "Entertainment": ["BookMyShow", "Netflix", "Cafe", "Gaming"],
    "Investments": ["IDBI SIP", "RD Deposit", "Index Fund", "Gold ETF"],
    "Healthcare": ["Apollo Pharmacy", "Clinic", "Diagnostics"],
}

CHANNELS = ["mobile", "upi", "netbanking", "card", "branch"]
LOCATIONS = ["Bengaluru", "Mysuru", "Mumbai", "Delhi", "Hyderabad"]


def sample_customer_profile(customer_id: str = "CUST-1007") -> Dict[str, Any]:
    return {
        "customer_id": customer_id,
        "name": "Demo Customer",
        "segment": "mass-affluent digital banking",
        "age": 31,
        "monthly_income": 92000,
        "monthly_expenses": 41000,
        "dependents": 1,
        "salary_day": 1,
        "accounts": [
            {"type": "savings", "balance": 218500, "currency": "INR"},
            {"type": "recurring_deposit", "balance": 78500, "currency": "INR"},
        ],
        "consents": {
            "transaction_analysis": True,
            "advisory_personalization": True,
            "marketing_cross_sell": False,
        },
        "kyc_status": "verified",
        "preferred_language": "English/Hindi",
        "risk_disclosures_seen": True,
    }


def sample_transactions(seed: int = 42, days: int = 90, customer_id: str = "CUST-1007") -> List[Dict[str, Any]]:
    random.seed(seed)
    txns: List[Dict[str, Any]] = []
    start = datetime.now() - timedelta(days=days)
    balance = 245000.0

    for i in range(260):
        category = random.choices(
            list(MERCHANTS.keys()),
            weights=[25, 15, 13, 14, 10, 15, 8],
            k=1,
        )[0]
        base = {
            "Groceries": 700,
            "Transport": 300,
            "Shopping": 1800,
            "Bills": 2600,
            "Entertainment": 950,
            "Investments": 5600,
            "Healthcare": 1100,
        }[category]
        amount = max(50, random.gauss(base, base * 0.38))
        dt = start + timedelta(days=random.randint(0, days), hours=random.randint(7, 23), minutes=random.randint(0, 59))
        direction = "debit" if category != "Investments" else "investment"
        balance -= amount if direction != "investment" else amount * 0.35
        txns.append({
            "id": f"TXN-{i+1:04d}",
            "customer_id": customer_id,
            "date": dt.strftime("%Y-%m-%d"),
            "timestamp": dt.isoformat(timespec="seconds"),
            "hour": dt.hour,
            "merchant": random.choice(MERCHANTS[category]),
            "category": category,
            "amount": round(amount, 2),
            "type": direction,
            "channel": random.choices(CHANNELS, weights=[55, 22, 10, 10, 3], k=1)[0],
            "location": random.choices(LOCATIONS, weights=[78, 7, 5, 5, 5], k=1)[0],
            "device_id": random.choice(["trusted-phone-1", "trusted-phone-1", "trusted-phone-2"]),
            "is_new_payee": random.random() < 0.04,
            "geo_distance_km": round(abs(random.gauss(18, 25)), 1),
            "velocity_10m": random.choice([1, 1, 1, 2, 2, 3]),
            "balance_after": round(balance, 2),
        })

    now = datetime.now()
    txns.extend([
        {
            "id": "TXN-ANOM-1", "customer_id": customer_id, "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.replace(hour=2, minute=13).isoformat(timespec="seconds"), "hour": 2,
            "merchant": "Unknown", "category": "Shopping", "amount": 49999, "type": "debit",
            "channel": "upi", "location": "Delhi", "device_id": "new-device-9", "is_new_payee": True,
            "geo_distance_km": 1750.0, "velocity_10m": 6, "balance_after": 132000.0,
        },
        {
            "id": "TXN-ANOM-2", "customer_id": customer_id, "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.replace(hour=3, minute=4).isoformat(timespec="seconds"), "hour": 3,
            "merchant": "wallet-load", "category": "Entertainment", "amount": 24999, "type": "debit",
            "channel": "mobile", "location": "Mumbai", "device_id": "trusted-phone-1", "is_new_payee": True,
            "geo_distance_km": 980.0, "velocity_10m": 4, "balance_after": 107001.0,
        },
        {
            "id": "TXN-ANOM-3", "customer_id": customer_id, "date": now.strftime("%Y-%m-%d"),
            "timestamp": now.replace(hour=1, minute=39).isoformat(timespec="seconds"), "hour": 1,
            "merchant": "Crypto Exchange", "category": "Shopping", "amount": 35900, "type": "debit",
            "channel": "card", "location": "Hyderabad", "device_id": "new-device-11", "is_new_payee": True,
            "geo_distance_km": 570.0, "velocity_10m": 5, "balance_after": 71101.0,
        },
    ])
    return sorted(txns, key=lambda x: x["timestamp"], reverse=True)


def spend_summary(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories: Dict[str, float] = {}
    total_spend = 0.0
    investments = 0.0
    channel_mix: Dict[str, int] = {}
    for t in transactions:
        amount = float(t["amount"])
        categories[t["category"]] = categories.get(t["category"], 0.0) + amount
        channel_mix[t["channel"]] = channel_mix.get(t["channel"], 0) + 1
        if t["type"] == "investment":
            investments += amount
        else:
            total_spend += amount
    estimated_monthly_income = 92000
    estimated_monthly_spend = total_spend / 3
    savings_rate = max(0.0, (estimated_monthly_income - estimated_monthly_spend) / estimated_monthly_income)
    return {
        "total_spend_90d": round(total_spend, 2),
        "total_investments_90d": round(investments, 2),
        "estimated_monthly_income": estimated_monthly_income,
        "estimated_monthly_spend": round(estimated_monthly_spend, 2),
        "estimated_savings_rate_pct": round(savings_rate * 100, 2),
        "category_breakdown": {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda item: item[1], reverse=True)},
        "channel_mix": channel_mix,
        "savings_nudge": "Move repeated discretionary overspend into a consent-based goal sweep: salary credit → expense reserve → emergency fund → SIP/RD.",
    }


def live_transaction_tick(transactions: List[Dict[str, Any]], tick: int) -> Dict[str, Any]:
    if not transactions:
        raise ValueError("No transactions available")
    item = transactions[tick % len(transactions)]
    return {**item, "stream_tick": tick, "stream_type": "transaction_intelligence"}
