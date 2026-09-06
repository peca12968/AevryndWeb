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

  const lightbox = document.querySelector("#showcaseLightbox");
  const lightboxImage = lightbox?.querySelector("figure img");
  const lightboxCaption = lightbox?.querySelector("figcaption");
  const lightboxTriggers = [...document.querySelectorAll("[data-lightbox-src]")];
  let lightboxIndex = 0;
  let lightboxReturnFocus = null;
  const showLightboxImage = index => {
    if (!lightbox || !lightboxImage || !lightboxCaption || lightboxTriggers.length === 0) return;
    lightboxIndex = (index + lightboxTriggers.length) % lightboxTriggers.length;
    const trigger = lightboxTriggers[lightboxIndex];
    lightboxImage.src = trigger.dataset.lightboxSrc;
    lightboxImage.alt = trigger.dataset.lightboxAlt || "角色預覽";
    lightboxCaption.textContent = trigger.dataset.lightboxAlt || "角色預覽";
  };
  const openLightbox = (trigger, index) => {
    if (!lightbox) return;
    lightboxReturnFocus = trigger;
    showLightboxImage(index);
    lightbox.setAttribute("aria-hidden", "false");
    lightbox.classList.add("is-open");
    document.body.style.overflow = "hidden";
    lightbox.querySelector(".lightbox-close")?.focus();
  };
  const closeLightbox = () => {
    if (!lightbox || lightbox.getAttribute("aria-hidden") === "true") return;
    lightbox.setAttribute("aria-hidden", "true");
    lightbox.classList.remove("is-open");
    document.body.style.overflow = "";
    lightboxReturnFocus?.focus();
  };
  lightboxTriggers.forEach((trigger, index) => trigger.addEventListener("click", () => openLightbox(trigger, index)));
  lightbox?.querySelector(".lightbox-close")?.addEventListener("click", closeLightbox);
  lightbox?.querySelectorAll("[data-lightbox-step]").forEach(button => button.addEventListener("click", () => showLightboxImage(lightboxIndex + Number(button.dataset.lightboxStep))));
  lightbox?.addEventListener("click", event => { if (event.target === lightbox) closeLightbox(); });
  document.addEventListener("keydown", event => {
    if (lightbox?.getAttribute("aria-hidden") !== "false") return;
    if (event.key === "Escape") closeLightbox();
    if (event.key === "ArrowLeft") showLightboxImage(lightboxIndex - 1);
    if (event.key === "ArrowRight") showLightboxImage(lightboxIndex + 1);
  });
})();
