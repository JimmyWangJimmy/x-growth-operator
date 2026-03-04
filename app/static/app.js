const byId = (id) => document.getElementById(id);
let currentActionId = "";

function setStatus(message, kind = "info") {
  const target = byId("statusBanner");
  if (!target) return;
  target.textContent = message;
  target.style.color = kind === "error" ? "#8c2c1a" : kind === "success" ? "#2c5a46" : "";
}

async function postJson(path, payload = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok || body.ok === false) {
    throw new Error(body.error || `Request failed: ${response.status}`);
  }
  return body;
}

function renderKeyValueBlock(target, entries) {
  if (!entries.length) {
    target.innerHTML = '<div class="empty-state">No data available.</div>';
    return;
  }
  target.innerHTML = entries
    .map(
      ([label, value]) => `
        <div class="meta-item">
          <span class="meta-label">${label}</span>
          <span class="meta-value">${value}</span>
        </div>
      `
    )
    .join("");
}

function renderTagList(values) {
  if (!values || !values.length) return '<span class="muted">None</span>';
  return values.map((value) => `<span class="tag">${value}</span>`).join("");
}

function renderMission(mission) {
  byId("missionName").textContent = mission?.name || "No mission loaded";
  renderKeyValueBlock(byId("missionMeta"), [
    ["Goal", mission?.goal || "None"],
    ["Voice", mission?.voice || "None"],
    ["Risk", mission?.risk_tolerance || "None"],
    ["Topics", renderTagList(mission?.primary_topics || [])],
    ["Keywords", renderTagList(mission?.watch_keywords || [])],
    ["Accounts", renderTagList(mission?.watch_accounts || [])],
    ["CTA", mission?.cta || "None"],
  ]);
}

function renderPlan(plan) {
  const items = plan?.items || [];
  byId("planCount").textContent = `${items.length} actions`;
  const target = byId("planList");
  if (!items.length) {
    target.className = "list-block empty-state";
    target.textContent = "No action plan found.";
    return;
  }
  target.className = "list-block";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item-head">
            <strong>${item.action_type}</strong>
            <span class="chip small">${item.priority}</span>
          </div>
          <p>${item.target_account || "unknown"} · score ${item.score} · readiness ${item.interaction_readiness}</p>
          <p class="muted">${item.why_now || ""}</p>
          <div class="list-item-actions">
            <button class="secondary-button draft-button" data-opportunity-id="${item.opportunity_id}">Draft</button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderCurrentAction(action) {
  currentActionId = action?.id || "";
  byId("actionType").textContent = action?.action_type || "None";
  const target = byId("currentAction");
  const disabled = !currentActionId;
  byId("preflightButton").disabled = disabled;
  byId("dryRunButton").disabled = disabled;
  byId("executeButton").disabled = disabled;
  if (!action || !action.id) {
    target.className = "action-card empty-state";
    target.textContent = "No proposed action found.";
    return;
  }
  target.className = "action-card";
  target.innerHTML = `
    <p><strong>${action.action_type}</strong> · score ${action.score ?? "n/a"} · risk ${action.risk_level ?? "n/a"}</p>
    <p class="draft">${action.draft_text || "No draft text."}</p>
    <p class="muted">${action.rationale || ""}</p>
  `;
}

function renderMemory(memory) {
  const target = byId("memoryBlock");
  if (!memory || !Object.keys(memory).length) {
    target.className = "memory-grid empty-state";
    target.textContent = "No memory file found.";
    return;
  }
  target.className = "memory-grid";
  const cards = [
    ["Successful Topics", memory.successful_topics || {}],
    ["Action Types", memory.successful_action_types || {}],
    ["High Signal Accounts", memory.high_signal_accounts || {}],
    ["Avoid Accounts", memory.avoid_accounts || {}],
  ];
  target.innerHTML = cards
    .map(([title, obj]) => {
      const entries = Object.entries(obj);
      return `
        <div class="memory-card">
          <h3>${title}</h3>
          ${
            entries.length
              ? entries
                  .slice(0, 5)
                  .map(([key, value]) => `<div class="memory-row"><span>${key}</span><strong>${value}</strong></div>`)
                  .join("")
              : '<div class="muted">No signals yet.</div>'
          }
        </div>
      `;
    })
    .join("");
}

function renderOpportunities(payload) {
  const items = payload?.items || [];
  byId("opportunityCount").textContent = `${items.length} items`;
  const target = byId("opportunityList");
  if (!items.length) {
    target.className = "list-block empty-state";
    target.textContent = "No scored opportunities found.";
    return;
  }
  target.className = "list-block";
  target.innerHTML = items
    .slice(0, 6)
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item-head">
            <strong>${item.source_account || "unknown"}</strong>
            <span class="chip small">${item.recommended_action}</span>
          </div>
          <p>${item.score} · ${item.risk_level} · ${(item.algorithm_hints || {}).interaction_readiness || "unknown"}</p>
          <p class="muted">${(item.text || "").slice(0, 140)}</p>
          ${
            item.recommended_action && item.recommended_action !== "observe"
              ? `<div class="list-item-actions"><button class="secondary-button draft-button" data-opportunity-id="${item.id}">Draft</button></div>`
              : ""
          }
        </article>
      `
    )
    .join("");
}

function renderExecutions(events) {
  const items = events || [];
  byId("executionCount").textContent = `${items.length} events`;
  const target = byId("executionList");
  if (!items.length) {
    target.className = "list-block empty-state";
    target.textContent = "No executions recorded.";
    return;
  }
  target.className = "list-block";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="list-item">
          <div class="list-item-head">
            <strong>${item.action_type || "unknown"}</strong>
            <span class="chip small">${item.status}</span>
          </div>
          <p>${item.target_account || "unknown"} · ${item.executed_at || "n/a"}</p>
          <p class="muted">${(item.draft_text || "").slice(0, 140)}</p>
        </article>
      `
    )
    .join("");
}

function renderFiles(files) {
  const target = byId("fileList");
  if (!files?.length) {
    target.className = "file-list empty-state";
    target.textContent = "No generated files found.";
    return;
  }
  target.className = "file-list";
  target.innerHTML = files.map((file) => `<span class="file-pill">${file}</span>`).join("");
}

async function loadState() {
  const response = await fetch("/api/state");
  const data = await response.json();
  renderMission(data.mission);
  renderPlan(data.action_plan);
  renderCurrentAction(data.current_action);
  renderMemory(data.memory);
  renderOpportunities(data.opportunities_scored);
  renderExecutions(data.execution_log);
  renderFiles(data.generated_files);
  wireActionButtons();
}

function wireActionButtons() {
  document.querySelectorAll(".draft-button").forEach((button) => {
    button.onclick = async () => {
      const opportunityId = button.dataset.opportunityId;
      if (!opportunityId) return;
      try {
        setStatus(`Drafting action for ${opportunityId}...`);
        await postJson("/api/draft", { opportunity_id: opportunityId });
        await loadState();
        setStatus(`Draft created from ${opportunityId}.`, "success");
      } catch (error) {
        console.error(error);
        setStatus(error.message, "error");
      }
    };
  });
}

byId("refreshButton").addEventListener("click", async () => {
  try {
    setStatus("Refreshing state...");
    await loadState();
    setStatus("State refreshed.", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
});

byId("preflightButton").addEventListener("click", async () => {
  if (!currentActionId) return;
  try {
    setStatus("Running preflight...");
    const response = await postJson("/api/preflight", {});
    const decision = response.preflight?.decision || "unknown";
    setStatus(`Preflight decision: ${decision}.`, decision === "allow" ? "success" : "error");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
});

byId("dryRunButton").addEventListener("click", async () => {
  if (!currentActionId) return;
  try {
    setStatus("Executing dry run...");
    await postJson("/api/execute", { mode: "dry-run" });
    await loadState();
    setStatus("Dry run executed.", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
});

byId("executeButton").addEventListener("click", async () => {
  if (!currentActionId) return;
  if (!window.confirm("Execute current action live on X API?")) return;
  try {
    setStatus("Executing live action...");
    await postJson("/api/execute", { mode: "x-api" });
    await loadState();
    setStatus("Live execution completed.", "success");
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
});

loadState().catch((error) => {
  console.error(error);
  setStatus(error.message, "error");
});
