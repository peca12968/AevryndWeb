import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const assets = '/@fs/D:/Download/Aevrynd/sites-engine-journey/assets-source/aevrynd-character/runtime-character-r526';
const cases = {
  baseline: `${assets}/baseline-r522.glb`,
  candidate: `${assets}/candidate-r526.glb`,
};
const output = document.querySelector('#result');
const batches = 5;
const framesPerBatch = 300;

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

async function parse(bytes) {
  const loader = new GLTFLoader();
  const started = performance.now();
  const gltf = await loader.parseAsync(bytes, '');
  return { gltf, elapsedMs: performance.now() - started };
}

function dispose(root) {
  root.traverse(node => {
    if (!node.isMesh) return;
    node.geometry.dispose();
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) material?.dispose();
  });
}

function prepare(gltf) {
  const scene = new THREE.Scene();
  scene.add(gltf.scene);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x222222, 2.2));
  const camera = new THREE.PerspectiveCamera(38, 1, 0.01, 10);
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse(node => {
    if (node.isSkinnedMesh) node.skeleton.update();
    if (node.isMesh) node.frustumCulled = false;
  });
  const bounds = new THREE.Box3().setFromObject(gltf.scene, true);
  const center = bounds.getCenter(new THREE.Vector3());
  const size = bounds.getSize(new THREE.Vector3());
  const extent = Math.max(size.x, size.y, size.z);
  camera.near = extent / 100;
  camera.far = extent * 10;
  camera.position.set(center.x, center.y, center.z + extent * 2.2);
  camera.lookAt(center);
  camera.updateProjectionMatrix();
  return { scene, camera };
}

try {
  const buffers = {};
  for (const label of ['baseline', 'candidate']) buffers[label] = await (await fetch(cases[label])).arrayBuffer();
  const order = ['baseline', 'candidate', 'candidate', 'baseline', 'baseline', 'candidate', 'candidate', 'baseline', 'baseline', 'candidate'];
  const parseRuns = { baseline: [], candidate: [] };
  for (const label of order) {
    const result = await parse(buffers[label]);
    parseRuns[label].push(result.elapsedMs);
    dispose(result.gltf.scene);
    await new Promise(resolve => requestAnimationFrame(resolve));
  }
  const prepared = {};
  for (const label of ['baseline', 'candidate']) prepared[label] = prepare((await parse(buffers[label])).gltf);
  const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(900, 900, false);
  renderer.info.autoReset = false;
  document.body.append(renderer.domElement);
  for (const label of ['baseline', 'candidate']) {
    for (let frame = 0; frame < 60; frame++) renderer.render(prepared[label].scene, prepared[label].camera);
    renderer.getContext().finish();
  }
  const renderRuns = { baseline: [], candidate: [] };
  const topology = {};
  for (const label of order) {
    renderer.info.reset();
    const started = performance.now();
    for (let frame = 0; frame < framesPerBatch; frame++) renderer.render(prepared[label].scene, prepared[label].camera);
    renderer.getContext().finish();
    renderRuns[label].push((performance.now() - started) / framesPerBatch);
    topology[label] = { calls: renderer.info.render.calls / framesPerBatch, triangles: renderer.info.render.triangles / framesPerBatch };
  }
  const result = label => ({
    bytes: buffers[label].byteLength,
    parseMs: median(parseRuns[label]),
    renderMsMedian: median(renderRuns[label]),
    parseSamplesMs: parseRuns[label],
    renderSamplesMs: renderRuns[label],
    ...topology[label],
  });
  const baseline = result('baseline');
  const candidate = result('candidate');
  const gates = {
    noDownloadRegression: candidate.bytes <= baseline.bytes,
    noDrawCallRegression: candidate.calls <= baseline.calls,
    noTriangleRegression: candidate.triangles <= baseline.triangles,
    renderWithinFifteenPercent: candidate.renderMsMedian <= baseline.renderMsMedian * 1.15,
    parseWithinFifteenPercent: candidate.parseMs <= baseline.parseMs * 1.15,
  };
  const report = { environment: navigator.userAgent, viewport: [900, 900], batches, framesPerBatch, baseline, candidate, gates, status: Object.values(gates).every(Boolean) ? 'PASS' : 'FAIL' };
  window.__AEVRYND_R526_BENCHMARK__ = report;
  output.textContent = JSON.stringify(report, null, 2);
  document.title = `R526 WebGL benchmark ${report.status}`;
  renderer.domElement.remove();
  renderer.dispose();
} catch (error) {
  const report = { status: 'ERROR', message: String(error), stack: error?.stack };
  window.__AEVRYND_R526_BENCHMARK__ = report;
  output.textContent = JSON.stringify(report, null, 2);
  document.title = 'R526 WebGL benchmark ERROR';
}
