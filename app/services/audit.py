from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(__file__).resolve().parents[2] / "audit.db"


def init_audit_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                payload TEXT NOT NULL,
                decision_hash TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _stable_hash(payload: Dict[str, Any]) -> str:
    import hashlib

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def log_event(actor: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    init_audit_db()
    event_id = str(uuid.uuid4())
    ts = time.time()
    record = {
        "id": event_id,
        "ts": ts,
        "actor": actor,
        "action": action,
        "payload": payload,
    }
    decision_hash = _stable_hash(record)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO audit_events(id, ts, actor, action, payload, decision_hash) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, ts, actor, action, json.dumps(payload, sort_keys=True), decision_hash),
        )
        conn.commit()
    return {**record, "decision_hash": decision_hash}


def list_events(limit: int = 100) -> List[Dict[str, Any]]:
    init_audit_db()
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT id, ts, actor, action, payload, decision_hash FROM audit_events ORDER BY ts DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {
            "id": row[0],
            "ts": row[1],
            "actor": row[2],
            "action": row[3],
            "payload": json.loads(row[4]),
            "decision_hash": row[5],
        }
        for row in rows
    ]
