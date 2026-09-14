import assert from 'node:assert/strict';
import { performance } from 'node:perf_hooks';
import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadGeometry } from './load-character.mjs';


const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const assets = path.join(root, 'assets-source', 'aevrynd-character');
const baselinePath = path.join(assets, 'runtime-groom-r506', 'aevrynd-female-hair-runtime-r506.glb');
const candidatePath = path.join(assets, 'runtime-groom-r517', 'aevrynd-female-hair-runtime-r517.glb');
const reportPath = path.join(assets, 'runtime-groom-r517', 'performance-audit.json');


function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}


async function inspect(file) {
  const bytes = await readFile(file);
  const times = [];
  let topology;
  for (let iteration = 0; iteration < 5; iteration++) {
    const started = performance.now();
    const gltf = await loadGeometry(bytes);
    times.push(performance.now() - started);
    let vertices = 0;
    let triangles = 0;
    let drawCalls = 0;
    let meshes = 0;
    const materials = new Set();
    gltf.scene.traverse(object => {
      if (!object.isMesh) return;
      meshes++;
      vertices += object.geometry.attributes.position?.count ?? 0;
      triangles += (object.geometry.index?.count ?? 0) / 3;
      const list = Array.isArray(object.material) ? object.material : [object.material];
      drawCalls += list.length;
      for (const material of list) if (material) materials.add(material.uuid);
    });
    topology = { vertices, triangles, drawCalls, meshes, materials: materials.size, animations: gltf.animations.length };
  }
  return {
    file,
    bytes: bytes.length,
    downloadMB: bytes.length / 1e6,
    medianParseMs: median(times),
    parseSamplesMs: times,
    ...topology,
  };
}


const baseline = await inspect(baselinePath);
const candidate = await inspect(candidatePath);
const gates = {
  smallerDownload: candidate.bytes < baseline.bytes,
  noVertexRegression: candidate.vertices <= baseline.vertices,
  noTriangleRegression: candidate.triangles <= baseline.triangles,
  noDrawCallRegression: candidate.drawCalls <= baseline.drawCalls,
  parseWithinFifteenPercent: candidate.medianParseMs <= baseline.medianParseMs * 1.15,
  animationPresent: candidate.animations >= 1,
};
const report = {
  environment: 'Node.js Three.js GLTFLoader structural/load benchmark; browser GPU benchmark remains required before website replacement',
  baseline,
  candidate,
  delta: {
    bytes: candidate.bytes - baseline.bytes,
    vertices: candidate.vertices - baseline.vertices,
    triangles: candidate.triangles - baseline.triangles,
    drawCalls: candidate.drawCalls - baseline.drawCalls,
    medianParseMs: candidate.medianParseMs - baseline.medianParseMs,
  },
  gates,
  status: Object.values(gates).every(Boolean) ? 'PASS' : 'FAIL',
};
await writeFile(reportPath, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
assert.equal(report.status, 'PASS');

