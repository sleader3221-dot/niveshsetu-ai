from __future__ import annotations

from typing import Any, Dict, List


def sandbox_status() -> Dict[str, Any]:
    return {
        "mode": "mock-bank-sandbox",
        "connectors": [
            {"name": "Core banking customer/account API", "status": "mocked", "latency_ms": 42},
            {"name": "Mobile banking transaction stream", "status": "mocked", "latency_ms": 35},
            {"name": "CRM adviser case queue", "status": "mocked", "latency_ms": 48},
            {"name": "Notification service", "status": "mocked", "latency_ms": 31},
            {"name": "Model-risk registry", "status": "mocked", "latency_ms": 27},
        ],
        "production_path": [
            "API gateway + OAuth/OIDC",
            "Customer consent ledger",
            "Core banking read-only data contract",
            "Approved product shelf service",
            "Adviser approval workflow",
            "Audit retention and SIEM forwarding",
        ],
    }


def data_contracts() -> List[Dict[str, Any]]:
    return [
        {"entity": "CustomerProfile", "pii": "tokenized", "required_fields": ["customer_id", "age", "income_band", "dependents", "consents"]},
        {"entity": "Transaction", "pii": "masked", "required_fields": ["id", "amount", "timestamp", "merchant", "category", "channel", "device_id"]},
        {"entity": "AdvisoryRecommendation", "pii": "tokenized", "required_fields": ["risk_bucket", "allocation", "disclosures", "consent_status"]},
        {"entity": "AuditEvent", "pii": "none", "required_fields": ["actor", "action", "payload", "prev_hash", "decision_hash"]},
    ]
