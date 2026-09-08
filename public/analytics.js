(() => {
  const onlineNode = document.querySelector('[data-online-count]');
  const viewNode = document.querySelector('[data-view-count]');
  const heartbeatInterval = 25_000;
  const sessionKey = 'aevrynd-analytics-session';
  const viewId = crypto.randomUUID();
  let sessionId;
  let viewCounted = false;
  let timer;

  const format = value => new Intl.NumberFormat('zh-TW').format(value);

  const getSessionId = () => {
    try {
      const existing = sessionStorage.getItem(sessionKey);
      if (existing) return existing;
      const created = crypto.randomUUID();
      sessionStorage.setItem(sessionKey, created);
      return created;
    } catch {
      return crypto.randomUUID();
    }
  };

  const render = ({ online, totalViews }) => {
    onlineNode.textContent = format(online);
    viewNode.textContent = format(totalViews);
  };

  const heartbeat = async () => {
    if (document.hidden) return;

    try {
      const response = await fetch('/api/stats', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          viewId: viewCounted ? undefined : viewId,
        }),
      });

      if (!response.ok) throw new Error(`Stats request failed: ${response.status}`);
      render(await response.json());
      viewCounted = true;
    } catch {
      // Analytics failure must never block the site or the 3D editor.
    }
  };

  const start = () => {
    sessionId = getSessionId();
    heartbeat();
    timer = window.setInterval(heartbeat, heartbeatInterval);
    document.addEventListener('visibilitychange', heartbeat);
    window.addEventListener('pagehide', () => window.clearInterval(timer), { once: true });
  };

  Promise.resolve(window.aevryndAgeGate).then(start);
})();
