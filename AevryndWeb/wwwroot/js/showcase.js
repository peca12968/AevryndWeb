(() => {
  const ageGate = document.querySelector("[data-age-gate]");
  const restrictedContent = document.querySelector("[data-age-restricted-content]");
  const ageConfirmationKey = "aevrynd-showcase-age-confirmed-v1";
  const revealRestrictedContent = () => {
    ageGate?.setAttribute("hidden", "");
    restrictedContent?.removeAttribute("inert");
    restrictedContent?.removeAttribute("aria-hidden");
    document.documentElement.classList.remove("age-gate-active");
  };
  let ageConfirmed = false;
  try { ageConfirmed = window.sessionStorage.getItem(ageConfirmationKey) === "yes"; } catch { ageConfirmed = false; }
  if (ageConfirmed) revealRestrictedContent();
  else {
    document.documentElement.classList.add("age-gate-active");
    ageGate?.querySelector("[data-age-confirm]")?.addEventListener("click", () => {
      try { window.sessionStorage.setItem(ageConfirmationKey, "yes"); } catch { /* 瀏覽器拒絕儲存時仍允許本次檢視。 */ }
      revealRestrictedContent();
    });
  }

  // 靜態展示更新也能提供歷代入口；新版頁面已有連結時不重複新增。
  const archiveNav = document.querySelector('.atlas-nav');
  if (archiveNav && !archiveNav.querySelector('a[href="/history/index.html"]')) {
    const archiveLink = document.createElement('a');
    archiveLink.href = '/history/index.html';
    archiveLink.textContent = '0.x～1.3 歷代版本圖文（44 張截圖）';
    archiveNav.prepend(archiveLink);
  }
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
  const applyZoom = () => { if (map) map.dataset.zoom = String(Math.round(zoom * 100)); const reset = document.querySelector('[data-map-zoom="reset"]'); if (reset) reset.textContent = `${Math.round(zoom * 100)}%`; };
  document.querySelectorAll("[data-map-zoom]").forEach(button => button.addEventListener("click", () => {
    const action = button.dataset.mapZoom;
    zoom = action === "in" ? Math.min(1.8, zoom + .2) : action === "out" ? Math.max(.8, zoom - .2) : 1;
    applyZoom();
  }));

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-comparison]").forEach(comparison => {
    const card = comparison.closest(".visual-pair");
    const range = card?.querySelector("[data-comparison-range]");
    const output = card?.querySelector("[data-comparison-output]");
    if (!range) return;
    const updateComparison = value => {
      const percentage = Math.round(Math.max(0, Math.min(100, Number(value))) / 5) * 5;
      range.value = String(percentage);
      comparison.dataset.reveal = String(percentage);
      if (output) output.textContent = `${percentage}% 顯示新版`;
    };
    const updateFromPointer = event => {
      const bounds = comparison.getBoundingClientRect();
      updateComparison(Math.round(((event.clientX - bounds.left) / bounds.width) * 100));
    };
    let dragging = false;
    comparison.addEventListener("pointerdown", event => {
      dragging = true;
      comparison.setPointerCapture?.(event.pointerId);
      updateFromPointer(event);
    });
    comparison.addEventListener("pointermove", event => { if (dragging) updateFromPointer(event); });
    comparison.addEventListener("pointerup", event => {
      dragging = false;
      comparison.releasePointerCapture?.(event.pointerId);
    });
    comparison.addEventListener("pointercancel", () => { dragging = false; });
    range.addEventListener("input", () => updateComparison(range.value));
    updateComparison(range.value);
  });

  const sceneExplorer = document.querySelector("[data-scene-explorer]");
  if (sceneExplorer) {
    const image = sceneExplorer.querySelector("[data-scene-image]");
    const caption = sceneExplorer.querySelector("[data-scene-caption]");
    const viewButtons = [...sceneExplorer.querySelectorAll("[data-scene-view]")];
    const timeButtons = [...sceneExplorer.querySelectorAll("[data-scene-time]")];
    const playButton = sceneExplorer.querySelector("[data-scene-play]");
    const views = ["first", "third", "god"];
    const times = ["day", "dusk", "night"];
    const viewLabels = { first: "第一人稱", third: "第三人稱", god: "上帝視角" };
    const timeLabels = { day: "日間", dusk: "黃昏", night: "夜間" };
    let currentView = "first", currentTime = "day", sceneTimer = null;
    const renderScene = () => {
      if (!image || !caption) return;
      image.src = `/media/development/visual-score-40-${currentView}-${currentTime}.png`;
      image.alt = `未重新評分 WIP 候選 · ${viewLabels[currentView]}${timeLabels[currentTime]}固定鏡頭實機擷取`;
      const position = views.indexOf(currentView) * times.length + times.indexOf(currentTime) + 1;
      caption.textContent = `${viewLabels[currentView]} · ${timeLabels[currentTime]} · 未評分候選 ${position}／9`;
      viewButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.sceneView === currentView)));
      timeButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.sceneTime === currentTime)));
    };
    const stopScenePlayback = () => {
      if (sceneTimer) window.clearInterval(sceneTimer);
      sceneTimer = null;
      playButton?.setAttribute("aria-pressed", "false");
      if (playButton && !reducedMotion) playButton.textContent = "播放三時段";
    };
    const startScenePlayback = () => {
      if (reducedMotion || sceneTimer) return;
      times.forEach(time => { const preload = new Image(); preload.src = `/media/development/visual-score-40-${currentView}-${time}.png`; });
      playButton?.setAttribute("aria-pressed", "true");
      if (playButton) playButton.textContent = "暫停三時段";
      sceneTimer = window.setInterval(() => {
        currentTime = times[(times.indexOf(currentTime) + 1) % times.length];
        renderScene();
      }, 2200);
    };
    viewButtons.forEach(button => button.addEventListener("click", () => { currentView = button.dataset.sceneView; renderScene(); }));
    timeButtons.forEach(button => button.addEventListener("click", () => { currentTime = button.dataset.sceneTime; renderScene(); }));
    playButton?.addEventListener("click", () => { if (sceneTimer) stopScenePlayback(); else startScenePlayback(); });
    if (playButton && reducedMotion) {
      playButton.disabled = true;
      playButton.textContent = "減少動態模式";
      playButton.title = "系統偏好減少動態，請使用日間、黃昏與夜間按鈕手動切換。";
    }
    document.addEventListener("visibilitychange", () => { if (document.hidden) stopScenePlayback(); });
    window.addEventListener("pagehide", stopScenePlayback);
    renderScene();
  }

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
    lightboxImage.alt = trigger.dataset.lightboxAlt || "展示影像";
    lightboxCaption.textContent = trigger.dataset.lightboxAlt || "展示影像";
  };
  const openLightbox = (trigger, index) => {
    if (!lightbox) return;
    lightboxReturnFocus = trigger;
    showLightboxImage(index);
    lightbox.setAttribute("aria-hidden", "false");
    lightbox.classList.add("is-open");
    document.documentElement.classList.add("showcase-lightbox-active");
    lightbox.querySelector(".lightbox-close")?.focus();
  };
  const closeLightbox = () => {
    if (!lightbox || lightbox.getAttribute("aria-hidden") === "true") return;
    lightbox.setAttribute("aria-hidden", "true");
    lightbox.classList.remove("is-open");
    document.documentElement.classList.remove("showcase-lightbox-active");
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
    if (event.key === "Tab") {
      const controls = [...lightbox.querySelectorAll("button:not([disabled])")];
      if (controls.length === 0) return;
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
})();
