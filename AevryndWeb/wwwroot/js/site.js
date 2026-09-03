(() => {
  let csrf = "";
  async function token() { if (!csrf) csrf = (await (await fetch("/api/auth/csrf", { credentials: "same-origin" })).json()).token; return csrf; }
  async function post(url, body) { const response = await fetch(url, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", "X-CSRF-TOKEN": await token() }, body: JSON.stringify(body) }); return { response, data: await response.json().catch(() => ({})) }; }
  const send = document.querySelector("#sendButton"), status = document.querySelector("#status");
  send?.addEventListener("click", async () => { const email = document.querySelector("#email"); if (!email.reportValidity()) return; send.disabled = true; try { const result = await post("/api/auth/request-code", { email: email.value }); status.textContent = result.data.message; document.querySelector("#verifyBox").hidden = false; setTimeout(() => send.disabled = false, 60000); } catch { status.textContent = "暫時無法連線。"; send.disabled = false; } });
  document.querySelector("#loginForm")?.addEventListener("submit", async event => { event.preventDefault(); const result = await post("/api/auth/verify", { email: document.querySelector("#email").value, code: document.querySelector("#code").value.toUpperCase() }); if (result.response.ok) location.assign(result.data.redirect); else status.textContent = result.data.message; });
  document.querySelector("#logoutButton")?.addEventListener("click", async () => { await post("/api/auth/logout", {}); location.assign("/"); });
})();
