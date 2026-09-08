import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { loadGeometry } from './load-character.mjs';

const baselinePath = process.argv[2] || '.character-build/aevrynd-female-authoring-v57.glb';
const candidatePath = process.argv[3] || '.character-build/aevrynd-female-authoring-v61.glb';
const rounds = 7;

function median(values) {
  const ordered = [...values].sort((a, b) => a - b);
  return ordered[Math.floor(ordered.length / 2)];
}

async function measure(path) {
  const bytes = await readFile(path);
  const times = [];
  let metrics;
  for (let round = 0; round < rounds; round += 1) {
    global.gc?.();
    const beforeHeap = process.memoryUsage().heapUsed;
    const start = performance.now();
    const gltf = await loadGeometry(bytes);
    const elapsed = performance.now() - start;
    let drawCalls = 0;
    let vertices = 0;
    let triangles = 0;
    gltf.scene.traverse(object => {
      if (!object.isMesh) return;
      drawCalls += Array.isArray(object.material) ? object.material.length : 1;
      const positions = object.geometry.getAttribute('position');
      vertices += positions?.count || 0;
      triangles += object.geometry.index ? object.geometry.index.count / 3 : (positions?.count || 0) / 3;
    });
    metrics = {
      bytes: bytes.length,
      drawCalls,
      vertices,
      triangles,
      animations: gltf.animations.length,
      heapDeltaMB: +((process.memoryUsage().heapUsed - beforeHeap) / 1048576).toFixed(2),
    };
    times.push(elapsed);
  }
  return {
    ...metrics,
    medianLoadMs: +median(times).toFixed(2),
    minLoadMs: +Math.min(...times).toFixed(2),
    maxLoadMs: +Math.max(...times).toFixed(2),
  };
}

const baseline = await measure(baselinePath);
const candidate = await measure(candidatePath);
assert(candidate.bytes <= baseline.bytes, `candidate download regression ${candidate.bytes}/${baseline.bytes}`);
assert(candidate.drawCalls <= baseline.drawCalls, `candidate draw-call regression ${candidate.drawCalls}/${baseline.drawCalls}`);
assert(candidate.vertices <= baseline.vertices, `candidate vertex regression ${candidate.vertices}/${baseline.vertices}`);
assert(candidate.medianLoadMs <= baseline.medianLoadMs * 1.20 + 2, `candidate median load regression ${candidate.medianLoadMs}/${baseline.medianLoadMs}`);
console.log(JSON.stringify({
  status: 'PASS',
  rounds,
  baseline,
  candidate,
  byteReductionPercent: +((1 - candidate.bytes / baseline.bytes) * 100).toFixed(2),
  drawCallReduction: baseline.drawCalls - candidate.drawCalls,
  vertexReduction: baseline.vertices - candidate.vertices,
}, null, 2));
