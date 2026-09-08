const viewer = document.querySelector('#character-model');
const status = document.querySelector('#viewer-status');
const controls = [...document.querySelectorAll('.character-editor-panel button, #orbit-slider')];
const rotate = document.querySelector('#rotate-model');
const orbitSlider = document.querySelector('#orbit-slider');
const orbitOutput = document.querySelector('#orbit-output');
const motion = matchMedia('(prefers-reduced-motion: reduce)');
let cameraMode = 'body';
let timeout;

const camera = {
  face: { target: '0m 1.53m 0m', radius: '1.2m', field: '25deg' },
  body: { target: '0m 0.86m 0m', radius: '3.7m', field: '30deg' }
};

function setPressedCamera(mode) {
  document.querySelectorAll('[data-camera]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.camera === mode));
  });
}

function setOrbit(angle, immediate = false) {
  const view = camera[cameraMode];
  viewer.cameraTarget = view.target;
  viewer.fieldOfView = view.field;
  viewer.cameraOrbit = `${angle}deg 82deg ${view.radius}`;
  orbitSlider.value = String(angle);
  orbitOutput.value = `${angle}°`;
  orbitOutput.textContent = `${angle}°`;
  if (immediate || motion.matches) viewer.jumpCameraToGoal();
}

function stopRotation() {
  viewer.autoRotate = false;
  rotate.setAttribute('aria-pressed', 'false');
  rotate.textContent = '自動旋轉';
}
function failed() {
  clearTimeout(timeout);
  stopRotation();
  controls.forEach(button => { button.disabled = true; });
  status.hidden = false;
  status.replaceChildren(document.createTextNode('模型載入失敗，請檢查連線，或確認瀏覽器支援 3D 顯示。'));
  const retry = document.createElement('button');
  retry.type = 'button';
  retry.textContent = '重新載入';
  retry.addEventListener('click', () => location.reload());
  status.append(retry);
}
viewer.addEventListener('load', () => {
  clearTimeout(timeout);
  status.hidden = true;
  controls.forEach(button => { button.disabled = false; });
});
viewer.addEventListener('error', failed);
timeout = setTimeout(failed, 60000);
import('./vendor/model-viewer.min.js').catch(failed);

document.querySelectorAll('[data-view]').forEach(button => {
  button.addEventListener('click', () => {
    stopRotation();
    viewer.resetTurntableRotation();
    setOrbit(Number(button.dataset.view));
  });
});
document.querySelectorAll('[data-camera]').forEach(button => {
  button.addEventListener('click', () => {
    stopRotation();
    cameraMode = button.dataset.camera;
    setPressedCamera(cameraMode);
    setOrbit(Number(orbitSlider.value));
  });
});
orbitSlider.addEventListener('input', () => {
  stopRotation();
  setOrbit(Number(orbitSlider.value), true);
});
rotate.addEventListener('click', () => {
  viewer.autoRotate = !viewer.autoRotate;
  rotate.setAttribute('aria-pressed', String(viewer.autoRotate));
  rotate.textContent = viewer.autoRotate ? '暫停旋轉' : '自動旋轉';
});
document.querySelector('#reset-model').addEventListener('click', () => {
  stopRotation();
  cameraMode = 'body';
  setPressedCamera(cameraMode);
  viewer.resetTurntableRotation();
  setOrbit(0);
});
viewer.addEventListener('camera-change', () => {
  if (viewer.autoRotate) return;
  const degrees = Math.round(viewer.getCameraOrbit().theta * 180 / Math.PI);
  const normalized = ((degrees + 180) % 360 + 360) % 360 - 180;
  orbitSlider.value = String(normalized);
  orbitOutput.value = `${normalized}°`;
  orbitOutput.textContent = `${normalized}°`;
});
viewer.addEventListener('pointerdown', stopRotation);
viewer.addEventListener('keydown', stopRotation);
motion.addEventListener('change', () => { if (motion.matches) stopRotation(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopRotation(); });
