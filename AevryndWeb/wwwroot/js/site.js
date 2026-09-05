(() => {
  let csrf = "";
  let cooldownTimer = 0;
  const notify = (icon, title, message) => window.Swal?.fire({ icon, title, text: message, confirmButtonText: "知道了", buttonsStyling: false, customClass: { popup: "aevrynd-alert", confirmButton: "aevrynd-alert-button" } });
  const loading = message => window.Swal?.fire({ title: message, text: "請稍候，系統正在透過加密通道處理。", allowEscapeKey: false, allowOutsideClick: false, showConfirmButton: false, didOpen: () => window.Swal.showLoading(), customClass: { popup: "aevrynd-alert" } });
  const tunnelHeaders = { "ngrok-skip-browser-warning": "true" };
  async function token() { if (!csrf) csrf = (await (await fetch("/api/auth/csrf", { credentials: "same-origin", headers: tunnelHeaders })).json()).token; return csrf; }
  async function post(url, body) { const response = await fetch(url, { method: "POST", credentials: "same-origin", headers: { ...tunnelHeaders, "Content-Type": "application/json", "X-CSRF-TOKEN": await token() }, body: JSON.stringify(body) }); return { response, data: await response.json().catch(() => ({})) }; }
  const send = document.querySelector("#sendButton"), status = document.querySelector("#status");
  function startCooldown() { let remaining = 60; const label = send.querySelector("span"); window.clearInterval(cooldownTimer); cooldownTimer = window.setInterval(() => { remaining -= 1; label.textContent = remaining > 0 ? `${remaining} 秒後可重新傳送` : "重新傳送驗證碼"; if (remaining <= 0) { window.clearInterval(cooldownTimer); send.disabled = false; } }, 1000); }
  send?.addEventListener("click", async () => { const email = document.querySelector("#email"); if (!email.checkValidity()) { email.reportValidity(); notify("warning", "請檢查電子信箱", "請輸入有效且已授權的電子信箱地址。"); return; } const label = send.querySelector("span"); send.disabled = true; send.classList.add("is-loading"); label.textContent = "正在建立安全郵件…"; status.textContent = ""; loading("正在傳送驗證碼"); try { const result = await post("/api/auth/request-code", { email: email.value }); const message = result.data.message || "驗證碼已傳送，請查看信箱。"; status.textContent = message; status.dataset.kind = result.response.ok ? "success" : "error"; window.Swal?.close(); if (!result.response.ok) { send.disabled = false; label.textContent = "重新傳送驗證碼"; notify("error", "無法傳送", message); return; } document.querySelector("#verifyBox").hidden = false; document.querySelector("#code").focus(); startCooldown(); notify("success", "驗證碼已寄出", `${message} 60 秒後可重新傳送。`); } catch { const message = "暫時無法連線，請稍後再試。"; window.Swal?.close(); status.textContent = message; status.dataset.kind = "error"; send.disabled = false; label.textContent = "重新傳送驗證碼"; notify("error", "連線失敗", message); } finally { send.classList.remove("is-loading"); } });
  document.querySelector("#loginForm")?.addEventListener("submit", async event => { event.preventDefault(); const code = document.querySelector("#code"); if (!code.checkValidity()) { code.reportValidity(); notify("warning", "驗證碼格式不符", "請輸入郵件中的 8 位英數驗證碼。"); return; } const submit = event.currentTarget.querySelector('[type="submit"]'); submit.disabled = true; submit.classList.add("is-loading"); status.textContent = "正在驗證安全代碼…"; status.dataset.kind = "neutral"; loading("正在驗證身分"); try { const result = await post("/api/auth/verify", { email: document.querySelector("#email").value, code: code.value.toUpperCase() }); window.Swal?.close(); if (result.response.ok) { await notify("success", "驗證成功", "即將進入 Aevrynd AI 控制中心。"); location.assign(result.data.redirect); } else { status.textContent = result.data.message; status.dataset.kind = "error"; notify("error", "登入失敗", result.data.message || "驗證碼無效或已過期。"); } } catch { const message = "驗證服務暫時無法連線。"; window.Swal?.close(); status.textContent = message; status.dataset.kind = "error"; notify("error", "連線失敗", message); } finally { submit.disabled = false; submit.classList.remove("is-loading"); } });
  document.querySelector("#logoutButton")?.addEventListener("click", async () => { await post("/api/auth/logout", {}); location.assign("/"); });
})();

(() => {
  const root = document.querySelector("[data-operations-root]");
  if (!root) return;
  const tunnelHeaders = { "ngrok-skip-browser-warning": "true" };
  const source = root.querySelector("[data-operations-source]");
  const sourceStatus = root.querySelector("[data-source-status]");
  const snapshotTime = root.querySelector("[data-snapshot-time]");
  const pollStatus = root.querySelector("[data-poll-status]");
  const activeBody = root.querySelector("[data-active-body]");
  const historyBody = root.querySelector("[data-history-body]");
  const activeWrap = root.querySelector("[data-active-wrap]");
  const historyWrap = root.querySelector("[data-history-wrap]");
  const activeEmpty = root.querySelector("[data-active-empty]");
  const historyEmpty = root.querySelector("[data-history-empty]");
  const historyElement = root.querySelector("[data-history-table]");
  const hardwareGrid = root.querySelector("[data-hardware-grid]");
  const scheduleGrid = root.querySelector("[data-schedule-grid]");
  const scheduleStatus = root.querySelector("[data-schedule-status]");
  // 首次畫面可能仍來自瀏覽器保存的舊 HTML；立即統一狀態用語，再由即時快照接管。
  root.querySelectorAll('[data-schedule-count-state="blocked"]').forEach(value => {
    if (value.previousElementSibling) value.previousElementSibling.textContent = "等待條件";
  });
  root.querySelectorAll(".operations-badge.is-blocked").forEach(value => { value.textContent = "等待條件"; });
  let historyDataTable = null;
  const endpoint = root.dataset.snapshotUrl;
  const refreshIntervalMs = 10000;
  const requestTimeoutMs = 8000;
  const staleAfterMs = 35000;
  const remoteUnavailableAfterMs = 120000;
  let pollInFlight = false;
  let lastTrustedModel = null;
  let lastTrustedServerEpoch = null;
  let lastTrustedMonotonic = 0;
  const formatMetric = value => Number.isFinite(value) ? `${value.toFixed(1)}%` : "unavailable";
  const taipeiTime = new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
  });
  const formatTime = value => {
    if (!value) return "unavailable";
    const parsed = new Date(value);
    if (Number.isNaN(parsed.valueOf())) return "unavailable";
    const parts = Object.fromEntries(taipeiTime.formatToParts(parsed).map(part => [part.type, part.value]));
    return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second} 台北時間 (UTC+8)`;
  };
  const appendCell = (row, label, value) => {
    const cell = document.createElement("td"); cell.dataset.label = label; cell.textContent = value; row.append(cell); return cell;
  };
  const hardwareValue = value => value || "等待實測";
  const hardwareStatus = item => {
    const fields = [item.cpu, item.ram, item.gpu, item.motherboard, item.os];
    const hasAny = fields.some(value => typeof value === "string" && value.trim()) || (Array.isArray(item.storage) && item.storage.some(value => typeof value === "string" && value.trim()));
    const complete = fields.every(value => typeof value === "string" && value.trim()) && Array.isArray(item.storage) && item.storage.some(value => typeof value === "string" && value.trim());
    if (item.hardwareStatus !== "verified" && item.hardwareStatus !== "partial") return { value: "pending", label: "待採樣", css: "is-unavailable" };
    return item.hardwareStatus === "verified" && complete ? { value: "verified", label: "已驗證", css: "is-current" } : hasAny ? { value: "partial", label: "部分已驗證", css: "is-stale" } : { value: "pending", label: "待採樣", css: "is-unavailable" };
  };
  const badge = (value, stale = false) => {
    const terminal = value === "failed" ? "is-failed" : value === "blocked" ? "is-blocked" : value === "cancelled" ? "is-cancelled" : stale ? "is-stale" : "is-current";
    const span = document.createElement("span"); span.className = `operations-badge ${terminal}`;
    const labels = { working: "進行中", completed: "已完成", failed: "未通過", blocked: "等待條件", cancelled: "已停止" };
    const label = labels[value] || "狀態待確認";
    span.textContent = stale ? `${label} · 資料待更新` : label; return span;
  };
  const renderWork = (items, body, wrap, empty, sourceAvailable, sourceMessage, history, catalog = []) => {
    if (!body || !wrap || !empty) return;
    const preservedSearch = historyDataTable?.search() || "";
    const preservedPage = historyDataTable?.page() || 0;
    if (history && historyDataTable) historyDataTable.clear(); else body.replaceChildren();
    wrap.hidden = items.length === 0; empty.hidden = items.length !== 0;
    if (!items.length) {
      empty.textContent = sourceAvailable
        ? history ? "尚未累積歷程；工作來源必須提供明確結束狀態才會列入。" : "目前沒有來源宣告中的工作；請確認各節點 Codex status publisher 正在更新。"
        : `${history ? "無法讀取歷程" : "無法讀取工作"}：${sourceMessage}`;
      if (history && historyDataTable) historyDataTable.draw(false);
      return;
    }
    items.forEach(item => {
      const row = document.createElement("tr");
      const title = [...catalog].sort((a, b) => Date.parse(b.assignedAt) - Date.parse(a.assignedAt)).find(task => task.id === item.name && ({ local: "本機", taichung: "台中", taoyuan: "桃園" })[task.nodeId] === item.host && Date.parse(item.startedAt) >= Date.parse(task.assignedAt))?.title;
      const nameCell = appendCell(row, "任務", title || item.name);
      if (title && title !== item.name) {
        const detail = document.createElement("details"); const label = document.createElement("summary"); label.textContent = "任務識別";
        const identity = document.createElement("small"); identity.textContent = item.name; detail.append(label, identity); nameCell.append(detail);
      }
      appendCell(row, history ? "類型／主機" : "類型", history ? `${item.type} · ${item.host}` : item.type);
      if (!history) appendCell(row, "主機", item.host);
      if (history) { const timeline = appendCell(row, "時間軸", `開始 ${formatTime(item.startedAt)}\n更新 ${formatTime(item.updatedAt)}\n結束 ${formatTime(item.endedAt)}`); timeline.className = "operations-timeline"; timeline.dataset.order = String(new Date(item.startedAt).valueOf()); }
      else { appendCell(row, "開始", formatTime(item.startedAt)); appendCell(row, "最近更新", formatTime(item.updatedAt)); }
      const statusCell = appendCell(row, history ? "結果" : "狀態", ""); statusCell.append(badge(item.status, !history && item.stale));
      if (history) appendCell(row, "證據摘要", item.evidenceSummary || "來源未提供證據摘要。");
      if (history && historyDataTable) historyDataTable.row.add(row); else body.append(row);
    });
    if (history && historyDataTable) {
      historyDataTable.search(preservedSearch).draw(false);
      const lastPage = Math.max(0, historyDataTable.page.info().pages - 1);
      historyDataTable.page(Math.min(preservedPage, lastPage)).draw("page");
    }
  };
  const stateLabel = { queued: "等待中", acknowledged: "已接單", running: "執行中", blocked: "等待條件", unconfirmed: "狀態待確認" };
  const renderSchedule = schedule => {
    if (!scheduleGrid) return;
    const tasks = Array.isArray(schedule?.tasks) ? schedule.tasks : [];
    if (scheduleStatus) {
      const observed = formatTime(schedule?.observedAt);
      scheduleStatus.textContent = schedule?.sourceAvailable
        ? (schedule.stale ? "排程資料已過期（" + observed + "）；不推測任務已停止。" : "排程來源已驗證，觀測於 " + observed + "。")
        : "目前沒有可驗證的排程來源。";
      if (schedule?.sourceAvailable && schedule.verifiedAt) scheduleStatus.textContent += " 來源核對：" + formatTime(schedule.verifiedAt) + "；工作時間依實際事件保留。";
      if (schedule?.diagnostic) scheduleStatus.textContent += " " + schedule.diagnostic;
    }
    const byNode = new Map(["local", "taichung", "taoyuan"].map(id => [id, tasks.filter(task => task.nodeId === id)]));
    scheduleGrid.querySelectorAll("[data-schedule-node]").forEach(card => {
      const nodeTasks = byNode.get(card.dataset.scheduleNode) || [];
      const openIds = new Set(Array.from(card.querySelectorAll("[data-schedule-task-id][open]")).map(item => item.dataset.scheduleTaskId));
      const count = card.querySelector("[data-schedule-count]"); if (count) count.textContent = String(nodeTasks.length);
      card.querySelectorAll("[data-schedule-count-state]").forEach(element => { element.textContent = String(nodeTasks.filter(task => task.state === element.dataset.scheduleCountState).length); });
      const list = card.querySelector("[data-schedule-list]"); const empty = card.querySelector("[data-schedule-empty]");
      if (!list || !empty) return;
      const scrollTop = list.scrollTop;
      const hint = card.querySelector("[data-schedule-scroll-hint]");
      if (hint) hint.textContent = "全部 " + nodeTasks.length + " 筆 · 清單可上下捲動，展開任務查看詳細內容。";
      list.replaceChildren(); empty.hidden = nodeTasks.length !== 0;
      nodeTasks.sort((a, b) => new Date(b.updatedAt || 0).valueOf() - new Date(a.updatedAt || 0).valueOf()).forEach(task => {
        const details = document.createElement("details"); details.className = "operations-schedule-task";
        const summary = document.createElement("summary"); const title = document.createElement("span"); title.textContent = task.title || "未命名工作";
        const updated = document.createElement("small"); updated.textContent = "最近更新：" + formatTime(task.updatedAt); title.append(document.createElement("br"), updated);
        const state = document.createElement("span"); state.className = "operations-badge is-" + (task.state || "unconfirmed"); state.textContent = stateLabel[task.state] || "狀態待確認";
        summary.append(title, state);
        const detail = document.createElement("div"); detail.className = "operations-schedule-detail";
        const add = (label, value) => { const paragraph = document.createElement("p"); paragraph.textContent = label + (value || "未提供"); detail.append(paragraph); };
        const dependencyText = Array.isArray(task.dependsOn) && task.dependsOn.length
          ? task.dependsOn.map(id => { const dependency = (schedule.catalog || tasks).find(candidate => candidate.id === id); return dependency?.title || "先前任務（" + id + "）"; }).join("、")
          : "無";
        add("", task.description); add("原因：", (task.reason || "").replaceAll("受阻", "正在等待必要條件")); add("依賴：", dependencyText);
        add("指派：", formatTime(task.assignedAt) + " · 更新：" + formatTime(task.updatedAt));
        const evidence = document.createElement("small"); evidence.textContent = "任務識別：" + (task.id || "未提供") + " · 證據：" + (task.evidence || "未提供"); detail.append(evidence);
        details.dataset.scheduleTaskId = task.instanceId || task.id || ""; if (openIds.has(details.dataset.scheduleTaskId)) details.open = true;
        details.append(summary, detail); list.append(details);
      });
      list.scrollTop = scrollTop;
    });
  };
  const renderNode = node => {
    const card = root.querySelector(`[data-node-id="${node.id}"]`); if (!card) return;
    card.querySelector('[data-node-metric="cpu"]').textContent = formatMetric(node.cpuPercent);
    card.querySelector('[data-node-metric="ram"]').textContent = formatMetric(node.ramPercent);
    card.querySelector('[data-node-metric="gpu"]').textContent = formatMetric(node.gpuPercent);
    const availability = card.querySelector("[data-node-availability]"); availability.textContent = node.availability;
    availability.className = `operations-badge is-${node.availability}`;
    const sampled = card.querySelector("[data-node-sampled]"); sampled.textContent = formatTime(node.sampledAt); sampled.dateTime = node.sampledAt || "";
    card.querySelector("[data-node-diagnostic]").textContent = node.diagnostic;
  };
  const render = model => {
    source.classList.toggle("is-available", model.sourceAvailable); source.classList.toggle("is-unavailable", !model.sourceAvailable);
    sourceStatus.textContent = model.sourceStatus; snapshotTime.textContent = formatTime(model.snapshotAt); snapshotTime.dateTime = model.snapshotAt || "";
    model.nodes.forEach(renderNode);
    model.hardware?.forEach(item => {
      const card = hardwareGrid?.querySelector(`[data-hardware-id="${item.id}"]`); if (!card) return;
      const resolvedStatus = hardwareStatus(item); const status = card.querySelector("[data-hardware-status]"); status.textContent = resolvedStatus.label; status.dataset.hardwareDeclaredStatus = resolvedStatus.value; status.className = `operations-badge ${resolvedStatus.css}`;
      for (const field of ["model", "reasoning", "role", "cpu", "ram", "gpu", "motherboard", "os", "modelSource", "source"]) { const element = card.querySelector(`[data-hardware-field="${field}"]`); if (element) element.textContent = hardwareValue(item[field]); }
      const storage = card.querySelector('[data-hardware-field="storage"]'); if (storage) storage.textContent = item.storage?.length ? item.storage.join("；") : "等待實測";
      const sampled = card.querySelector('[data-hardware-field="sampledAt"]'); if (sampled) { sampled.textContent = formatTime(item.sampledAt); sampled.dateTime = item.sampledAt || ""; }
    });
    renderSchedule(model.schedule);
    renderWork(model.activeWork, activeBody, activeWrap, activeEmpty, model.sourceAvailable, model.sourceStatus, false, model.schedule?.catalog || model.schedule?.tasks || []);
    renderWork(model.history.filter(item => ["completed", "failed"].includes(item.status) && item.endedAt), historyBody, historyWrap, historyEmpty, model.sourceAvailable, model.sourceStatus, true, model.schedule?.catalog || model.schedule?.tasks || []);
  };
  const validDate = value => value == null || Number.isFinite(Date.parse(value));
  const validMetric = value => value == null || (Number.isFinite(value) && value >= 0 && value <= 100);
  const validWork = item => item && typeof item === "object" && typeof item.name === "string" && typeof item.type === "string" &&
    typeof item.host === "string" && typeof item.status === "string" && Number.isFinite(Date.parse(item.startedAt)) &&
    validDate(item.updatedAt) && validDate(item.endedAt);
  const knownNodeIds = ["local", "taichung", "taoyuan"];
  const validHardware = item => item && typeof item === "object" && knownNodeIds.includes(item.id) && typeof item.name === "string" &&
    typeof item.model === "string" && typeof item.reasoning === "string" && typeof item.role === "string" &&
    typeof item.hardwareStatus === "string" && validDate(item.sampledAt) && Array.isArray(item.storage);
  const validScheduleTask = item => item && typeof item === "object" && typeof item.id === "string" && knownNodeIds.includes(item.nodeId) &&
    typeof item.title === "string" && typeof item.description === "string" && typeof item.state === "string" &&
    typeof item.reason === "string" && Array.isArray(item.dependsOn) && Number.isFinite(Date.parse(item.assignedAt)) &&
    Number.isFinite(Date.parse(item.updatedAt)) && typeof item.evidence === "string";
  const validModel = model => {
    if (!model || typeof model !== "object" || typeof model.sourceAvailable !== "boolean" || typeof model.sourceStatus !== "string" ||
        (model.sourceAvailable ? !Number.isFinite(Date.parse(model.snapshotAt)) : !validDate(model.snapshotAt)) ||
        !Array.isArray(model.nodes) || !Array.isArray(model.activeWork) || !Array.isArray(model.history) ||
        !model.activeWork.every(validWork) || !model.history.every(validWork) ||
        (model.hardware != null && (!Array.isArray(model.hardware) || !model.hardware.every(validHardware))) ||
        (model.schedule != null && (typeof model.schedule !== "object" || typeof model.schedule.sourceAvailable !== "boolean" ||
          typeof model.schedule.stale !== "boolean" || !validDate(model.schedule.observedAt) || !validDate(model.schedule.verifiedAt) || !Array.isArray(model.schedule.tasks) ||
          !model.schedule.tasks.every(validScheduleTask) ||
          (model.schedule.catalog != null && (!Array.isArray(model.schedule.catalog) || !model.schedule.catalog.every(validScheduleTask)))))) return false;
    const ids = model.nodes.map(node => node?.id);
    return ids.length === knownNodeIds.length && new Set(ids).size === knownNodeIds.length && knownNodeIds.every(id => ids.includes(id)) &&
      model.nodes.every(node => {
        if (!node || typeof node !== "object" || typeof node.name !== "string" || typeof node.stale !== "boolean" ||
            !validMetric(node.cpuPercent) || !validMetric(node.ramPercent) || !validMetric(node.gpuPercent) ||
            !validDate(node.sampledAt) || typeof node.diagnostic !== "string" || !["current", "stale", "unavailable"].includes(node.availability)) return false;
        const hasMetric = [node.cpuPercent, node.ramPercent, node.gpuPercent].some(value => value != null);
        return node.availability === "unavailable"
          ? !hasMetric && node.stale
          : Number.isFinite(Date.parse(node.sampledAt)) && hasMetric && node.stale === (node.availability === "stale");
      });
  };
  const trustedResponseEpoch = (response, model) => {
    const value = response.headers?.get?.("date");
    const epoch = Date.parse(value || "");
    if (!Number.isFinite(epoch)) return null;
    const payloadTimes = [model.snapshotAt, ...model.nodes.map(node => node.sampledAt)].map(value => Date.parse(value || "")).filter(Number.isFinite);
    const latestPayloadTime = payloadTimes.length ? Math.max(...payloadTimes) : Number.NEGATIVE_INFINITY;
    return latestPayloadTime <= epoch + 60000 ? epoch : null;
  };
  const unavailableNode = (node, diagnostic) => ({ ...node, cpuPercent: null, ramPercent: null, gpuPercent: null, availability: "unavailable", diagnostic });
  const disconnectedNode = (node, effectiveServerEpoch) => {
    if (node.availability === "unavailable") return node;
    if (!Number.isFinite(effectiveServerEpoch)) {
      return node.availability === "current"
        ? unavailableNode(node, "連線中斷且伺服器時間來源無法驗證；已隱藏最後量測值，避免誤認為目前狀態。")
        : node;
    }
    const sampledEpoch = Date.parse(node.sampledAt || "");
    if (!Number.isFinite(sampledEpoch)) return unavailableNode(node, "連線中斷且採樣時間無效；已隱藏最後量測值，避免誤認為可用。");
    const age = effectiveServerEpoch - sampledEpoch;
    if (node.id !== "local" && age > remoteUnavailableAfterMs)
      return unavailableNode(node, "連線中斷；遠端採樣已超過兩分鐘，已隱藏最後量測值且不視為可用。");
    if (age > staleAfterMs && node.availability === "current")
      return { ...node, availability: "stale", diagnostic: "連線中斷；採樣已超過 35 秒，保留最後實測值且不進行推估。" };
    return node;
  };
  const markServerRenderedCurrentUnavailable = () => {
    root.querySelectorAll("[data-node-id]").forEach(card => {
      const availability = card.querySelector("[data-node-availability]");
      if (!availability || availability.textContent !== "current") return;
      availability.textContent = "unavailable";
      availability.className = "operations-badge is-unavailable";
      for (const metric of ["cpu", "ram", "gpu"]) {
        const element = card.querySelector(`[data-node-metric="${metric}"]`);
        if (element) element.textContent = "unavailable";
      }
      const diagnostic = card.querySelector("[data-node-diagnostic]");
      if (diagnostic) diagnostic.textContent = "尚未取得可驗證的更新；已隱藏伺服器首次量測值，避免誤認為目前狀態。";
    });
  };
  const markDisconnected = message => {
    source.classList.remove("is-available"); source.classList.add("is-unavailable");
    sourceStatus.textContent = message;
    if (!lastTrustedModel) { markServerRenderedCurrentUnavailable(); return; }
    const effectiveServerEpoch = Number.isFinite(lastTrustedServerEpoch)
      ? lastTrustedServerEpoch + Math.max(0, performance.now() - lastTrustedMonotonic)
      : null;
    lastTrustedModel.nodes.map(node => disconnectedNode(node, effectiveServerEpoch)).forEach(renderNode);
  };
  const pollingError = (kind, message) => Object.assign(new Error(message), { kind });
  const poll = async () => {
    if (pollInFlight) return;
    pollInFlight = true;
    const roundStarted = performance.now();
    const controller = new AbortController();
    let timeoutTriggered = false;
    const timeout = window.setTimeout(() => { timeoutTriggered = true; controller.abort(); }, requestTimeoutMs);
    try {
      const response = await fetch(endpoint, { credentials: "same-origin", headers: { ...tunnelHeaders, Accept: "application/json" }, cache: "no-store", signal: controller.signal });
      if (response.status === 401 || response.status === 403) throw pollingError("auth", "登入已失效，請重新登入。");
      if (!response.ok) throw pollingError("http", `更新服務回應 ${response.status}。`);
      if (response.redirected || !response.headers?.get?.("content-type")?.toLowerCase().includes("application/json"))
        throw pollingError("format", "更新回應格式錯誤，可能已被重新導向。");
      let model;
      try { model = await response.json(); }
      catch { throw pollingError("format", "更新回應不是有效的 JSON。"); }
      if (!validModel(model)) throw pollingError("format", "更新回應格式錯誤，未通過快照契約驗證。");
      const serverEpoch = trustedResponseEpoch(response, model);
      render(model);
      lastTrustedServerEpoch = serverEpoch;
      lastTrustedMonotonic = performance.now();
      lastTrustedModel = model;
      pollStatus.textContent = Number.isFinite(lastTrustedServerEpoch)
        ? `畫面更新：${formatTime(new Date(lastTrustedServerEpoch).toISOString())}`
        : "畫面已更新；伺服器時間來源未提供，斷線時不推算 freshness。";
    } catch (error) {
      const kind = timeoutTriggered || error?.name === "AbortError" ? "timeout" : error?.kind || (error instanceof TypeError ? "network" : "http");
      const message = kind === "auth" ? "登入已失效，請重新登入。"
        : kind === "timeout" ? "更新逾時；保留最後一次已驗證資料，10 秒後重試。"
          : kind === "format" ? "更新回應格式錯誤；保留最後一次已驗證資料，10 秒後重試。"
            : kind === "network" ? "網路連線失敗；保留最後一次已驗證資料，10 秒後重試。"
              : "更新服務暫時無法使用；保留最後一次已驗證資料，10 秒後重試。";
      const timeWarning = lastTrustedModel && !Number.isFinite(lastTrustedServerEpoch) ? " 伺服器時間來源無法驗證。" : "";
      pollStatus.textContent = message + timeWarning;
      markDisconnected(message + timeWarning);
    } finally {
      window.clearTimeout(timeout);
      pollInFlight = false;
      const elapsed = Math.max(0, performance.now() - roundStarted);
      window.setTimeout(poll, Math.max(0, refreshIntervalMs - elapsed));
    }
  };
  if (window.DataTable && historyElement) {
    historyDataTable = new window.DataTable(historyElement, {
      order: [[2, "desc"]], pageLength: 25,
      language: { search: "搜尋歷程：", lengthMenu: "每頁 _MENU_ 筆", info: "第 _START_–_END_ 筆，共 _TOTAL_ 筆", infoEmpty: "沒有可顯示的歷程", zeroRecords: "找不到符合的歷程", emptyTable: "尚無歷程", paginate: { first: "第一頁", last: "最後一頁", next: "下一頁", previous: "上一頁" } }
    });
  }
  window.setTimeout(poll, refreshIntervalMs);
})();
