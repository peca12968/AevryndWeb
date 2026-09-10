import fs from 'node:fs';
import path from 'node:path';
import { createRuntimeGroom, decodeRuntimeGroom } from '../src/hair-groom-format.js';

const directory = process.env.AEVRYND_RUNTIME_GROOM_DIR;
if (!directory) throw new Error('AEVRYND_RUNTIME_GROOM_DIR is required');
const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'manifest.json'), 'utf8'));
const read = file => {
  const value = fs.readFileSync(path.join(directory, file));
  return value.buffer.slice(value.byteOffset, value.byteOffset + value.byteLength);
};
const decoded = decodeRuntimeGroom(manifest, {
  guides: read(manifest.files.guides), followGuide: read(manifest.files.followGuide),
  followOffsets: read(manifest.files.followOffsets),
  followCollisionNormals: read(manifest.files.followCollisionNormals),
  followContactHeadWeights: read(manifest.files.followContactHeadWeights),
});
const variants = [
  { id: 'control', root: 0.16, tip: 0.035 },
  { id: 'balanced', root: 0.13, tip: 0.014 },
  { id: 'loose', root: 0.11, tip: 0.007 },
  { id: 'flowing', root: 0.09, tip: 0.0035 },
];
const results = [];
for (const variant of variants) {
  const runtime = createRuntimeGroom(decoded, {
    damping: 0.075, bendCompliance: 4e-7, collisionMargin: 0.0015,
    shapeStiffnessRoot: variant.root, shapeStiffnessTip: variant.tip,
  });
  const anchors = Float64Array.from(decoded.guides.flatMap(guide => guide[0]));
  const authored = runtime.solver.copyPositions(new Float64Array(runtime.solver.positions.length));
  runtime.solver.setWind(0, 0, 0);
  for (let frame = 0; frame < 120; frame++) runtime.solver.advance(1 / 30, anchors);
  let staticDisplacement = 0;
  for (let index = 0; index < authored.length; index += 3) staticDisplacement = Math.max(staticDisplacement, Math.hypot(
    runtime.solver.positions[index] - authored[index], runtime.solver.positions[index + 1] - authored[index + 1],
    runtime.solver.positions[index + 2] - authored[index + 2]));
  const restTips = [];
  for (let guide = 0; guide < runtime.solver.offsets.length - 1; guide++) {
    const tip = (runtime.solver.offsets[guide + 1] - 1) * 3;
    restTips.push([runtime.solver.positions[tip], runtime.solver.positions[tip + 1], runtime.solver.positions[tip + 2]]);
  }
  let tipMotion = 0;
  for (let frame = 0; frame < 60; frame++) {
    runtime.solver.setWind(Math.sin(frame / 8) * 2.4, Math.cos(frame / 11) * 0.32, 0);
    runtime.solver.advance(1 / 30, anchors);
    for (let guide = 0; guide < runtime.solver.offsets.length - 1; guide++) {
      const tip = (runtime.solver.offsets[guide + 1] - 1) * 3;
      tipMotion = Math.max(tipMotion, Math.hypot(runtime.solver.positions[tip] - restTips[guide][0],
        runtime.solver.positions[tip + 1] - restTips[guide][1], runtime.solver.positions[tip + 2] - restTips[guide][2]));
    }
  }
  results.push({ ...variant, maximumStaticGuideDisplacementM: staticDisplacement, maximumTipMotionM: tipMotion });
}
console.log(JSON.stringify(results));
