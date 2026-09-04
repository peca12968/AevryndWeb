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
  let historyDataTable = null;
  const endpoint = root.dataset.snapshotUrl;
  const formatMetric = value => Number.isFinite(value) ? `${value.toFixed(1)}%` : "unavailable";
  const formatTime = value => {
    if (!value) return "unavailable";
    const parsed = new Date(value);
    return Number.isNaN(parsed.valueOf()) ? "unavailable" : `${parsed.toISOString().slice(0, 19).replace("T", " ")} UTC`;
  };
  const appendCell = (row, label, value) => {
    const cell = document.createElement("td"); cell.dataset.label = label; cell.textContent = value; row.append(cell); return cell;
  };
  const badge = (value, stale = false) => {
    const span = document.createElement("span"); span.className = `operations-badge ${stale ? "is-stale" : "is-current"}`;
    span.textContent = stale ? `${value} · stale` : value; return span;
  };
  const renderWork = (items, body, wrap, empty, sourceAvailable, sourceMessage, history) => {
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
      appendCell(row, "安全名稱", item.name);
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
  const render = model => {
    source.classList.toggle("is-available", model.sourceAvailable); source.classList.toggle("is-unavailable", !model.sourceAvailable);
    sourceStatus.textContent = model.sourceStatus; snapshotTime.textContent = formatTime(model.snapshotAt); snapshotTime.dateTime = model.snapshotAt || "";
    model.nodes.forEach(node => {
      const card = root.querySelector(`[data-node-id="${node.id}"]`); if (!card) return;
      card.querySelector('[data-node-metric="cpu"]').textContent = formatMetric(node.cpuPercent);
      card.querySelector('[data-node-metric="ram"]').textContent = formatMetric(node.ramPercent);
      card.querySelector('[data-node-metric="gpu"]').textContent = formatMetric(node.gpuPercent);
      const availability = card.querySelector("[data-node-availability]"); availability.textContent = node.availability;
      availability.className = `operations-badge is-${node.availability}`;
      const sampled = card.querySelector("[data-node-sampled]"); sampled.textContent = formatTime(node.sampledAt); sampled.dateTime = node.sampledAt || "";
      card.querySelector("[data-node-diagnostic]").textContent = node.diagnostic;
    });
    renderWork(model.activeWork, activeBody, activeWrap, activeEmpty, model.sourceAvailable, model.sourceStatus, false);
    renderWork(model.history, historyBody, historyWrap, historyEmpty, model.sourceAvailable, model.sourceStatus, true);
  };
  const poll = async () => {
    try {
      const response = await fetch(endpoint, { credentials: "same-origin", headers: { ...tunnelHeaders, Accept: "application/json" }, cache: "no-store" });
      if (!response.ok) throw new Error(String(response.status));
      render(await response.json()); pollStatus.textContent = `畫面更新：${formatTime(new Date().toISOString())}`;
    } catch {
      pollStatus.textContent = "更新失敗；保留最後一次已驗證資料，10 秒後重試";
      source.classList.remove("is-available"); source.classList.add("is-unavailable");
    } finally { window.setTimeout(poll, 10000); }
  };
  if (window.DataTable && historyElement) {
    historyDataTable = new window.DataTable(historyElement, {
      order: [[2, "desc"]], pageLength: 25,
      language: { search: "搜尋歷程：", lengthMenu: "每頁 _MENU_ 筆", info: "第 _START_–_END_ 筆，共 _TOTAL_ 筆", infoEmpty: "沒有可顯示的歷程", zeroRecords: "找不到符合的歷程", emptyTable: "尚無歷程", paginate: { first: "第一頁", last: "最後一頁", next: "下一頁", previous: "上一頁" } }
    });
  }
  window.setTimeout(poll, 10000);
})();
