let currentRiskBucket = "Balanced";

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
  return `<ul>${items.map(x => `<li>${x}</li>`).join("")}</ul>`;
}

async function init() {
  const state = await api("/api/demo/state");
  document.getElementById("modelStatus").innerHTML = state.model_state.enabled
    ? `<span class="status-good">AI model enabled</span> • ${state.model_state.version}`
    : `<span class="status-danger">AI model paused</span>`;
  document.getElementById("kpis").innerHTML = `
    <div class="kpi"><span>Time to Recommendation</span><strong>${state.judge_metrics.time_to_first_recommendation_sec}s</strong></div>
    <div class="kpi"><span>Explainability</span><strong>${state.judge_metrics.explainability_coverage_pct}%</strong></div>
    <div class="kpi"><span>Anomaly Alerts</span><strong>${state.anomaly_count}</strong></div>
    <div class="kpi"><span>Audit Hashing</span><strong>${state.judge_metrics.audit_hashing ? "ON" : "OFF"}</strong></div>
  `;
}

async function generateRisk() {
  try {
    const payload = getFormData("riskForm");
    payload.goal_priority = "wealth_growth";
    const result = await api("/api/risk/profile", { method: "POST", body: JSON.stringify(payload) });
    currentRiskBucket = result.risk_bucket;
    document.getElementById("portfolioBucket").value = currentRiskBucket;
    document.getElementById("scoreRing").innerText = result.risk_score;
    document.getElementById("riskBucket").innerText = `${result.risk_bucket} Investor`;
    document.getElementById("riskOutput").innerHTML = `
      <span class="badge">Risk Score: ${result.risk_score}/100</span>
      <span class="badge">Bucket: ${result.risk_bucket}</span>
      <h3>Why this score?</h3>${htmlList(result.top_factors)}
      <h3>Suitability guardrails</h3>${htmlList(result.guardrails)}
      <p><b>Compliance note:</b> ${result.compliance_note}</p>
    `;
    return result;
  } catch (e) {
    document.getElementById("riskOutput").innerHTML = `<p class="status-danger">${e.message}</p>`;
  }
}

async function generatePortfolio() {
  try {
    const payload = {
      risk_bucket: document.getElementById("portfolioBucket").value || currentRiskBucket,
      monthly_sip: Number(document.getElementById("sip").value),
      goal_amount: Number(document.getElementById("goal").value),
      horizon_years: Number(document.getElementById("portfolioHorizon").value),
    };
    const result = await api("/api/portfolio/recommend", { method: "POST", body: JSON.stringify(payload) });
    const rows = result.allocation.map(item => `
      <tr><td>${item.asset}</td><td>${item.allocation_pct}%</td><td>₹${item.monthly_amount.toLocaleString("en-IN")}</td><td>${item.why}</td></tr>
    `).join("");
    document.getElementById("portfolioOutput").innerHTML = `
      <span class="badge">Expected Return: ${result.expected_annual_return}%</span>
      <span class="badge">Volatility: ${result.estimated_portfolio_volatility}%</span>
      <span class="badge">Projected: ₹${result.projected_value.toLocaleString("en-IN")}</span>
      <span class="badge">Required SIP: ₹${result.required_sip_for_goal.toLocaleString("en-IN")}</span>
      <table><thead><tr><th>Asset</th><th>Allocation</th><th>Monthly</th><th>Reason</th></tr></thead><tbody>${rows}</tbody></table>
      <p><b>Rule:</b> ${result.rebalancing_rule}</p>
      <p><b>Human review required:</b> ${result.human_review_required ? "Yes" : "No"}</p>
    `;
    return result;
  } catch (e) {
    document.getElementById("portfolioOutput").innerHTML = `<p class="status-danger">${e.message}</p>`;
  }
}

async function loadAnomalies() {
  const result = await api("/api/anomalies");
  const rows = result.anomalies.slice(0, 12).map(a => `
    <tr><td>${a.id}</td><td>${a.date}</td><td>${a.merchant}</td><td>${a.category}</td><td>₹${Number(a.amount).toLocaleString("en-IN")}</td><td class="status-warn">${a.risk_score}</td><td>${a.explanation}</td></tr>
  `).join("");
  document.getElementById("anomalyOutput").innerHTML = `<table><thead><tr><th>ID</th><th>Date</th><th>Merchant</th><th>Category</th><th>Amount</th><th>Risk</th><th>Why flagged</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function askAdvisor() {
  const result = await api("/api/advisor/chat", { method: "POST", body: JSON.stringify({ question: document.getElementById("chatQuestion").value, risk_bucket: currentRiskBucket }) });
  document.getElementById("chatOutput").innerHTML = `
    <p>${result.answer}</p>
    <span class="badge">Confidence: ${Math.round(result.confidence * 100)}%</span>
    <span class="badge">Guardrail: ${result.guardrail}</span>
  `;
}

async function loadAudit() {
  const result = await api("/api/audit");
  const rows = result.events.slice(0, 25).map(e => `
    <tr><td>${new Date(e.ts * 1000).toLocaleString()}</td><td>${e.actor}</td><td>${e.action}</td><td>${e.decision_hash.slice(0, 18)}...</td></tr>
  `).join("");
  document.getElementById("auditOutput").innerHTML = `<table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>SHA-256 Decision Hash</th></tr></thead><tbody>${rows}</tbody></table>`;
}

async function toggleKillSwitch(enabled) {
  try {
    await api("/api/kill-switch", { method: "POST", body: JSON.stringify({ enabled, reason: enabled ? "Demo model enabled by presenter" : "Judge demo of model governance kill switch" }) });
    await init();
  } catch (e) { alert(e.message); }
}

async function runFullDemo() {
  await init();
  await generateRisk();
  await generatePortfolio();
  await loadAnomalies();
  await askAdvisor();
  await loadAudit();
}

init().catch(console.error);
