from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(os.getenv("AUDIT_DB_PATH", Path(__file__).resolve().parents[2] / "audit.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_audit_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'info',
                correlation_id TEXT NOT NULL,
                prev_hash TEXT,
                decision_hash TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_cases (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                customer_id TEXT NOT NULL,
                case_type TEXT NOT NULL,
                status TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload TEXT NOT NULL,
                decision_hash TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_events(ts DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_correlation ON audit_events(correlation_id)")
        conn.commit()


def stable_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _last_hash() -> Optional[str]:
    with _connect() as conn:
        row = conn.execute("SELECT decision_hash FROM audit_events ORDER BY ts DESC LIMIT 1").fetchone()
    return row["decision_hash"] if row else None


def log_event(
    actor: str,
    action: str,
    payload: Dict[str, Any],
    *,
    severity: str = "info",
    correlation_id: Optional[str] = None,
) -> Dict[str, Any]:
    init_audit_db()
    event_id = str(uuid.uuid4())
    ts = time.time()
    prev_hash = _last_hash()
    correlation_id = correlation_id or str(uuid.uuid4())
    record = {
        "id": event_id,
        "ts": ts,
        "actor": actor,
        "action": action,
        "payload": payload,
        "severity": severity,
        "correlation_id": correlation_id,
        "prev_hash": prev_hash,
    }
    decision_hash = stable_hash(record)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_events(id, ts, actor, action, payload, severity, correlation_id, prev_hash, decision_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                ts,
                actor,
                action,
                json.dumps(payload, sort_keys=True, default=str),
                severity,
                correlation_id,
                prev_hash,
                decision_hash,
            ),
        )
        conn.commit()
    return {**record, "decision_hash": decision_hash}


def list_events(limit: int = 100) -> List[Dict[str, Any]]:
    init_audit_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, ts, actor, action, payload, severity, correlation_id, prev_hash, decision_hash
            FROM audit_events ORDER BY ts DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "ts": row["ts"],
            "actor": row["actor"],
            "action": row["action"],
            "payload": json.loads(row["payload"]),
            "severity": row["severity"],
            "correlation_id": row["correlation_id"],
            "prev_hash": row["prev_hash"],
            "decision_hash": row["decision_hash"],
        }
        for row in rows
    ]


def verify_audit_chain(limit: int = 500) -> Dict[str, Any]:
    init_audit_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, ts, actor, action, payload, severity, correlation_id, prev_hash, decision_hash
            FROM audit_events ORDER BY ts ASC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    broken: List[Dict[str, Any]] = []
    previous_hash: Optional[str] = None
    for row in rows:
        record = {
            "id": row["id"],
            "ts": row["ts"],
            "actor": row["actor"],
            "action": row["action"],
            "payload": json.loads(row["payload"]),
            "severity": row["severity"],
            "correlation_id": row["correlation_id"],
            "prev_hash": row["prev_hash"],
        }
        recalculated = stable_hash(record)
        if recalculated != row["decision_hash"] or row["prev_hash"] != previous_hash:
            broken.append({"id": row["id"], "expected": recalculated, "stored": row["decision_hash"]})
        previous_hash = row["decision_hash"]

    return {
        "verified": not broken,
        "events_checked": len(rows),
        "broken_events": broken,
        "last_hash": previous_hash,
        "control": "SHA-256 chained audit log with tamper-evidence verification",
    }


def audit_stats() -> Dict[str, Any]:
    init_audit_db()
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) c FROM audit_events").fetchone()["c"]
        by_action = conn.execute("SELECT action, COUNT(*) c FROM audit_events GROUP BY action ORDER BY c DESC").fetchall()
        by_severity = conn.execute("SELECT severity, COUNT(*) c FROM audit_events GROUP BY severity ORDER BY c DESC").fetchall()
    return {
        "total_events": total,
        "by_action": {row["action"]: row["c"] for row in by_action},
        "by_severity": {row["severity"]: row["c"] for row in by_severity},
    }


def create_approval_case(
    customer_id: str,
    case_type: str,
    risk_level: str,
    summary: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    init_audit_db()
    case_id = f"CASE-{uuid.uuid4().hex[:10].upper()}"
    ts = time.time()
    record = {
        "id": case_id,
        "ts": ts,
        "customer_id": customer_id,
        "case_type": case_type,
        "status": "pending_human_review",
        "risk_level": risk_level,
        "summary": summary,
        "payload": payload,
    }
    decision_hash = stable_hash(record)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO approval_cases(id, ts, customer_id, case_type, status, risk_level, summary, payload, decision_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                ts,
                customer_id,
                case_type,
                record["status"],
                risk_level,
                summary,
                json.dumps(payload, sort_keys=True, default=str),
                decision_hash,
            ),
        )
        conn.commit()
    log_event("system", "approval_case_created", record, severity="review")
    return {**record, "decision_hash": decision_hash}


def list_approval_cases(limit: int = 50) -> List[Dict[str, Any]]:
    init_audit_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM approval_cases ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "ts": row["ts"],
            "customer_id": row["customer_id"],
            "case_type": row["case_type"],
            "status": row["status"],
            "risk_level": row["risk_level"],
            "summary": row["summary"],
            "payload": json.loads(row["payload"]),
            "decision_hash": row["decision_hash"],
        }
        for row in rows
    ]
