import { GuideFollowExpander, HairGuideSolver } from './hair-dynamics.js';

function assertLength(name, array, expected) {
  if (array.length !== expected) throw new RangeError(`${name} contains ${array.length} values; expected ${expected}`);
}

export function decodeRuntimeGroom(manifest, buffers) {
  if (manifest?.format !== 'aevrynd-runtime-groom-v1') throw new TypeError('unsupported Aevrynd groom format');
  const guideValues = new Float32Array(buffers.guides);
  const followGuide = new Uint16Array(buffers.followGuide);
  const followOffsets = new Float32Array(buffers.followOffsets);
  const followCollisionNormals = buffers.followCollisionNormals
    ? new Int8Array(buffers.followCollisionNormals)
    : null;
  const followContactHeadWeights = buffers.followContactHeadWeights
    ? new Uint8Array(buffers.followContactHeadWeights)
    : null;
  const guideCount = manifest.simulation.guideCount;
  const guidePoints = manifest.simulation.pointsPerGuide;
  const curveCount = manifest.render.curveCount;
  const curvePoints = manifest.render.pointsPerCurve;
  assertLength('simulation guides', guideValues, guideCount * guidePoints * 3);
  assertLength('follow guide map', followGuide, curveCount);
  assertLength('follow offsets', followOffsets, curveCount * curvePoints * 3);
  if (followCollisionNormals) assertLength('follow collision normals', followCollisionNormals, curveCount * curvePoints * 3);
  if (followContactHeadWeights) assertLength('follow contact head weights', followContactHeadWeights, curveCount * curvePoints);
  const guides = [];
  let cursor = 0;
  for (let guide = 0; guide < guideCount; guide++) {
    const points = [];
    for (let point = 0; point < guidePoints; point++) points.push([guideValues[cursor++], guideValues[cursor++], guideValues[cursor++]]);
    guides.push(points);
  }
  const follows = [];
  cursor = 0;
  for (let curve = 0; curve < curveCount; curve++) {
    const offsets = [];
    for (let point = 0; point < curvePoints; point++) offsets.push([followOffsets[cursor++], followOffsets[cursor++], followOffsets[cursor++]]);
    follows.push({ guide: followGuide[curve], offsets });
  }
  return { manifest, guides, follows, followCollisionNormals, followContactHeadWeights };
}

export function createRuntimeGroom(decoded, solverOptions = {}) {
  const solver = new HairGuideSolver(decoded.guides, {
    fixedStep: 1 / decoded.manifest.simulation.fixedStepHz,
    constraintIterations: decoded.manifest.simulation.constraintIterations,
    colliders: decoded.manifest.collision,
    gravity: decoded.manifest.simulation.gravity,
    posePivot: decoded.manifest.contactPose?.pivot,
    shapeStiffnessRoot: decoded.manifest.simulation.shapeStiffnessRoot,
    shapeStiffnessTip: decoded.manifest.simulation.shapeStiffnessTip,
    ...solverOptions,
  });
  return { solver, follows: new GuideFollowExpander(
    solver,
    decoded.follows,
    decoded.followCollisionNormals,
    decoded.followContactHeadWeights,
  ) };
}

export async function loadRuntimeGroom(manifestUrl, fetchImpl = fetch, solverOptions = {}) {
  const manifestResponse = await fetchImpl(manifestUrl);
  if (!manifestResponse.ok) throw new Error(`failed to load groom manifest: ${manifestResponse.status}`);
  const manifest = await manifestResponse.json();
  const base = new URL('.', manifestResponse.url || manifestUrl);
  const entries = await Promise.all(Object.entries(manifest.files).map(async ([key, file]) => {
    const response = await fetchImpl(new URL(file, base));
    if (!response.ok) throw new Error(`failed to load groom ${key}: ${response.status}`);
    return [key, await response.arrayBuffer()];
  }));
  return createRuntimeGroom(decodeRuntimeGroom(manifest, Object.fromEntries(entries)), solverOptions);
}
