from __future__ import annotations

from typing import Dict, List

KNOWLEDGE_BASE = [
    {
        "topic": "suitability",
        "answer": "Recommendations must fit the customer's goal horizon, risk appetite, liquidity need, dependents, debt burden, and emergency buffer. Conservative customers should not receive high-risk product pushes.",
    },
    {
        "topic": "emergency fund",
        "answer": "A practical baseline is three to six months of essential expenses before aggressive investing. For volatile income, six to twelve months is safer.",
    },
    {
        "topic": "sip",
        "answer": "A SIP converts monthly savings into disciplined investing. For mobile banking, the best UX is goal-linked auto-sweep: salary credit → expenses reserve → emergency fund → SIP/RD allocation.",
    },
    {
        "topic": "fraud",
        "answer": "Late-night, high-value, unknown-merchant, unusual-location, and device-risk transactions should be flagged for step-up authentication or review.",
    },
    {
        "topic": "human review",
        "answer": "High-risk investment recommendations, low-confidence AI output, unusual customer profile changes, and vulnerable-customer cases should be routed to a human adviser.",
    },
]


def answer_question(question: str, risk_bucket: str = "Balanced") -> Dict:
    q = question.lower()
    matched: List[Dict] = []
    for item in KNOWLEDGE_BASE:
        if item["topic"] in q or any(word in q for word in item["topic"].split()):
            matched.append(item)
    if not matched:
        matched = [KNOWLEDGE_BASE[0], KNOWLEDGE_BASE[2]]

    answer = " ".join(item["answer"] for item in matched[:2])
    answer += f" For your current demo profile bucket ({risk_bucket}), the assistant should show a clear reason, risk badge, and human-review option before execution."

    return {
        "answer": answer,
        "citations": [item["topic"] for item in matched[:2]],
        "confidence": 0.82 if len(matched) > 1 else 0.74,
        "guardrail": "No trade/order execution is performed in this demo. Final regulated advice requires authorized review and explicit consent.",
    }
