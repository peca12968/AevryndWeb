import * as THREE from 'three';
import { createLineSegmentIndices, loadRuntimeHairMotion } from '../hair-motion-runtime.js';

const result = document.querySelector('#result');
try {
  const runtime = await loadRuntimeHairMotion('/assets/character-r1084-motion/manifest.json');
  const indices = createLineSegmentIndices(runtime.curveOffsets);
  const canvas = document.querySelector('#view');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(1);
  renderer.setSize(640, 640, false);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x111111);
  const camera = new THREE.PerspectiveCamera(34, 1, 0.01, 10);
  camera.position.set(0, -1.15, 1.58);
  camera.lookAt(0, 0, 1.52);
  const geometry = new THREE.BufferGeometry();
  const position = new THREE.BufferAttribute(runtime.positions, 3);
  position.setUsage(THREE.DynamicDrawUsage);
  geometry.setAttribute('position', position);
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  const lines = new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0x7b3f24, transparent: true, opacity: 0.82 }));
  scene.add(lines);
  for (let frame = 0; frame < 60; frame++) {
    runtime.evaluateFrame(frame + 1);
    position.needsUpdate = true;
    renderer.render(scene, camera);
  }
  const samples = 180;
  let evaluationMs = 0;
  const started = performance.now();
  for (let frame = 0; frame < samples; frame++) {
    const before = performance.now();
    runtime.evaluateFrame(frame + 1);
    evaluationMs += performance.now() - before;
    position.needsUpdate = true;
    renderer.render(scene, camera);
  }
  const totalMs = performance.now() - started;
  const gl = renderer.getContext();
  const binaryBytes = Object.values(runtime.manifest.digests).reduce((sum, item) => sum + item.bytes, 0);
  const report = {
    revision: 'v249r1084-browser-hair-motion-benchmark',
    userAgent: navigator.userAgent,
    renderer: gl.getParameter(gl.RENDERER),
    curveCount: runtime.manifest.geometry.curveCount,
    pointCount: runtime.manifest.geometry.pointCount,
    segmentCount: indices.length / 2,
    binaryBytes,
    cpuPositionBytes: runtime.positions.byteLength,
    indexBytes: indices.byteLength,
    measuredFrames: samples,
    averageEvaluationMs: evaluationMs / samples,
    averageEvaluationAndRenderMs: totalMs / samples,
    drawCalls: renderer.info.render.calls,
    triangles: renderer.info.render.triangles,
    lines: renderer.info.render.lines,
    thresholds: { maximumEvaluationMs: 5, maximumEvaluationAndRenderMs: 33.3, maximumBinaryBytes: 3 * 1024 * 1024, maximumDrawCalls: 1 },
  };
  report.failures = [];
  if (report.averageEvaluationMs > report.thresholds.maximumEvaluationMs) report.failures.push('CPU evaluation exceeds 5ms');
  if (report.averageEvaluationAndRenderMs > report.thresholds.maximumEvaluationAndRenderMs) report.failures.push('combined update/render exceeds 30fps budget');
  if (binaryBytes > report.thresholds.maximumBinaryBytes) report.failures.push('binary payload exceeds 3MiB');
  if (report.drawCalls > report.thresholds.maximumDrawCalls) report.failures.push('draw calls exceed one');
  report.status = report.failures.length ? 'FAIL' : 'PASS';
  result.textContent = JSON.stringify(report, null, 2);
  result.dataset.status = report.status;
  window.__AEVRYND_R1084_BENCHMARK__ = report;
} catch (error) {
  result.textContent = JSON.stringify({ status: 'ERROR', message: error?.stack || String(error) }, null, 2);
  result.dataset.status = 'ERROR';
}
