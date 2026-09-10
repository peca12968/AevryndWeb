import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRuntimeGroom, decodeRuntimeGroom } from '../src/hair-groom-format.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const directory = path.join(root, 'assets-source/aevrynd-character/runtime-groom-v249r94');
const output = path.join(directory, 'motion-audit-r187.json');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));

function readArrayBuffer(filename) {
  const value = fs.readFileSync(path.join(directory, filename));
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
}

const decoded = decodeRuntimeGroom(manifest, {
  guides: readArrayBuffer(manifest.files.guides),
  followGuide: readArrayBuffer(manifest.files.followGuide),
  followOffsets: readArrayBuffer(manifest.files.followOffsets),
  followCollisionNormals: readArrayBuffer(manifest.files.followCollisionNormals),
  followContactHeadWeights: readArrayBuffer(manifest.files.followContactHeadWeights),
});
const runtime = createRuntimeGroom(decoded, {
  damping: 0.09,
  bendCompliance: 4e-7,
  collisionMargin: 0.0015,
});
const solver = runtime.solver;
const anchors = Float64Array.from(decoded.guides.flatMap(guide => guide[0]));
const bindAnchors = Float64Array.from(anchors);
const pivot = manifest.contactPose.pivot;

for (let frame = 0; frame < 120; frame++) solver.advance(1 / 30, anchors);
const settled = Float64Array.from(solver.positions);
const states = [];
let peakTipLagM = 0;
let peakMidLagM = 0;
let peakRootErrorM = 0;

function distance(array, offset, x, y, z) {
  return Math.hypot(array[offset] - x, array[offset + 1] - y, array[offset + 2] - z);
}

for (let frame = 1; frame <= 60; frame++) {
  const yaw = Math.sin(frame * Math.PI / 30) * Math.PI / 10;
  const cosine = Math.cos(yaw), sine = Math.sin(yaw);
  const rotation = [cosine, -sine, 0, sine, cosine, 0, 0, 0, 1];
  solver.setPoseRotation(rotation, pivot);
  for (let guide = 0; guide < decoded.guides.length; guide++) {
    const offset = guide * 3;
    const x = bindAnchors[offset] - pivot[0];
    const y = bindAnchors[offset + 1] - pivot[1];
    anchors[offset] = pivot[0] + cosine * x - sine * y;
    anchors[offset + 1] = pivot[1] + sine * x + cosine * y;
    anchors[offset + 2] = bindAnchors[offset + 2];
  }
  const impulse = frame <= 36 ? Math.sin(frame / 8) * 2.4 : Math.sin(frame / 8) * 0.7;
  solver.setWind(impulse, 0.32 * Math.cos(frame / 11), 0);
  solver.advance(1 / 30, anchors);

  let rootMaximum = 0, midTotal = 0, tipTotal = 0;
  for (let guide = 0; guide < decoded.guides.length; guide++) {
    const start = solver.offsets[guide];
    const end = solver.offsets[guide + 1];
    const rootOffset = start * 3;
    rootMaximum = Math.max(rootMaximum, distance(solver.positions, rootOffset,
      anchors[guide * 3], anchors[guide * 3 + 1], anchors[guide * 3 + 2]));
    for (const [point, accumulator] of [[Math.floor((start + end - 1) / 2), 'mid'], [end - 1, 'tip']]) {
      const offset = point * 3;
      const rx = solver.restRelative[offset], ry = solver.restRelative[offset + 1], rz = solver.restRelative[offset + 2];
      const targetX = anchors[guide * 3] + rotation[0] * rx + rotation[1] * ry + rotation[2] * rz;
      const targetY = anchors[guide * 3 + 1] + rotation[3] * rx + rotation[4] * ry + rotation[5] * rz;
      const targetZ = anchors[guide * 3 + 2] + rotation[6] * rx + rotation[7] * ry + rotation[8] * rz;
      const lag = distance(solver.positions, offset, targetX, targetY, targetZ);
      if (accumulator === 'mid') midTotal += lag;
      else tipTotal += lag;
    }
  }
  const meanMidLagM = midTotal / decoded.guides.length;
  const meanTipLagM = tipTotal / decoded.guides.length;
  peakRootErrorM = Math.max(peakRootErrorM, rootMaximum);
  peakMidLagM = Math.max(peakMidLagM, meanMidLagM);
  peakTipLagM = Math.max(peakTipLagM, meanTipLagM);
  if ([12, 24, 36, 60].includes(frame)) {
    states.push({ frame, yawDeg: yaw * 180 / Math.PI, rootMaxErrorM: rootMaximum, meanMidLagM, meanTipLagM });
  }
}

solver.setWind(0, 0, 0);
solver.setPoseRotation([1, 0, 0, 0, 1, 0, 0, 0, 1], pivot);
anchors.set(bindAnchors);
for (let frame = 0; frame < 180; frame++) solver.advance(1 / 30, anchors);
let settleTipTotal = 0;
for (let guide = 0; guide < decoded.guides.length; guide++) {
  const tip = (solver.offsets[guide + 1] - 1) * 3;
  settleTipTotal += distance(solver.positions, tip, settled[tip], settled[tip + 1], settled[tip + 2]);
}
const settleTipMeanErrorM = settleTipTotal / decoded.guides.length;
const finite = [...solver.positions].every(Number.isFinite);
const thresholds = {
  maximumRootTrackingErrorM: 1e-8,
  minimumPeakTipLagM: 0.002,
  maximumPeakTipLagM: 0.09,
  minimumTipToMidLagRatio: 1.05,
  maximumSettleTipMeanErrorM: 0.006,
};
const failures = [];
if (!finite) failures.push('non-finite simulated positions');
if (peakRootErrorM > thresholds.maximumRootTrackingErrorM) failures.push('root tracking drift');
if (peakTipLagM < thresholds.minimumPeakTipLagM) failures.push('tip motion too small');
if (peakTipLagM > thresholds.maximumPeakTipLagM) failures.push('tip motion too large');
if (peakTipLagM / peakMidLagM < thresholds.minimumTipToMidLagRatio) failures.push('motion does not increase from mid-length to tip');
if (settleTipMeanErrorM > thresholds.maximumSettleTipMeanErrorM) failures.push('hair does not settle close to its resting state');

const report = {
  candidate: 'r187',
  runtimeGroom: path.relative(root, directory).replaceAll('\\', '/'),
  guideCount: decoded.guides.length,
  renderedCurveCount: manifest.render.curveCount,
  fixedStepHz: 1 / solver.fixedStep,
  states,
  peakRootErrorM,
  peakMidLagM,
  peakTipLagM,
  tipToMidLagRatio: peakTipLagM / peakMidLagM,
  settleFrames: 180,
  settleTipMeanErrorM,
  finite,
  thresholds,
  failures,
  status: failures.length ? 'FAIL' : 'PASS',
};
fs.writeFileSync(output, `${JSON.stringify(report, null, 2)}\n`);
console.log(JSON.stringify({ output, status: report.status, failures, peakRootErrorM, peakTipLagM, tipToMidLagRatio: report.tipToMidLagRatio, settleTipMeanErrorM }));
if (failures.length) process.exitCode = 2;
