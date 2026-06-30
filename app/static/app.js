let currentRiskBucket = "Balanced";
let liveSource = null;

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

function getFormData(formId) {
  const fd = new FormData(document.getElementById(formId));
  return Object.fromEntries([...fd.entries()].map(([k, v]) => [k, isNaN(Number(v)) ? v : Number(v)]));
}

function htmlList(items) {
  return `<ul>${(items || []).map(x => `<li>${typeof x === "string" ? x : JSON.stringify(x)}</li>`).join("")}</ul>`;
}

function badge(text, cls = "") {
  return `<span class="badge ${cls}">${text}</span>`;
}

function money(n) {
  return `₹${Number(n || 0).toLocaleString("en-IN")}`;
}

function setProgress(pct, text) {
  document.querySelector("#progressRail span").style.width = `${pct}%`;
  document.getElementById("progressText").innerText = text || `${pct}% complete`;
}

async function init() {
  const state = await api("/api/demo/state");
  renderModelStatus(state.model_state);
  document.getElementById("kpis").innerHTML = `
    <div class="kpi glass"><span>Recommendation Speed</span><strong>${state.judge_metrics.time_to_first_recommendation_sec}s</strong></div>
    <div class="kpi glass"><span>Explainability</span><strong>${state.judge_metrics.explainability_coverage_pct}%</strong></div>
    <div class="kpi glass"><span>Fraud Alerts</span><strong>${state.anomaly_summary.total_alerts}</strong></div>
    <div class="kpi glass"><span>Governance Score</span><strong>${state.judge_metrics.governance_score}</strong></div>
    <div class="kpi glass"><span>Audit Chain</span><strong>${state.judge_metrics.audit_chain_verified ? "Verified" : "Check"}</strong></div>
    <div class="kpi glass"><span>Real-time</span><strong>${state.judge_metrics.real_time_streaming ? "ON" : "OFF"}</strong></div>
  `;
  await loadCustomer360();
}

function renderModelStatus(model) {
  document.getElementById("modelStatus").innerHTML = model.enabled
    ? `<span class="status-good">AI enabled</span> • ${model.version}`
    : `<span class="status-danger">AI paused</span>`;
}

async function loadCustomer360() {
  const result = await api("/api/customer/360");
  document.getElementById("customer360").innerHTML = `
    <div class="mini-grid">
      <div>${badge("Health Score " + result.financial_health.health_score)}</div>
      <div>${badge("Monthly surplus " + money(result.financial_health.monthly_surplus))}</div>
      <div>${badge("Savings rate " + result.financial_health.savings_rate_pct + "%")}</div>
      <div>${badge("Alerts " + result.financial_health.anomaly_alerts, "warn")}</div>
    </div>
    <h3>Goal ladder</h3>
    ${result.goal_ladder.map(x => `<div class="step"><b>${x.step}. ${x.destination}</b><span>${money(x.monthly_amount)}</span><p>${x.why}</p></div>`).join("")}
    <h3>Nudges</h3>${htmlList(result.nudges.map(n => `${n.priority.toUpperCase()}: ${n.message}`))}
  `;
}

async function generateRisk() {
  try {
    setProgress(25, "Risk profiling running...");
    const payload = getFormData("riskForm");
    payload.goal_priority = "wealth_growth";
    const result = await api("/api/risk/profile", { method: "POST", body: JSON.stringify(payload) });
    currentRiskBucket = result.risk_bucket;
    document.getElementById("portfolioBucket").value = currentRiskBucket;
    document.getElementById("scoreRing").innerText = result.risk_score;
    document.getElementById("riskBucket").innerText = `${result.risk_bucket} Investor`;
    document.getElementById("riskOutput").innerHTML = `
      ${badge(`Risk Score: ${result.risk_score}/100`)} ${badge(`Bucket: ${result.risk_bucket}`)} ${badge(`Confidence: ${result.confidence}`)}
      <h3>Component scores</h3>
      <div class="bars">${Object.entries(result.component_scores).map(([k,v]) => `<div><span>${k.replaceAll("_", " ")}</span><i><b style="width:${v}%"></b></i><em>${v}</em></div>`).join("")}</div>
      <h3>Why this score?</h3>${htmlList(result.top_factors)}
      <h3>Suitability guardrails</h3>${htmlList(result.guardrails)}
      <p><b>Compliance note:</b> ${result.compliance_note}</p>
    `;
    setProgress(35, "Risk profile ready.");
    return result;
  } catch (e) {
    document.getElementById("riskOutput").innerHTML = `<p class="status-danger">${e.message}</p>`;
  }
}

function portfolioPayload() {
  return {
    risk_bucket: document.getElementById("portfolioBucket").value || currentRiskBucket,
    monthly_sip: Number(document.getElementById("monthlySip").value),
    goal_amount: Number(document.getElementById("goalAmount").value),
    horizon_years: Number(document.getElementById("portfolioHorizon").value),
  };
}

async function generatePortfolio() {
  try {
    setProgress(55, "Portfolio engine running...");
    const result = await api("/api/portfolio/recommend", { method: "POST", body: JSON.stringify(portfolioPayload()) });
    document.getElementById("portfolioOutput").innerHTML = renderPortfolio(result);
    setProgress(62, "Portfolio and stress test ready.");
    return result;
  } catch (e) {
    document.getElementById("portfolioOutput").innerHTML = `<p class="status-danger">${e.message}</p>`;
  }
}

function renderPortfolio(result) {
  return `
    ${badge(result.risk_bucket)} ${badge(`Projected ${money(result.projected_value)}`)} ${badge(`Goal ${result.goal_completion_pct}%`)} ${badge(`Required SIP ${money(result.required_sip_for_goal)}`)}
    <div class="table-wrap"><table><thead><tr><th>Asset</th><th>%</th><th>Monthly</th><th>Why</th></tr></thead><tbody>
      ${result.allocation.map(a => `<tr><td>${a.asset}</td><td>${a.allocation_pct}%</td><td>${money(a.monthly_amount)}</td><td>${a.why}</td></tr>`).join("")}
    </tbody></table></div>
    <h3>Stress test</h3>
    ${result.stress_test ? htmlList([
      `Market drawdown: ${money(result.stress_test.market_drawdown_case.stressed_value)} after ${result.stress_test.market_drawdown_case.assumed_drawdown_pct}% stress`,
      `Income shock action: ${result.stress_test.income_shock_case.action}`,
      result.stress_test.liquidity_case.rule
    ]) : ""}
    ${result.approval_case ? `<p class="status-warn"><b>Human review case:</b> ${result.approval_case.id}</p>` : ""}
  `;
}

async function simulateGoal() {
  const result = await api("/api/goal/simulate", { method: "POST", body: JSON.stringify(portfolioPayload()) });
  document.getElementById("portfolioOutput").innerHTML = `
    <h3>Base plan</h3>${renderPortfolio(result.base)}
    <h3>Goal ladder</h3>${result.goal_ladder.map(x => `<div class="step"><b>${x.step}. ${x.destination}</b><span>${money(x.monthly_amount)}</span><p>${x.why}</p></div>`).join("")}
  `;
}

async function loadAnomalies() {
  setProgress(72, "Scanning transactions...");
  const result = await api("/api/anomalies");
  document.getElementById("anomalyOutput").innerHTML = `
    ${badge(`Total alerts ${result.summary.total_alerts}`, "warn")} ${badge(`High risk ${result.summary.high_risk}`, "danger")} ${badge(`Protected ${money(result.summary.protected_value)}`)}
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Merchant</th><th>Amount</th><th>Risk</th><th>Action</th></tr></thead><tbody>
      ${result.anomalies.slice(0,8).map(a => `<tr><td>${a.id}</td><td>${a.merchant}</td><td>${money(a.amount)}</td><td>${a.risk_score}</td><td>${a.recommended_action}<br><small>${a.explanation}</small></td></tr>`).join("")}
    </tbody></table></div>
  `;
  setProgress(78, "Fraud intelligence ready.");
}

async function scoreDemoTransaction() {
  const result = await api("/api/transactions/risk-score", { method: "POST", body: JSON.stringify({}) });
  document.getElementById("anomalyOutput").innerHTML = `
    ${badge(`Risk ${result.risk.risk_score}`, result.risk.risk_level === "high" ? "danger" : "warn")} ${badge(result.risk.recommended_action)}
    <p>${result.risk.explanation}</p>
    <p><b>Audit:</b> ${result.audit_event.decision_hash.slice(0, 24)}...</p>
  `;
}

async function askAdvisor() {
  setProgress(84, "Advisor copilot answering...");
  const payload = { question: document.getElementById("chatQuestion").value, risk_bucket: currentRiskBucket };
  const result = await api("/api/advisor/chat", { method: "POST", body: JSON.stringify(payload) });
  document.getElementById("chatOutput").innerHTML = `
    ${badge(`Confidence ${result.confidence}`)} ${badge(result.human_review_recommended ? "Human review" : "Auto support", result.human_review_recommended ? "warn" : "")}
    <p>${result.answer}</p>
    <h3>Next actions</h3>${htmlList(result.next_best_actions || [])}
    <p><b>Guardrail:</b> ${result.guardrail}</p>
  `;
  setProgress(88, "Advisor answer ready.");
}

async function toggleKillSwitch(enabled) {
  const reason = enabled ? "Demo model restored after governance test." : "Judge demo: prove instant AI pause and human fallback.";
  const result = await api("/api/kill-switch", { method: "POST", body: JSON.stringify({ enabled, reason }) });
  renderModelStatus(result.model_state);
  setProgress(enabled ? 15 : 92, enabled ? "AI model enabled." : "AI paused by kill switch.");
}

async function loadGovernance() {
  const [cards, val, drift, fair, score] = await Promise.all([
    api("/api/governance/model-cards"), api("/api/governance/validation"), api("/api/governance/drift"), api("/api/governance/fairness"), api("/api/governance/scorecard")
  ]);
  document.getElementById("governanceOutput").innerHTML = `
    ${badge(`Score ${score.score}`)} ${badge(val.overall_status)} ${badge(`Drift ${drift.status}`)}
    <h3>Controls</h3>${htmlList(Object.entries(score.controls).map(([k,v]) => `${k}: ${v}`))}
    <h3>Model registry</h3>${htmlList(cards.models.map(m => `${m.model_id}: ${m.purpose} — ${m.status}`))}
    <h3>Fairness</h3><p>${fair.explanation}</p>
  `;
}

async function loadAudit() {
  const result = await api("/api/audit");
  document.getElementById("auditOutput").innerHTML = `
    <div class="table-wrap"><table><thead><tr><th>Action</th><th>Actor</th><th>Severity</th><th>Hash</th></tr></thead><tbody>
      ${result.events.slice(0,10).map(e => `<tr><td>${e.action}</td><td>${e.actor}</td><td>${e.severity}</td><td><code>${e.decision_hash.slice(0, 18)}...</code></td></tr>`).join("")}
    </tbody></table></div>
  `;
}

async function verifyAudit() {
  const result = await api("/api/audit/verify");
  document.getElementById("auditOutput").innerHTML = `
    ${badge(result.verified ? "Verified" : "Broken", result.verified ? "" : "danger")} ${badge(`${result.events_checked} events checked`)}
    <p><b>Last hash:</b> <code>${String(result.last_hash || "").slice(0, 36)}...</code></p>
    <p>${result.control}</p>
  `;
}

async function loadSandbox() {
  const [status, contracts, metrics] = await Promise.all([api("/api/sandbox/status"), api("/api/sandbox/data-contracts"), api("/api/metrics")]);
  document.getElementById("sandboxOutput").innerHTML = `
    ${badge(status.mode)} ${badge(`${metrics.technical.api_count} APIs`)} ${badge(`Tests ${metrics.technical.test_count}`)}
    <h3>Connectors</h3>${htmlList(status.connectors.map(c => `${c.name}: ${c.status}, ${c.latency_ms}ms`))}
    <h3>Production path</h3>${htmlList(status.production_path)}
    <h3>Data contracts</h3>${htmlList(contracts.contracts.map(c => `${c.entity}: ${c.required_fields.join(", ")}`))}
  `;
}

function startLiveStream() {
  const feed = document.getElementById("liveFeed");
  if (liveSource) liveSource.close();
  feed.innerHTML = "";
  liveSource = new EventSource("/api/realtime/events");
  liveSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setProgress(data.progress, `Live tick ${data.tick}: ${data.transaction.merchant} ${money(data.transaction.amount)}`);
    const item = document.createElement("div");
    item.className = "feed-item";
    item.innerHTML = `<b>Tick ${data.tick}</b> ${data.transaction.merchant} • ${money(data.transaction.amount)}<br><span>${data.anomaly_summary.total_alerts} alerts • model ${data.model_state.enabled ? "enabled" : "paused"}</span>`;
    feed.prepend(item);
    while (feed.children.length > 8) feed.removeChild(feed.lastChild);
  };
  liveSource.onerror = () => {
    liveSource.close();
    liveSource = null;
  };
}

function runJudgeDemo() {
  const feed = document.getElementById("liveFeed");
  feed.innerHTML = "";
  const src = new EventSource("/api/realtime/demo-run");
  src.onmessage = async (event) => {
    const step = JSON.parse(event.data);
    setProgress(step.progress, step.name);
    const item = document.createElement("div");
    item.className = "feed-item demo-step";
    item.innerHTML = `<b>${step.step}. ${step.name}</b><br><span>${step.proof}</span>`;
    feed.prepend(item);
    if (step.step === 2) await generateRisk();
    if (step.step === 4) await generatePortfolio();
    if (step.step === 5) await loadAnomalies();
    if (step.step === 6) await askAdvisor();
    if (step.step === 8) await verifyAudit();
  };
  src.onerror = () => src.close();
}

init().catch(err => {
  document.body.insertAdjacentHTML("afterbegin", `<div class="error">${err.message}</div>`);
});
