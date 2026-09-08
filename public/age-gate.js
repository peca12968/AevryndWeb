(() => {
  const gate = document.querySelector('#age-gate');
  const panel = gate?.querySelector('.age-gate-panel');
  const title = gate?.querySelector('#age-gate-title');
  const copy = gate?.querySelector('#age-gate-copy');
  const confirmButton = gate?.querySelector('[data-age-confirm]');
  const denyButton = gate?.querySelector('[data-age-deny]');
  const storageKey = 'aevrynd-age-confirmed';
  let allow;

  window.aevryndAgeGate = new Promise(resolve => { allow = resolve; });

  const enter = () => {
    document.body.classList.remove('age-pending');
    gate.hidden = true;
    allow(true);
  };

  try {
    if (sessionStorage.getItem(storageKey) === 'yes') {
      enter();
      return;
    }
  } catch {
    // The prompt still works when storage is unavailable.
  }

  confirmButton?.addEventListener('click', () => {
    try { sessionStorage.setItem(storageKey, 'yes'); } catch {}
    enter();
    document.querySelector('.skip-link')?.focus();
  });

  denyButton?.addEventListener('click', () => {
    panel.classList.add('is-denied');
    title.textContent = '此內容僅限成年人觀看';
    copy.textContent = '你目前無法進入 Aevrynd 開發歷程網站。請關閉此頁面。';
    gate.querySelector('.age-gate-actions')?.remove();
    title.focus?.();
  });

  confirmButton?.focus();
})();
