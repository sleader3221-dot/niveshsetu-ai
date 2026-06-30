from __future__ import annotations

from typing import Any, Dict, List

KNOWLEDGE_BASE = [
    {
        "topic": "suitability",
        "keywords": ["risk", "suitable", "profile", "recommend"],
        "answer": "Recommendations must fit the customer's goal horizon, risk appetite, liquidity need, dependents, debt burden, emergency buffer, and consent status.",
    },
    {
        "topic": "emergency fund",
        "keywords": ["emergency", "buffer", "liquidity"],
        "answer": "A practical baseline is three to six months of essential expenses before aggressive investing. For volatile income, six to twelve months is safer.",
    },
    {
        "topic": "sip",
        "keywords": ["sip", "invest", "goal", "wealth"],
        "answer": "A SIP converts monthly savings into disciplined investing. The best banking UX is goal-linked auto-sweep: salary credit → expense reserve → emergency fund → SIP/RD allocation.",
    },
    {
        "topic": "fraud",
        "keywords": ["fraud", "anomaly", "unknown", "transaction"],
        "answer": "Late-night, high-value, unknown-merchant, unusual-location, new-device, and high-velocity transactions should be flagged for step-up authentication or review.",
    },
    {
        "topic": "human review",
        "keywords": ["review", "adviser", "approval", "human"],
        "answer": "High-risk recommendations, low-confidence AI output, unusual customer profile changes, and vulnerable-customer cases should be routed to a human adviser.",
    },
    {
        "topic": "kill switch",
        "keywords": ["kill", "pause", "disable", "governance"],
        "answer": "A bank-grade AI system needs an operational kill switch so model-risk teams can pause or override automated decision support instantly.",
    },
]


def answer_question(question: str, risk_bucket: str = "Balanced") -> Dict[str, Any]:
    q = question.lower()
    matched: List[Dict[str, Any]] = []
    for item in KNOWLEDGE_BASE:
        if any(keyword in q for keyword in item["keywords"]):
            matched.append(item)
    if not matched:
        matched = [KNOWLEDGE_BASE[0], KNOWLEDGE_BASE[2]]

    answer = " ".join(item["answer"] for item in matched[:2])
    answer += f" For the current profile bucket ({risk_bucket}), the assistant must show a risk badge, key reasons, downside scenario, and a human-review/consent option before action."

    confidence = 0.86 if len(matched) > 1 else 0.76
    human_review = risk_bucket == "Growth" or confidence < 0.80 or any(item["topic"] in {"human review", "fraud"} for item in matched)
    return {
        "answer": answer,
        "citations": [item["topic"] for item in matched[:2]],
        "confidence": confidence,
        "human_review_recommended": human_review,
        "guardrail": "No trade/order execution is performed in this demo. Final regulated advice requires authorized review and explicit consent.",
        "next_best_actions": [
            "Show suitability summary",
            "Run stress scenario",
            "Capture customer consent",
            "Route to adviser if high risk or low confidence",
        ],
    }


def generate_customer_nudges(summary: Dict[str, Any], risk_bucket: str) -> List[Dict[str, Any]]:
    savings_rate = float(summary.get("estimated_savings_rate_pct", 0))
    category = summary.get("category_breakdown", {})
    entertainment = float(category.get("Entertainment", 0))
    shopping = float(category.get("Shopping", 0))
    nudges = []
    if savings_rate < 25:
        nudges.append({"type": "cashflow", "priority": "high", "message": "Create an automatic expense reserve before investing more."})
    if entertainment + shopping > 120000:
        nudges.append({"type": "behavior", "priority": "medium", "message": "Redirect 10% of discretionary spend into a goal-linked RD/SIP."})
    nudges.append({"type": "advisory", "priority": "medium", "message": f"Use a {risk_bucket.lower()} allocation with explicit risk disclosure and monthly rebalancing."})
    nudges.append({"type": "consent", "priority": "mandatory", "message": "Ask for consent before using transaction data for personalized advice."})
    return nudges
