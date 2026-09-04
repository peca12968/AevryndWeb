(() => {
  const shell = document.querySelector(".remote-shell");
  if (!shell) return;
  const frame = document.querySelector("#remoteFrame"), placeholder = document.querySelector("#framePlaceholder"), frameStatus = document.querySelector("#frameStatus");
  const workspace = document.querySelector("#remoteWorkspace"), stepUp = document.querySelector("#stepUpPanel"), stepStatus = document.querySelector("#stepUpStatus");
  let active = shell.dataset.active === "true", csrf = "", stopped = false, frameGeneration = 0, lease = null;
  let capabilities = new Set((shell.dataset.capabilities || "").split(",").filter(Boolean));
  const keyboardPanel = document.querySelector("#keyboardPanel"), keyboardCapture = document.querySelector("#keyboardCapture"), pressedCodes = new Set();
  function applyCapabilities() { if (keyboardPanel) keyboardPanel.hidden = !capabilities.has("keyboard.write"); const textPanel = document.querySelector("#textPanel"), screenPanel = document.querySelector("#screenPanel"); if (textPanel) textPanel.hidden = !capabilities.has("input.text"); if (screenPanel) screenPanel.hidden = !capabilities.has("screen.read"); }
  function showGrantLifetime(expiresAt) { const target = document.querySelector("#grantLifetime"), expires = new Date(expiresAt); if (!target || Number.isNaN(expires.valueOf())) return; shell.dataset.grantExpires = expires.toISOString(); const update = () => { const seconds = Math.max(0, Math.ceil((expires - new Date()) / 1000)); target.textContent = `網站授權剩餘 ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}（閒置 2 分鐘會提早撤銷）`; }; update(); window.setInterval(update, 1000); }
  function openLease() { if (!active || lease) return; lease = new EventSource("/RemoteConsole/lease"); lease.onopen = () => refreshFrame(); lease.onerror = () => { lease?.close(); lease = null; active = false; }; }
  async function token() { if (!csrf) csrf = (await (await fetch("/api/auth/csrf", { credentials: "same-origin", cache: "no-store" })).json()).token; return csrf; }
  async function post(url, body) { const response = await fetch(url, { method: "POST", credentials: "same-origin", cache: "no-store", headers: { "Content-Type": "application/json", "X-CSRF-TOKEN": await token() }, body: JSON.stringify(body) }); return { response, data: await response.json().catch(() => ({})) }; }

  document.querySelector("#pairingForm")?.addEventListener("submit", async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector("button"); button.disabled = true; stepStatus.textContent = "正在建立第二因素驗證…";
    try { const result = await post("/RemoteConsole/request-code", { pairingNonce: document.querySelector("#pairingNonce").value }); stepStatus.textContent = result.data.message || "請查看電子信箱。"; if (result.response.ok) document.querySelector("#controlCodeForm").hidden = false; }
    catch { stepStatus.textContent = "安全通道暫時無法使用。"; } finally { button.disabled = false; }
  });
  document.querySelector("#controlCodeForm")?.addEventListener("submit", async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector("button"); button.disabled = true;
    try { const result = await post("/RemoteConsole/verify-code", { code: document.querySelector("#controlCode").value.toUpperCase() }); stepStatus.textContent = result.data.message || "驗證失敗。"; if (result.response.ok) { active = true; capabilities = new Set(result.data.capabilities || []); applyCapabilities(); showGrantLifetime(result.data.expiresAt); stepUp.hidden = true; workspace.hidden = false; document.querySelector("#revokeRemoteGrant").hidden = false; openLease(); } }
    catch { stepStatus.textContent = "驗證服務暫時無法使用。"; } finally { button.disabled = false; }
  });
  async function refreshFrame() {
    if (!active || stopped || document.hidden || !capabilities.has("screen.read")) return;
    try {
      const response = await fetch(`/RemoteConsole/frame?t=${Date.now()}`, { credentials: "same-origin", cache: "no-store" });
      if (response.status === 401 || response.status === 403) { active = false; location.reload(); return; }
      if (response.status === 429) return;
      if (!response.ok) throw new Error();
      const blob = await response.blob(), previous = frame.src; frameGeneration = Number(response.headers.get("X-Aevrynd-Frame-Generation") || 0); frame.src = URL.createObjectURL(blob); frame.hidden = false; placeholder.hidden = true; frameStatus.textContent = `已更新 ${new Date().toLocaleTimeString()}`; if (previous.startsWith("blob:")) URL.revokeObjectURL(previous);
    } catch { frameStatus.textContent = "畫面暫時無法取得"; placeholder.textContent = "互動式桌面未就緒，系統將安全地重試。"; placeholder.hidden = false; }
  }
  document.querySelector("#remoteTextForm")?.addEventListener("submit", async event => {
    event.preventDefault(); const button = event.currentTarget.querySelector("button"), input = document.querySelector("#remoteText"), status = document.querySelector("#remoteTextStatus"); button.disabled = true;
    try { const result = await post("/RemoteConsole/text", { text: input.value }); status.textContent = result.data.message || "無法傳送文字。"; status.dataset.kind = result.response.ok ? "success" : "error"; if (result.response.ok) input.value = ""; if (result.response.status === 401 || result.response.status === 403) location.reload(); }
    catch { status.textContent = "安全通道暫時無法使用。"; status.dataset.kind = "error"; } finally { button.disabled = false; }
  });
  async function sendMouse(event, action, delta = 0) {
    if (!active || !capabilities.has("mouse.write") || !frameGeneration) return;
    const bounds = frame.getBoundingClientRect(), x = (event.clientX - bounds.left) / bounds.width, y = (event.clientY - bounds.top) / bounds.height;
    try { await post("/RemoteConsole/mouse", { frameGeneration, x, y, action, delta }); }
    catch { frameStatus.textContent = "滑鼠操作失敗，請等待新畫面"; }
  }
  frame?.addEventListener("click", event => sendMouse(event, "leftClick"));
  frame?.addEventListener("contextmenu", event => { event.preventDefault(); sendMouse(event, "rightClick"); });
  frame?.addEventListener("wheel", event => { if (!capabilities.has("mouse.write")) return; event.preventDefault(); sendMouse(event, "wheel", event.deltaY < 0 ? 120 : -120); }, { passive: false });
  async function sendKeys(strokes) { const result = await post("/RemoteConsole/keyboard", { strokes }); const keyboardStatus = document.querySelector("#keyboardStatus"); keyboardStatus.textContent = result.data.message || (result.response.ok ? "按鍵已送出。" : "按鍵被拒絕。"); if (!result.response.ok) keyboardStatus.dataset.kind = "error"; return result.response.ok; }
  keyboardCapture?.addEventListener("keydown", event => { event.preventDefault(); if (event.repeat || pressedCodes.has(event.code)) return; pressedCodes.add(event.code); sendKeys([{ code: event.code, action: "down" }]); });
  keyboardCapture?.addEventListener("keyup", event => { event.preventDefault(); pressedCodes.delete(event.code); sendKeys([{ code: event.code, action: "up" }]); });
  keyboardCapture?.addEventListener("blur", () => { if (pressedCodes.size) { const strokes = [...pressedCodes].map(code => ({ code, action: "up" })); pressedCodes.clear(); sendKeys(strokes); } });
  document.querySelector("#revokeRemoteGrant")?.addEventListener("click", async () => { await post("/RemoteConsole/revoke", {}); active = false; location.reload(); });
  applyCapabilities();
  if (shell.dataset.grantExpires) showGrantLifetime(shell.dataset.grantExpires);
  window.addEventListener("beforeunload", () => { stopped = true; lease?.close(); });
  if (active) openLease(); window.setInterval(refreshFrame, 1600);
})();
