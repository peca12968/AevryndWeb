(() => {
  const detail = document.querySelector("#showcaseDetail");
  const detailTitle = detail?.querySelector("h2"), detailCopy = detail?.querySelector("h2 + p");
  const openDetail = target => {
    if (!detail || !target.dataset.detail) return;
    detailTitle.textContent = target.dataset.detailTitle || "證據詳情";
    detailCopy.textContent = target.dataset.detail;
    detail.setAttribute("aria-hidden", "false");
  };
  document.querySelectorAll("[data-detail]").forEach(target => {
    target.addEventListener("click", () => openDetail(target));
    target.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openDetail(target); } });
  });
  detail?.querySelector("button")?.addEventListener("click", () => detail.setAttribute("aria-hidden", "true"));

  const bindFilter = (buttonSelector, itemSelector, buttonKey, itemKey) => {
    const buttons = document.querySelectorAll(buttonSelector), items = document.querySelectorAll(itemSelector);
    buttons.forEach(button => button.addEventListener("click", () => {
      const value = button.dataset[buttonKey];
      buttons.forEach(item => item.setAttribute("aria-pressed", String(item === button)));
      items.forEach(item => { item.hidden = value !== "all" && item.dataset[itemKey] !== value; });
    }));
  };
  bindFilter("[data-release-filter]", "[data-release-state]", "releaseFilter", "releaseState");
  bindFilter("[data-stage-filter]", "[data-stage]", "stageFilter", "stage");

  const map = document.querySelector("#systemArchitectureMap"); let zoom = 1;
  const applyZoom = () => { if (map) { map.style.width = `${zoom * 100}%`; map.style.maxWidth = "none"; } const reset = document.querySelector('[data-map-zoom="reset"]'); if (reset) reset.textContent = `${Math.round(zoom * 100)}%`; };
  document.querySelectorAll("[data-map-zoom]").forEach(button => button.addEventListener("click", () => {
    const action = button.dataset.mapZoom;
    zoom = action === "in" ? Math.min(1.8, zoom + .2) : action === "out" ? Math.max(.8, zoom - .2) : 1;
    applyZoom();
  }));
})();
