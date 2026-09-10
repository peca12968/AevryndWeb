import fs from 'node:fs';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { createRuntimeGroom, decodeRuntimeGroom } from '../src/hair-groom-format.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const directory = process.env.AEVRYND_RUNTIME_GROOM_DIR
  ?? path.join(root, 'assets-source/aevrynd-character/runtime-groom-v249r17');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));

function readArrayBuffer(file) {
  const value = fs.readFileSync(path.join(directory, file));
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
}

const buffers = {
  guides: readArrayBuffer(manifest.files.guides),
  followGuide: readArrayBuffer(manifest.files.followGuide),
  followOffsets: readArrayBuffer(manifest.files.followOffsets),
  followCollisionNormals: readArrayBuffer(manifest.files.followCollisionNormals),
  followContactHeadWeights: readArrayBuffer(manifest.files.followContactHeadWeights),
};
const decoded = decodeRuntimeGroom(manifest, buffers);
const runtime = createRuntimeGroom(decoded, { damping: 0.09, bendCompliance: 4e-7, collisionMargin: 0.0015 });
const anchors = Float64Array.from(decoded.guides.flatMap(guide => guide[0]));
const baseAnchors = Float64Array.from(anchors);
const posePivot = manifest.contactPose.pivot;
const authored = runtime.solver.copyPositions(new Float64Array(runtime.solver.positions.length));

runtime.solver.setWind(0, 0, 0);
for (let frame = 0; frame < 120; frame++) runtime.solver.advance(1 / 30, anchors);
let maximumStaticGuideDisplacement = 0;
for (let guide = 0; guide < runtime.solver.offsets.length - 1; guide++) {
  for (let point = runtime.solver.offsets[guide] + 1; point < runtime.solver.offsets[guide + 1]; point++) {
    const offset = point * 3;
    maximumStaticGuideDisplacement = Math.max(maximumStaticGuideDisplacement, Math.hypot(
      runtime.solver.positions[offset] - authored[offset],
      runtime.solver.positions[offset + 1] - authored[offset + 1],
      runtime.solver.positions[offset + 2] - authored[offset + 2],
    ));
  }
}

let output;
let maximumTipMotion = 0;
const restTips = [];
for (let guide = 0; guide < runtime.solver.offsets.length - 1; guide++) {
  const tip = (runtime.solver.offsets[guide + 1] - 1) * 3;
  restTips.push([runtime.solver.positions[tip], runtime.solver.positions[tip + 1], runtime.solver.positions[tip + 2]]);
}
for (let frame = 0; frame < 40; frame++) {
  runtime.solver.setWind(Math.sin(frame / 8) * 1.2, Math.cos(frame / 11) * 0.25, 0);
  runtime.solver.advance(1 / 30, anchors);
  output = runtime.follows.write(output);
  for (let guide = 0; guide < runtime.solver.offsets.length - 1; guide++) {
    const tip = (runtime.solver.offsets[guide + 1] - 1) * 3;
    maximumTipMotion = Math.max(maximumTipMotion, Math.hypot(
      runtime.solver.positions[tip] - restTips[guide][0],
      runtime.solver.positions[tip + 1] - restTips[guide][1],
      runtime.solver.positions[tip + 2] - restTips[guide][2],
    ));
  }
}

const measuredFrames = 30;
const started = performance.now();
for (let frame = 0; frame < measuredFrames; frame++) {
  const yaw = Math.sin(frame * Math.PI / 15) * Math.PI / 10;
  const cosine = Math.cos(yaw), sine = Math.sin(yaw);
  runtime.solver.setPoseRotation([cosine, -sine, 0, sine, cosine, 0, 0, 0, 1], posePivot);
  for (let guide = 0; guide < decoded.guides.length; guide++) {
    const offset = guide * 3;
    const x = baseAnchors[offset] - posePivot[0];
    const y = baseAnchors[offset + 1] - posePivot[1];
    anchors[offset] = posePivot[0] + cosine * x - sine * y;
    anchors[offset + 1] = posePivot[1] + sine * x + cosine * y;
    anchors[offset + 2] = baseAnchors[offset + 2];
  }
  runtime.solver.setWind(Math.sin(frame / 8) * 1.2, Math.cos(frame / 11) * 0.25, 0);
  runtime.solver.advance(1 / 30, anchors);
  output = runtime.follows.write(output);
}
const averageFrameMs = (performance.now() - started) / measuredFrames;
const totalBytes = Object.values(buffers).reduce((sum, buffer) => sum + buffer.byteLength, 0);
const finiteOutput = output.every(Number.isFinite);
const failures = [];
if (manifest.maximumRestReconstructionErrorM > 1e-6) failures.push('rest reconstruction error');
if (!finiteOutput) failures.push('non-finite follow output');
if (averageFrameMs > 33.3) failures.push('CPU simulation and follow expansion exceeds 30fps budget');
if (totalBytes > 5 * 1024 * 1024) failures.push('runtime groom exceeds 5MiB source budget');
if (maximumStaticGuideDisplacement > 0.03) failures.push('collision or gravity destroys the authored rest silhouette');
if (maximumTipMotion < 0.002 || maximumTipMotion > 0.09) failures.push('secondary tip motion outside 2-90mm range');

const report = {
  format: manifest.format,
  simulationGuideCount: decoded.guides.length,
  renderedCurveCount: decoded.follows.length,
  pointsPerCurve: manifest.render.pointsPerCurve,
  totalBinaryBytes: totalBytes,
  averageCpuFrameMs: averageFrameMs,
  measuredFrames,
  measuredHeadYawDegrees: 18,
  finiteOutput,
  maximumRestReconstructionErrorM: manifest.maximumRestReconstructionErrorM,
  maximumStaticGuideDisplacementM: maximumStaticGuideDisplacement,
  maximumTipMotionM: maximumTipMotion,
  thresholds: {
    maximumAverageCpuFrameMs: 33.3,
    maximumBinaryBytes: 5 * 1024 * 1024,
    maximumRestReconstructionErrorM: 1e-6,
    maximumStaticGuideDisplacementM: 0.03,
    minimumTipMotionM: 0.002,
    maximumTipMotionM: 0.09,
  },
  failures,
  status: failures.length ? 'FAIL' : 'PASS',
};
fs.writeFileSync(path.join(directory, 'runtime-audit.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
if (failures.length) process.exitCode = 2;
