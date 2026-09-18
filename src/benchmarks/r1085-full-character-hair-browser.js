import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { loadRuntimeHairMotion } from '../hair-motion-runtime.js';
import { HairStrandRenderer } from '../hair-strand-renderer.js';
import { auditDynamicHairBodyCollision } from '../hair-runtime-collision.js';
import { applyOwnedCharacterMaterials } from '../character-runtime-materials.js';


const resultElement = document.querySelector('#result');
const canvas = document.querySelector('#view');
const width = 900;
const height = 900;
const samples = 180;
const batches = 3;

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

async function parse(buffer) {
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const started = performance.now();
  const gltf = await loader.parseAsync(buffer, '');
  return { gltf, elapsedMs: performance.now() - started };
}

function addLighting(scene) {
  scene.background = new THREE.Color(0x15181b);
  scene.add(new THREE.HemisphereLight(0xf3f6ff, 0x251814, 1.55));
  const key = new THREE.DirectionalLight(0xffeadf, 3.4);
  key.position.set(2.2, 3.5, 4.5);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xb8d7ff, 2.0);
  rim.position.set(-3.2, 2.4, -2.0);
  scene.add(rim);
}

function prepare(root) {
  const scene = new THREE.Scene();
  scene.add(root);
  addLighting(scene);
  root.updateMatrixWorld(true);
  root.traverse(node => {
    if (!node.isMesh) return;
    node.frustumCulled = false;
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) {
      if (!material) continue;
      material.envMapIntensity = 0.55;
      material.needsUpdate = true;
    }
  });
  const bounds = new THREE.Box3().setFromObject(root, true);
  return { scene, root, bounds };
}

function createHeadCamera(bounds, angleDegrees = 0) {
  const size = bounds.getSize(new THREE.Vector3());
  const center = bounds.getCenter(new THREE.Vector3());
  const target = new THREE.Vector3(center.x, bounds.max.y - size.y * 0.085, center.z);
  const distance = size.y * 0.39;
  const angle = THREE.MathUtils.degToRad(angleDegrees);
  const camera = new THREE.PerspectiveCamera(32, width / height, Math.max(0.005, size.y / 500), size.y * 8);
  camera.position.set(target.x + Math.sin(angle) * distance, target.y + size.y * 0.015, target.z + Math.cos(angle) * distance);
  camera.lookAt(target);
  camera.updateProjectionMatrix();
  return camera;
}

function transformedHairBounds(runtime, hairMesh) {
  hairMesh.updateWorldMatrix(true, false);
  const bounds = new THREE.Box3();
  const point = new THREE.Vector3();
  for (let index = 0; index < runtime.basePositions.length; index += 3) {
    point.fromArray(runtime.basePositions, index).applyMatrix4(hairMesh.matrixWorld);
    bounds.expandByPoint(point);
  }
  return { min: bounds.min.toArray(), max: bounds.max.toArray(), hairMatrixWorld: hairMesh.matrixWorld.toArray() };
}

async function benchmarkScene(renderer, prepared, camera, hair = null) {
  for (let frame = 0; frame < 60; frame++) {
    hair?.updateFrame(frame + 1);
    renderer.render(prepared.scene, camera);
  }
  renderer.getContext().finish();
  const frameRuns = [];
  const updateRuns = [];
  let topology = null;
  for (let batch = 0; batch < batches; batch++) {
    renderer.info.reset();
    let updateMs = 0;
    const started = performance.now();
    for (let frame = 0; frame < samples; frame++) {
      const updateStarted = performance.now();
      hair?.updateFrame(frame + 1);
      updateMs += performance.now() - updateStarted;
      renderer.render(prepared.scene, camera);
    }
    renderer.getContext().finish();
    frameRuns.push((performance.now() - started) / samples);
    updateRuns.push(updateMs / samples);
    topology = {
      drawCalls: renderer.info.render.calls / samples,
      triangles: renderer.info.render.triangles / samples,
      lines: renderer.info.render.lines / samples,
      points: renderer.info.render.points / samples,
    };
  }
  return { frameMsMedian: median(frameRuns), updateMsMedian: median(updateRuns), frameRuns, updateRuns, ...topology };
}

try {
  const urls = {
    baseline: '/assets/character-female-refined.glb',
    candidate: '/assets/character-r1085/character-r1085.glb',
  };
  const [baselineResponse, candidateResponse, runtime] = await Promise.all([
    fetch(urls.baseline),
    fetch(urls.candidate),
    loadRuntimeHairMotion('/assets/character-r1084-motion/manifest.json'),
  ]);
  if (!baselineResponse.ok || !candidateResponse.ok) throw new Error('failed to fetch full-character benchmark asset');
  const [baselineBuffer, candidateBuffer] = await Promise.all([baselineResponse.arrayBuffer(), candidateResponse.arrayBuffer()]);
  const baselineParsed = await parse(baselineBuffer);
  const candidateParsed = await parse(candidateBuffer);
  const baseline = prepare(baselineParsed.gltf.scene);
  const candidate = prepare(candidateParsed.gltf.scene);
  const ownedMaterials = applyOwnedCharacterMaterials(candidate.root);
  const anchor = candidate.root.getObjectByName('AevryndHairMotionAnchor_R1085');
  if (!anchor) throw new Error('r1085 dynamic-hair anchor is missing');
  const strands = new HairStrandRenderer(runtime, { viewportWidth: width, viewportHeight: height });
  anchor.add(strands.mesh);
  candidate.root.updateMatrixWorld(true);
  const runtimeHairBounds = transformedHairBounds(runtime, strands.mesh);
  const requestedAngle = Number(new URLSearchParams(location.search).get('angle') || 0);
  const baselineCamera = createHeadCamera(baseline.bounds, requestedAngle);
  const candidateCamera = createHeadCamera(candidate.bounds, requestedAngle);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setSize(width, height, false);
  renderer.setPixelRatio(1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.info.autoReset = false;
  const baselineMetrics = await benchmarkScene(renderer, baseline, baselineCamera);
  const candidateMetrics = await benchmarkScene(renderer, candidate, candidateCamera, strands);
  const dynamicCollision = auditDynamicHairBodyCollision(candidate.root, runtime, strands.mesh);
  const hairBinaryBytes = Object.values(runtime.manifest.digests).reduce((sum, item) => sum + item.bytes, 0);
  const dynamicCpuBytes = runtime.positions.byteLength + strands.textureData.byteLength;
  const geometryGpuBytes = strands.vertexCount * 4 * 4 + strands.indexCount * 4;
  const candidateDownloadBytes = candidateBuffer.byteLength + hairBinaryBytes;
  const gates = {
    anchorPresent: Boolean(anchor),
    downloadWithinTwelvePercent: candidateDownloadBytes <= baselineBuffer.byteLength * 1.12,
    updateUnderFiveMs: candidateMetrics.updateMsMedian <= 5,
    completeFrameUnderThirtyThreeMs: candidateMetrics.frameMsMedian <= 33.3,
    renderAtSixtyFpsBudget: candidateMetrics.frameMsMedian <= 16.67,
    drawCallsNoHigherThanBaseline: candidateMetrics.drawCalls <= baselineMetrics.drawCalls,
    drawCallsAtMostSixtyFour: candidateMetrics.drawCalls <= 64,
    trianglesAtMostDoubleBaseline: candidateMetrics.triangles <= baselineMetrics.triangles * 2,
    dynamicMemoryUnderEightMiB: dynamicCpuBytes + geometryGpuBytes <= 8 * 1024 * 1024,
    dynamicBodyCollisionClear: dynamicCollision.status === 'PASS',
  };
  const report = {
    revision: 'v249r1085-full-character-dynamic-hair-browser',
    environment: navigator.userAgent,
    renderer: renderer.getContext().getParameter(renderer.getContext().RENDERER),
    viewport: [width, height],
    batches,
    framesPerBatch: samples,
    baseline: { bytes: baselineBuffer.byteLength, parseMs: baselineParsed.elapsedMs, ...baselineMetrics },
    candidate: {
      characterBytes: candidateBuffer.byteLength,
      hairBinaryBytes,
      totalDownloadBytes: candidateDownloadBytes,
      parseMs: candidateParsed.elapsedMs,
      dynamicCpuBytes,
      dynamicGeometryGpuBytes: geometryGpuBytes,
      renderedHairCurves: strands.renderedCurveCount,
      sourceHairCurves: runtime.manifest.geometry.curveCount,
      hairSegments: strands.segmentCount,
      hairRibbonVertices: strands.vertexCount,
      hairRibbonIndices: strands.indexCount,
      runtimeHairBounds,
      ownedMaterials,
      ...candidateMetrics,
      dynamicCollision,
    },
    gates,
    failures: Object.entries(gates).filter(([, passed]) => !passed).map(([name]) => name),
  };
  report.status = report.failures.length ? 'FAIL' : 'PASS';
  window.__AEVRYND_R1085_BENCHMARK__ = report;
  resultElement.textContent = JSON.stringify(report, null, 2);
  resultElement.dataset.status = report.status;
  document.title = `Aevrynd r1085 ${report.status}`;
  strands.updateFrame(Number(new URLSearchParams(location.search).get('frame') || 21));
  renderer.info.autoReset = true;
  renderer.render(candidate.scene, candidateCamera);
} catch (error) {
  const report = { revision: 'v249r1085-full-character-dynamic-hair-browser', status: 'ERROR', message: error?.stack || String(error) };
  window.__AEVRYND_R1085_BENCHMARK__ = report;
  resultElement.textContent = JSON.stringify(report, null, 2);
  resultElement.dataset.status = 'ERROR';
  document.title = 'Aevrynd r1085 ERROR';
}
