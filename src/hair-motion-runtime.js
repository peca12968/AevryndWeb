const TAU = Math.PI * 2;

function assertLength(name, array, expected) {
  if (array.length !== expected) throw new RangeError(`${name} contains ${array.length} values; expected ${expected}`);
}

export function decodeRuntimeHairMotion(manifest, buffers) {
  if (manifest?.format !== 'aevrynd-runtime-hair-motion-v1') throw new TypeError('unsupported Aevrynd hair motion format');
  const curveOffsets = new Uint32Array(buffers.curveOffsets);
  const basePositions = new Float32Array(buffers.basePositions);
  const motionVectors = new Float32Array(buffers.motionVectors);
  const curvePhases = new Float32Array(buffers.curvePhases);
  const radii = new Float32Array(buffers.radii);
  const { curveCount, pointCount } = manifest.geometry;
  assertLength('curve offsets', curveOffsets, curveCount + 1);
  assertLength('base positions', basePositions, pointCount * 3);
  assertLength('motion vectors', motionVectors, pointCount * 3);
  assertLength('curve phases', curvePhases, curveCount);
  assertLength('radii', radii, pointCount);
  if (curveOffsets[0] !== 0 || curveOffsets[curveCount] !== pointCount) throw new RangeError('curve offsets do not span all points');
  return { manifest, curveOffsets, basePositions, motionVectors, curvePhases, radii };
}

export class DeterministicHairMotion {
  constructor(decoded) {
    Object.assign(this, decoded);
    this.positions = new Float32Array(this.basePositions);
  }

  evaluateFrame(frame, target = this.positions) {
    if (target.length !== this.basePositions.length) throw new RangeError('target position count does not match groom');
    const cycle = this.manifest.motion.cycleFrames;
    const cycleFrame = ((frame - 1) % cycle + cycle) % cycle;
    const u = cycleFrame / cycle;
    const envelope = Math.sin(Math.PI * u) ** 2;
    const temporalPhase = (frame - 1) * TAU / 48;
    for (let curve = 0; curve < this.curvePhases.length; curve++) {
      const scalar = envelope * (0.55 + 0.45 * Math.sin(temporalPhase + this.curvePhases[curve]));
      const start = this.curveOffsets[curve] * 3;
      const end = this.curveOffsets[curve + 1] * 3;
      for (let index = start; index < end; index++) target[index] = this.basePositions[index] + this.motionVectors[index] * scalar;
    }
    return target;
  }

  evaluateSeconds(seconds, target = this.positions) {
    return this.evaluateFrame(1 + seconds * this.manifest.motion.framesPerSecond, target);
  }
}

export function createLineSegmentIndices(curveOffsets) {
  let segmentCount = 0;
  for (let curve = 0; curve < curveOffsets.length - 1; curve++) segmentCount += Math.max(0, curveOffsets[curve + 1] - curveOffsets[curve] - 1);
  const Type = curveOffsets[curveOffsets.length - 1] > 65535 ? Uint32Array : Uint16Array;
  const indices = new Type(segmentCount * 2);
  let cursor = 0;
  for (let curve = 0; curve < curveOffsets.length - 1; curve++) {
    for (let point = curveOffsets[curve]; point + 1 < curveOffsets[curve + 1]; point++) {
      indices[cursor++] = point;
      indices[cursor++] = point + 1;
    }
  }
  return indices;
}

export async function loadRuntimeHairMotion(manifestUrl, fetchImpl = fetch) {
  const response = await fetchImpl(manifestUrl);
  if (!response.ok) throw new Error(`failed to load hair-motion manifest: ${response.status}`);
  const manifest = await response.json();
  const base = new URL('.', response.url || manifestUrl);
  const entries = await Promise.all(Object.entries(manifest.files).map(async ([key, file]) => {
    const item = await fetchImpl(new URL(file, base));
    if (!item.ok) throw new Error(`failed to load hair-motion ${key}: ${item.status}`);
    return [key, await item.arrayBuffer()];
  }));
  return new DeterministicHairMotion(decodeRuntimeHairMotion(manifest, Object.fromEntries(entries)));
}
