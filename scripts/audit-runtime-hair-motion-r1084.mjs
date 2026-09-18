import fs from 'node:fs';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { DeterministicHairMotion, decodeRuntimeHairMotion } from '../src/hair-motion-runtime.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const directory = path.join(root, 'assets-source/aevrynd-character/runtime-hair-motion-r1084');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));
const buffers = Object.fromEntries(Object.entries(manifest.files).map(([key, file]) => {
  const value = fs.readFileSync(path.join(directory, file));
  return [key, value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength)];
}));
const decoded = decodeRuntimeHairMotion(manifest, buffers);
const runtime = new DeterministicHairMotion(decoded);
const roots = Array.from(decoded.curveOffsets.slice(0, -1));
const tips = Array.from(decoded.curveOffsets.slice(1), value => value - 1);
const distance = (array, point) => {
  const index = point * 3;
  return Math.hypot(array[index] - decoded.basePositions[index], array[index + 1] - decoded.basePositions[index + 1], array[index + 2] - decoded.basePositions[index + 2]);
};
const percentile = (values, fraction) => values.sort((a, b) => a - b)[Math.min(values.length - 1, Math.floor((values.length - 1) * fraction))];
const frameMetrics = {};
for (const frame of [1, 11, 20, 21, 31, 33, 41, 51, 61]) {
  const output = runtime.evaluateFrame(frame);
  const rootMotion = roots.map(point => distance(output, point));
  const tipMotion = tips.map(point => distance(output, point));
  frameMetrics[frame] = { rootMaximumM: Math.max(...rootMotion), tipP95M: percentile(tipMotion, 0.95), tipMaximumM: Math.max(...tipMotion) };
}
for (let frame = 0; frame < 120; frame++) runtime.evaluateFrame(frame + 1);
const measuredFrames = 600;
const started = performance.now();
for (let frame = 0; frame < measuredFrames; frame++) runtime.evaluateFrame(frame + 1);
const averageCpuFrameMs = (performance.now() - started) / measuredFrames;
const binaryBytes = Object.values(buffers).reduce((sum, buffer) => sum + buffer.byteLength, 0);
const finiteOutput = runtime.positions.every(Number.isFinite);
const peak = frameMetrics[21];
const failures = [];
if (!finiteOutput) failures.push('non-finite output');
if (frameMetrics[1].rootMaximumM !== 0 || frameMetrics[61].rootMaximumM !== 0) failures.push('root drift at rest');
if (frameMetrics[61].tipMaximumM > 1e-8) failures.push('frame 61 does not settle');
if (Math.abs(peak.tipP95M - 0.0029608461426921338) > 2e-6) failures.push('frame 21 tip P95 differs from Blender audit');
if (Math.abs(peak.tipMaximumM - 0.003009277125700524) > 2e-6) failures.push('frame 21 maximum differs from Blender audit');
if (averageCpuFrameMs > 5) failures.push('CPU evaluation exceeds 5ms budget');
if (binaryBytes > 3 * 1024 * 1024) failures.push('runtime payload exceeds 3MiB budget');
const report = {
  format: manifest.format,
  curveCount: manifest.geometry.curveCount,
  pointCount: manifest.geometry.pointCount,
  binaryBytes,
  measuredFrames,
  averageCpuFrameMs,
  finiteOutput,
  frameMetrics,
  thresholds: { maximumAverageCpuFrameMs: 5, maximumBinaryBytes: 3 * 1024 * 1024, blenderMetricToleranceM: 2e-6, maximumSettleErrorM: 1e-8 },
  failures,
  status: failures.length ? 'FAIL' : 'PASS',
};
fs.writeFileSync(path.join(directory, 'runtime-audit.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
if (failures.length) process.exitCode = 2;
