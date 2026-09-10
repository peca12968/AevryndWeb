import fs from 'node:fs';
import path from 'node:path';
import { performance } from 'node:perf_hooks';
import { createRuntimeGroom, decodeRuntimeGroom } from '../src/hair-groom-format.js';

const directory = process.env.AEVRYND_RUNTIME_GROOM_DIR;
if (!directory) throw new Error('AEVRYND_RUNTIME_GROOM_DIR is required');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));
const read = file => {
  const value = fs.readFileSync(path.join(directory, file));
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
};
const decoded = decodeRuntimeGroom(manifest, {
  guides: read(manifest.files.guides),
  followGuide: read(manifest.files.followGuide),
  followOffsets: read(manifest.files.followOffsets),
  followCollisionNormals: read(manifest.files.followCollisionNormals),
  followContactHeadWeights: read(manifest.files.followContactHeadWeights),
});
const runtime = createRuntimeGroom(decoded, { damping: 0.09, bendCompliance: 4e-7, collisionMargin: 0.0015 });
const anchors = Float64Array.from(decoded.guides.flatMap(guide => guide[0]));
let output;
for (let index = 0; index < 20; index++) {
  runtime.solver.advance(1 / 30, anchors);
  output = runtime.follows.write(output);
}
const frames = 50;
let start = performance.now();
for (let index = 0; index < frames; index++) runtime.solver.advance(1 / 30, anchors);
const solverMs = (performance.now() - start) / frames;
start = performance.now();
for (let index = 0; index < frames; index++) output = runtime.follows.write(output);
const followMs = (performance.now() - start) / frames;
let contactPoints = 0;
for (let point = 0; point < decoded.followCollisionNormals.length; point += 3) {
  if (decoded.followCollisionNormals[point]
    || decoded.followCollisionNormals[point + 1]
    || decoded.followCollisionNormals[point + 2]) contactPoints++;
}
console.log(JSON.stringify({ solverMs, followMs, totalMs: solverMs + followMs, contactPoints,
  pointCount: runtime.follows.pointCount, contactPercent: contactPoints / runtime.follows.pointCount * 100 }));
