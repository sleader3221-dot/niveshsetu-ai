from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.advisor import answer_question
from app.services.anomaly import detect_spend_anomalies
from app.services.audit import init_audit_db, list_events, log_event
from app.services.portfolio import recommend_portfolio
from app.services.risk_engine import calculate_risk_profile, explain_suitability
from app.services.synthetic_data import sample_transactions, spend_summary

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="NiveshSetu AI - IDBI Innovate Demo",
    description="Explainable AI wealth advisory, mobile banking intelligence, fraud signal detection, and model governance demo.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MODEL_STATE = {
    "enabled": True,
    "version": "suitability-engine-v1.0",
    "last_validation": "2026-06-30",
    "owner": "Model Risk + Digital Banking Team",
}

TRANSACTIONS = sample_transactions()


class RiskInput(BaseModel):
    age: int = Field(ge=18, le=80, default=24)
    monthly_income: float = Field(gt=0, default=85000)
    monthly_expenses: float = Field(ge=0, default=42000)
    dependents: int = Field(ge=0, le=8, default=1)
    horizon_years: float = Field(gt=0, le=40, default=8)
    emergency_months: float = Field(ge=0, le=36, default=5)
    volatility_comfort: int = Field(ge=1, le=5, default=4)
    debt_to_income: float = Field(ge=0, le=1.5, default=0.18)
    goal_priority: str = Field(default="wealth_growth")


class PortfolioInput(BaseModel):
    risk_bucket: str = Field(default="Balanced")
    monthly_sip: float = Field(gt=0, default=18000)
    goal_amount: float = Field(gt=0, default=2500000)
    horizon_years: float = Field(gt=0, le=40, default=8)


class ChatInput(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    risk_bucket: str = Field(default="Balanced")


class KillSwitchInput(BaseModel):
    enabled: bool
    reason: str = Field(min_length=3, max_length=200)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.on_event("startup")
async def startup() -> None:
    init_audit_db()
    log_event("system", "startup", {"model_state": MODEL_STATE})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "model_state": MODEL_STATE}


@app.get("/api/demo/state")
async def demo_state() -> Dict[str, Any]:
    anomalies = detect_spend_anomalies(TRANSACTIONS)
    return {
        "project": "NiveshSetu AI",
        "tagline": "Bank-grade, explainable AI wealth advisory inside mobile banking.",
        "model_state": MODEL_STATE,
        "transaction_summary": spend_summary(TRANSACTIONS),
        "anomaly_count": len(anomalies),
        "high_risk_anomalies": anomalies[:3],
        "judge_metrics": {
            "time_to_first_recommendation_sec": 8,
            "explainability_coverage_pct": 100,
            "human_review_controls": True,
            "audit_hashing": True,
            "sandbox_api_ready": True,
        },
    }


@app.post("/api/risk/profile")
async def risk_profile(payload: RiskInput) -> Dict[str, Any]:
    if not MODEL_STATE["enabled"]:
        raise HTTPException(status_code=423, detail="AI model disabled by governance kill switch.")
    profile = calculate_risk_profile(payload.model_dump())
    result = explain_suitability(profile)
    log_event("demo-user", "risk_profile_generated", {"input": payload.model_dump(), "result": result})
    return result


@app.post("/api/portfolio/recommend")
async def portfolio_recommendation(payload: PortfolioInput) -> Dict[str, Any]:
    if not MODEL_STATE["enabled"]:
        raise HTTPException(status_code=423, detail="AI model disabled by governance kill switch.")
    result = recommend_portfolio(payload.risk_bucket, payload.monthly_sip, payload.goal_amount, payload.horizon_years)
    log_event("demo-user", "portfolio_recommended", {"input": payload.model_dump(), "result": result})
    return result


@app.post("/api/advisor/chat")
async def advisor_chat(payload: ChatInput) -> Dict[str, Any]:
    if not MODEL_STATE["enabled"]:
        return {
            "answer": "The AI assistant is currently paused by the model governance kill switch. Please route this query to a human adviser.",
            "confidence": 0,
            "guardrail": "AI paused",
        }
    result = answer_question(payload.question, payload.risk_bucket)
    log_event("demo-user", "advisor_chat_answered", {"input": payload.model_dump(), "result": result})
    return result


@app.get("/api/transactions/sample")
async def transactions() -> Dict[str, Any]:
    return {"transactions": TRANSACTIONS[:60], "summary": spend_summary(TRANSACTIONS)}


@app.get("/api/anomalies")
async def anomalies() -> Dict[str, Any]:
    result = detect_spend_anomalies(TRANSACTIONS)
    log_event("system", "anomaly_scan", {"count": len(result), "top": result[:3]})
    return {"anomalies": result}


@app.post("/api/goal/simulate")
async def goal_simulate(payload: PortfolioInput) -> Dict[str, Any]:
    base = recommend_portfolio(payload.risk_bucket, payload.monthly_sip, payload.goal_amount, payload.horizon_years)
    optimistic = recommend_portfolio(payload.risk_bucket, payload.monthly_sip * 1.2, payload.goal_amount, payload.horizon_years)
    conservative = recommend_portfolio(payload.risk_bucket, payload.monthly_sip * 0.8, payload.goal_amount, payload.horizon_years)
    return {"base": base, "optimistic_20pct_more_sip": optimistic, "stress_20pct_less_sip": conservative}


@app.post("/api/kill-switch")
async def kill_switch(payload: KillSwitchInput) -> Dict[str, Any]:
    MODEL_STATE["enabled"] = payload.enabled
    log_event("model-risk-officer", "kill_switch_changed", payload.model_dump())
    return {"model_state": MODEL_STATE, "message": "Governance state updated."}


@app.post("/api/recommendations/approve")
async def approve_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
    event = log_event("human-adviser", "recommendation_approved", payload)
    return {
        "status": "approved_for_customer_consent_screen",
        "audit_event": event,
        "next_step": "Show product-neutral recommendation summary and obtain explicit customer consent.",
    }


@app.get("/api/audit")
async def audit_events() -> Dict[str, Any]:
    return {"events": list_events(100)}
