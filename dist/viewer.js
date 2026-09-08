const viewer = document.querySelector('#character-model');
const status = document.querySelector('#viewer-status');
const controls = [...document.querySelectorAll('.viewer-controls button')];
const rotate = document.querySelector('#rotate-model');
const motion = matchMedia('(prefers-reduced-motion: reduce)');
let timeout;

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
    viewer.cameraOrbit = `${button.dataset.view}deg 80deg 105%`;
    if (motion.matches) viewer.jumpCameraToGoal();
  });
});
rotate.addEventListener('click', () => {
  viewer.autoRotate = !viewer.autoRotate;
  rotate.setAttribute('aria-pressed', String(viewer.autoRotate));
  rotate.textContent = viewer.autoRotate ? '暫停旋轉' : '自動旋轉';
});
document.querySelector('#reset-model').addEventListener('click', () => {
  stopRotation();
  viewer.resetTurntableRotation();
  viewer.cameraOrbit = '0deg 80deg 105%';
  viewer.cameraTarget = 'auto auto auto';
  viewer.fieldOfView = 'auto';
  if (motion.matches) viewer.jumpCameraToGoal();
});
viewer.addEventListener('pointerdown', stopRotation);
viewer.addEventListener('keydown', stopRotation);
motion.addEventListener('change', () => { if (motion.matches) stopRotation(); });
document.addEventListener('visibilitychange', () => { if (document.hidden) stopRotation(); });
