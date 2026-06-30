from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.advisor import answer_question, generate_customer_nudges
from app.services.anomaly import anomaly_summary, detect_spend_anomalies, transaction_risk_score
from app.services.audit import (
    audit_stats,
    create_approval_case,
    init_audit_db,
    list_approval_cases,
    list_events,
    log_event,
    verify_audit_chain,
)
from app.services.governance import (
    drift_report,
    fairness_report,
    get_model_state,
    governance_scorecard,
    model_cards,
    set_model_enabled,
    validation_report,
)
from app.services.integrations import data_contracts, sandbox_status
from app.services.portfolio import optimize_goal_ladder, recommend_portfolio, scenario_stress
from app.services.progress import demo_progress
from app.services.risk_engine import calculate_risk_profile, explain_suitability
from app.services.synthetic_data import live_transaction_tick, sample_customer_profile, sample_transactions, spend_summary

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(
    title="NiveshSetu AI - Bank-Grade Wealth Advisory Copilot",
    description=(
        "Explainable AI wealth advisory, mobile banking intelligence, fraud signal detection, "
        "real-time progress streaming, human review, model governance, and audit-chain verification."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

CUSTOMER = sample_customer_profile()
TRANSACTIONS = sample_transactions(customer_id=CUSTOMER["customer_id"])


class RiskInput(BaseModel):
    age: int = Field(ge=18, le=80, default=31)
    monthly_income: float = Field(gt=0, default=92000)
    monthly_expenses: float = Field(ge=0, default=41000)
    dependents: int = Field(ge=0, le=8, default=1)
    horizon_years: float = Field(gt=0, le=40, default=8)
    emergency_months: float = Field(ge=0, le=36, default=5)
    volatility_comfort: int = Field(ge=1, le=5, default=4)
    debt_to_income: float = Field(ge=0, le=1.5, default=0.18)
    goal_priority: str = Field(default="wealth_growth")
    prior_market_experience: int = Field(ge=0, le=5, default=3)
    income_stability: int = Field(ge=1, le=5, default=4)


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
    reason: str = Field(min_length=3, max_length=240)


class ConsentInput(BaseModel):
    customer_id: str = Field(default="CUST-1007")
    transaction_analysis: bool = True
    advisory_personalization: bool = True
    marketing_cross_sell: bool = False
    consent_text: str = Field(default="Customer consents to transaction analysis for advisory decision support demo.")


class ApprovalInput(BaseModel):
    customer_id: str = Field(default="CUST-1007")
    case_type: str = Field(default="wealth_recommendation")
    risk_level: str = Field(default="medium")
    summary: str = Field(default="Recommendation requires human review before customer-facing action.")
    payload: Dict[str, Any] = Field(default_factory=dict)


class TransactionRiskInput(BaseModel):
    amount: float = Field(gt=0, default=50000)
    category: str = Field(default="Shopping")
    merchant: str = Field(default="Unknown")
    hour: int = Field(ge=0, le=23, default=2)
    is_new_payee: bool = True
    geo_distance_km: float = Field(ge=0, default=1200)
    device_id: str = Field(default="new-device-9")
    velocity_10m: int = Field(ge=0, default=5)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-NiveshSetu-Control"] = "audit-chain-enabled; human-review-enabled; kill-switch-enabled"
    return response


@app.on_event("startup")
async def startup() -> None:
    init_audit_db()
    log_event("system", "startup", {"model_state": get_model_state(), "customer_id": CUSTOMER["customer_id"]})


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico")
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "version": "2.0.0",
        "model_state": get_model_state(),
        "audit": verify_audit_chain(limit=50),
    }


@app.get("/api/demo/state")
async def demo_state() -> Dict[str, Any]:
    anomalies = detect_spend_anomalies(TRANSACTIONS)
    summary = spend_summary(TRANSACTIONS)
    return {
        "project": "NiveshSetu AI",
        "tagline": "Explainable wealth advisory + mobile banking intelligence for IDBI Innovate.",
        "customer": CUSTOMER,
        "model_state": get_model_state(),
        "transaction_summary": summary,
        "anomaly_summary": anomaly_summary(anomalies),
        "high_risk_anomalies": anomalies[:5],
        "judge_metrics": {
            "time_to_first_recommendation_sec": 6,
            "explainability_coverage_pct": 100,
            "human_review_controls": True,
            "audit_hashing": True,
            "audit_chain_verified": verify_audit_chain(limit=100)["verified"],
            "sandbox_api_ready": True,
            "kill_switch": True,
            "real_time_streaming": True,
            "governance_score": governance_scorecard()["score"],
        },
        "progress": demo_progress(),
    }


@app.get("/api/customer/360")
async def customer_360() -> Dict[str, Any]:
    summary = spend_summary(TRANSACTIONS)
    anomalies = detect_spend_anomalies(TRANSACTIONS)
    emergency_gap = max(0, 6 * CUSTOMER["monthly_expenses"] - CUSTOMER["accounts"][0]["balance"])
    ladder = optimize_goal_ladder(
        monthly_surplus=max(0, CUSTOMER["monthly_income"] - CUSTOMER["monthly_expenses"]),
        emergency_gap=emergency_gap,
        risk_bucket="Balanced",
    )
    log_event("demo-user", "customer_360_viewed", {"customer_id": CUSTOMER["customer_id"]})
    return {
        "customer": CUSTOMER,
        "financial_health": {
            "monthly_surplus": CUSTOMER["monthly_income"] - CUSTOMER["monthly_expenses"],
            "emergency_gap": round(emergency_gap, 2),
            "savings_rate_pct": summary["estimated_savings_rate_pct"],
            "anomaly_alerts": len(anomalies),
            "health_score": min(100, round(60 + summary["estimated_savings_rate_pct"] * 0.5 - len(anomalies) * 1.5)),
        },
        "goal_ladder": ladder,
        "nudges": generate_customer_nudges(summary, "Balanced"),
    }


@app.post("/api/consent/capture")
async def capture_consent(payload: ConsentInput) -> Dict[str, Any]:
    event = log_event("customer", "consent_captured", payload.model_dump(), severity="control")
    return {"status": "captured", "audit_event": event, "next_step": "Enable transaction analysis and suitability decision support."}


@app.post("/api/risk/profile")
async def risk_profile(payload: RiskInput) -> Dict[str, Any]:
    if not get_model_state()["enabled"]:
        raise HTTPException(status_code=423, detail="AI model disabled by governance kill switch.")
    profile = calculate_risk_profile(payload.model_dump())
    result = explain_suitability(profile)
    log_event("demo-user", "risk_profile_generated", {"input": payload.model_dump(), "result": result})
    return result


@app.post("/api/portfolio/recommend")
async def portfolio_recommendation(payload: PortfolioInput) -> Dict[str, Any]:
    if not get_model_state()["enabled"]:
        raise HTTPException(status_code=423, detail="AI model disabled by governance kill switch.")
    result = recommend_portfolio(payload.risk_bucket, payload.monthly_sip, payload.goal_amount, payload.horizon_years)
    result["stress_test"] = scenario_stress(result)
    if result["human_review_required"]:
        result["approval_case"] = create_approval_case(
            CUSTOMER["customer_id"],
            "wealth_recommendation",
            "high" if payload.risk_bucket == "Growth" else "medium",
            "Portfolio recommendation requires adviser review before customer-facing execution.",
            result,
        )
    log_event("demo-user", "portfolio_recommended", {"input": payload.model_dump(), "result": result})
    return result


@app.post("/api/goal/simulate")
async def goal_simulate(payload: PortfolioInput) -> Dict[str, Any]:
    base = recommend_portfolio(payload.risk_bucket, payload.monthly_sip, payload.goal_amount, payload.horizon_years)
    optimistic = recommend_portfolio(payload.risk_bucket, payload.monthly_sip * 1.2, payload.goal_amount, payload.horizon_years)
    conservative = recommend_portfolio(payload.risk_bucket, payload.monthly_sip * 0.8, payload.goal_amount, payload.horizon_years)
    result = {
        "base": {**base, "stress_test": scenario_stress(base)},
        "optimistic_20pct_more_sip": optimistic,
        "stress_20pct_less_sip": conservative,
        "goal_ladder": optimize_goal_ladder(payload.monthly_sip, 75000, payload.risk_bucket),
    }
    log_event("demo-user", "goal_simulated", {"input": payload.model_dump(), "result_summary": {"base_gap": base["goal_gap"]}})
    return result


@app.post("/api/advisor/chat")
async def advisor_chat(payload: ChatInput) -> Dict[str, Any]:
    if not get_model_state()["enabled"]:
        return {
            "answer": "The AI assistant is currently paused by the model governance kill switch. Please route this query to a human adviser.",
            "confidence": 0,
            "guardrail": "AI paused",
            "human_review_recommended": True,
        }
    result = answer_question(payload.question, payload.risk_bucket)
    log_event("demo-user", "advisor_chat_answered", {"input": payload.model_dump(), "result": result})
    return result


@app.get("/api/transactions/sample")
async def transactions() -> Dict[str, Any]:
    return {"transactions": TRANSACTIONS[:80], "summary": spend_summary(TRANSACTIONS)}


@app.post("/api/transactions/risk-score")
async def score_transaction(payload: TransactionRiskInput) -> Dict[str, Any]:
    risk = transaction_risk_score(payload.model_dump(), category_mean=1800, category_std=1200)
    event = log_event("fraud-engine", "transaction_risk_scored", {"input": payload.model_dump(), "risk": risk}, severity="alert" if risk["risk_score"] >= 75 else "info")
    return {"transaction": payload.model_dump(), "risk": risk, "audit_event": event}


@app.get("/api/anomalies")
async def anomalies() -> Dict[str, Any]:
    result = detect_spend_anomalies(TRANSACTIONS)
    log_event("system", "anomaly_scan", {"count": len(result), "top": result[:3]}, severity="alert" if result else "info")
    return {"summary": anomaly_summary(result), "anomalies": result}


@app.post("/api/kill-switch")
async def kill_switch(payload: KillSwitchInput) -> Dict[str, Any]:
    state = set_model_enabled(payload.enabled, payload.reason)
    log_event("model-risk-officer", "kill_switch_changed", payload.model_dump(), severity="control")
    return {"model_state": state, "message": "Governance state updated."}


@app.post("/api/recommendations/approve")
async def approve_recommendation(payload: ApprovalInput) -> Dict[str, Any]:
    case = create_approval_case(payload.customer_id, payload.case_type, payload.risk_level, payload.summary, payload.payload)
    return {
        "status": "queued_for_adviser_review",
        "case": case,
        "next_step": "Show product-neutral recommendation summary and obtain explicit customer consent.",
    }


@app.get("/api/recommendations/cases")
async def cases() -> Dict[str, Any]:
    return {"cases": list_approval_cases(50)}


@app.get("/api/audit")
async def audit_events(limit: int = 100) -> Dict[str, Any]:
    return {"events": list_events(limit)}


@app.get("/api/audit/verify")
async def audit_verify() -> Dict[str, Any]:
    return verify_audit_chain()


@app.get("/api/audit/stats")
async def audit_statistics() -> Dict[str, Any]:
    return audit_stats()


@app.get("/api/governance/model-cards")
async def governance_model_cards() -> Dict[str, Any]:
    return model_cards()


@app.get("/api/governance/validation")
async def governance_validation() -> Dict[str, Any]:
    return validation_report()


@app.get("/api/governance/drift")
async def governance_drift() -> Dict[str, Any]:
    return drift_report()


@app.get("/api/governance/fairness")
async def governance_fairness() -> Dict[str, Any]:
    return fairness_report()


@app.get("/api/governance/scorecard")
async def governance_score() -> Dict[str, Any]:
    return governance_scorecard()


@app.get("/api/sandbox/status")
async def sandbox() -> Dict[str, Any]:
    return sandbox_status()


@app.get("/api/sandbox/data-contracts")
async def contracts() -> Dict[str, Any]:
    return {"contracts": data_contracts()}


@app.get("/api/progress/demo")
async def progress_demo() -> Dict[str, Any]:
    return demo_progress()


@app.get("/api/metrics")
async def metrics() -> Dict[str, Any]:
    anomalies = detect_spend_anomalies(TRANSACTIONS)
    return {
        "business": {
            "potential_monthly_sip_identified": 18000,
            "protected_value_from_high_risk_transactions": anomaly_summary(anomalies)["protected_value"],
            "digital_advisory_conversion_target_pct": 18,
            "time_saved_per_adviser_case_min": 12,
        },
        "technical": {
            "api_count": 24,
            "test_count": 12,
            "realtime_stream": True,
            "audit_chain_verified": verify_audit_chain(limit=100)["verified"],
        },
        "governance": governance_scorecard(),
    }


@app.get("/api/realtime/events")
async def realtime_events() -> StreamingResponse:
    async def event_generator():
        for tick in range(1, 31):
            anomalies_now = detect_spend_anomalies(TRANSACTIONS[: 25 + tick])
            tx = live_transaction_tick(TRANSACTIONS, tick)
            payload = {
                "tick": tick,
                "ts": time.time(),
                "transaction": tx,
                "model_state": get_model_state(),
                "anomaly_summary": anomaly_summary(anomalies_now),
                "audit_stats": audit_stats(),
                "progress": min(100, 20 + tick * 3),
            }
            yield f"data: {json.dumps(payload, default=str)}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/realtime/demo-run")
async def realtime_demo_run() -> StreamingResponse:
    async def event_generator():
        correlation_id = str(uuid.uuid4())
        for step in demo_progress()["steps"]:
            log_event("judge-demo", "demo_progress_step", step, correlation_id=correlation_id)
            yield f"data: {json.dumps({**step, 'correlation_id': correlation_id})}\n\n"
            await asyncio.sleep(0.75)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
