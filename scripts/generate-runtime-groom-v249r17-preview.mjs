import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRuntimeGroom, decodeRuntimeGroom } from '../src/hair-groom-format.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const directory = process.env.AEVRYND_RUNTIME_GROOM_DIR
  ?? path.join(root, 'assets-source/aevrynd-character/runtime-groom-v249r17');
const outputDirectory = process.env.AEVRYND_RUNTIME_GROOM_PREVIEW_DIR
  ?? path.join(root, '..', 'Temp/female-realism/v249-mainline-hair-r17-dynamics');
fs.mkdirSync(outputDirectory, { recursive: true });
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));

function readArrayBuffer(file) {
  const value = fs.readFileSync(path.join(directory, file));
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
}

const decoded = decodeRuntimeGroom(manifest, {
  guides: readArrayBuffer(manifest.files.guides),
  followGuide: readArrayBuffer(manifest.files.followGuide),
  followOffsets: readArrayBuffer(manifest.files.followOffsets),
  followCollisionNormals: readArrayBuffer(manifest.files.followCollisionNormals),
  followContactHeadWeights: readArrayBuffer(manifest.files.followContactHeadWeights),
});
const runtime = createRuntimeGroom(decoded, { damping: 0.09, bendCompliance: 4e-7, collisionMargin: 0.0015 });
const anchors = Float64Array.from(decoded.guides.flatMap(guide => guide[0]));
const baseAnchors = Float64Array.from(anchors);
const pivot = manifest.contactPose.pivot;
for (let frame = 0; frame < 120; frame++) runtime.solver.advance(1 / 30, anchors);

const saved = [];
function saveState(frame, yaw) {
  const positions = runtime.follows.write();
  const filename = `dynamic-${String(frame).padStart(3, '0')}.f32`;
  fs.writeFileSync(path.join(outputDirectory, filename), Buffer.from(positions.buffer));
  saved.push({ frame, filename, yawDeg: yaw * 180 / Math.PI });
}

saveState(0, 0);
for (let frame = 1; frame <= 60; frame++) {
  const yaw = Math.sin(frame * Math.PI / 30) * Math.PI / 10;
  const cosine = Math.cos(yaw), sine = Math.sin(yaw);
  const rotation = [cosine, -sine, 0, sine, cosine, 0, 0, 0, 1];
  runtime.solver.setPoseRotation(rotation, pivot);
  for (let guide = 0; guide < decoded.guides.length; guide++) {
    const offset = guide * 3;
    const x = baseAnchors[offset] - pivot[0];
    const y = baseAnchors[offset + 1] - pivot[1];
    anchors[offset] = pivot[0] + cosine * x - sine * y;
    anchors[offset + 1] = pivot[1] + sine * x + cosine * y;
    anchors[offset + 2] = baseAnchors[offset + 2];
  }
  const impulse = frame <= 36 ? Math.sin(frame / 8) * 2.4 : Math.sin(frame / 8) * 0.7;
  runtime.solver.setWind(impulse, 0.32 * Math.cos(frame / 11), 0);
  runtime.solver.advance(1 / 30, anchors);
  if ([12, 24, 36, 60].includes(frame)) saveState(frame, yaw);
}

fs.writeFileSync(path.join(outputDirectory, 'frames.json'), JSON.stringify({
  source: directory,
  curveCount: manifest.render.curveCount,
  pointsPerCurve: manifest.render.pointsPerCurve,
  mainCurveCount: 14396,
  fillCurveCount: 608,
  saved,
}, null, 2));
console.log(JSON.stringify({ outputDirectory, saved }));
