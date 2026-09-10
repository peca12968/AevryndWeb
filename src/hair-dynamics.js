const EPSILON = 1e-9;

function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

function length3(x, y, z) {
  return Math.sqrt(x * x + y * y + z * z);
}

function normalize3(x, y, z) {
  const length = length3(x, y, z);
  return length > EPSILON ? [x / length, y / length, z / length] : [0, 0, 0];
}

function closestCapsulePoint(px, py, pz, collider) {
  const abx = collider.b[0] - collider.a[0];
  const aby = collider.b[1] - collider.a[1];
  const abz = collider.b[2] - collider.a[2];
  const denominator = abx * abx + aby * aby + abz * abz;
  const t = denominator > EPSILON
    ? clamp(((px - collider.a[0]) * abx + (py - collider.a[1]) * aby + (pz - collider.a[2]) * abz) / denominator, 0, 1)
    : 0;
  return [collider.a[0] + abx * t, collider.a[1] + aby * t, collider.a[2] + abz * t];
}

function projectCollider(positions, offset, collider, clearance) {
  const px = positions[offset], py = positions[offset + 1], pz = positions[offset + 2];
  const center = collider.shape === 'capsule'
    ? closestCapsulePoint(px, py, pz, collider)
    : collider.center;
  let dx = px - center[0], dy = py - center[1], dz = pz - center[2];
  let distance = length3(dx, dy, dz);
  const required = collider.radius + clearance;
  if (distance >= required) return 0;
  if (distance < EPSILON) {
    dx = 0; dy = -1; dz = 0; distance = 1;
  }
  const scale = required / distance;
  positions[offset] = center[0] + dx * scale;
  positions[offset + 1] = center[1] + dy * scale;
  positions[offset + 2] = center[2] + dz * scale;
  return required - distance;
}

export class HairGuideSolver {
  constructor(guides, options = {}) {
    if (!Array.isArray(guides) || guides.some(guide => !Array.isArray(guide) || guide.length < 2)) {
      throw new TypeError('guides must contain arrays of at least two [x,y,z] points');
    }
    this.fixedStep = options.fixedStep ?? 1 / 120;
    this.maxSubsteps = options.maxSubsteps ?? 8;
    this.constraintIterations = options.constraintIterations ?? 6;
    this.damping = options.damping ?? 0.055;
    this.stretchCompliance = options.stretchCompliance ?? 0;
    this.bendCompliance = options.bendCompliance ?? 2e-7;
    this.shapeStiffnessRoot = options.shapeStiffnessRoot ?? 0.16;
    this.shapeStiffnessTip = options.shapeStiffnessTip ?? 0.035;
    this.gravity = options.gravity ?? [0, 0, -9.81];
    this.wind = [0, 0, 0];
    this.poseRotation = new Float64Array([1, 0, 0, 0, 1, 0, 0, 0, 1]);
    this.posePivot = options.posePivot ?? [0, 0, 0];
    this.contactPoseBlendZ = options.contactPoseBlendZ ?? [Infinity, Infinity];
    this.collisionMargin = options.collisionMargin ?? 0.001;
    this.colliders = options.colliders ?? [];
    this.accumulator = 0;
    this.offsets = new Uint32Array(guides.length + 1);
    let pointCount = 0;
    guides.forEach((guide, index) => {
      this.offsets[index] = pointCount;
      pointCount += guide.length;
    });
    this.offsets[guides.length] = pointCount;
    this.positions = new Float64Array(pointCount * 3);
    this.previous = new Float64Array(pointCount * 3);
    this.restRelative = new Float64Array(pointCount * 3);
    this.anchors = new Float64Array(guides.length * 3);
    this.previousAnchors = new Float64Array(guides.length * 3);
    this.restLengths = new Float64Array(pointCount - guides.length);
    this.restBends = new Float64Array(Math.max(0, pointCount - guides.length * 2));
    let segment = 0, bend = 0;
    guides.forEach((guide, guideIndex) => {
      guide.forEach((point, pointIndex) => {
        const global = this.offsets[guideIndex] + pointIndex;
        this.positions.set(point, global * 3);
        this.previous.set(point, global * 3);
        this.restRelative.set([
          point[0] - guide[0][0],
          point[1] - guide[0][1],
          point[2] - guide[0][2],
        ], global * 3);
        if (pointIndex === 0) {
          this.anchors.set(point, guideIndex * 3);
          this.previousAnchors.set(point, guideIndex * 3);
        }
        if (pointIndex > 0) {
          const before = guide[pointIndex - 1];
          this.restLengths[segment++] = length3(point[0] - before[0], point[1] - before[1], point[2] - before[2]);
        }
        if (pointIndex > 1) {
          const before = guide[pointIndex - 2];
          this.restBends[bend++] = length3(point[0] - before[0], point[1] - before[1], point[2] - before[2]);
        }
      });
    });
    this.rebuildCollisionClearances();
  }

  setColliders(colliders) {
    this.colliders = colliders;
    this.rebuildCollisionClearances();
  }

  rebuildCollisionClearances() {
    this.collisionClearances = new Float64Array(this.positions.length / 3 * this.colliders.length);
    for (let point = 0; point < this.positions.length / 3; point++) {
      const offset = point * 3;
      for (let colliderIndex = 0; colliderIndex < this.colliders.length; colliderIndex++) {
        const restDistance = signedColliderDistance([
          this.positions[offset], this.positions[offset + 1], this.positions[offset + 2],
        ], this.colliders[colliderIndex]);
        // Coarse runtime proxies can overlap a mesh-validated authored groom. Preserve
        // that safe bind-pose clearance while preventing any deeper inward movement.
        this.collisionClearances[point * this.colliders.length + colliderIndex] = Math.min(this.collisionMargin, restDistance);
      }
    }
  }

  setWind(x, y, z) {
    this.wind[0] = x; this.wind[1] = y; this.wind[2] = z;
  }

  setPoseRotation(matrix, pivot = this.posePivot) {
    if (!matrix || matrix.length !== 9) throw new RangeError('pose rotation must contain 9 matrix values');
    this.poseRotation.set(matrix);
    this.posePivot = [pivot[0], pivot[1], pivot[2]];
  }

  setAnchors(flatPositions) {
    if (flatPositions.length !== this.anchors.length) throw new RangeError('anchor count does not match guide count');
    this.anchors.set(flatPositions);
  }

  advance(deltaSeconds, anchors = null) {
    if (anchors) this.setAnchors(anchors);
    this.accumulator += Math.min(Math.max(deltaSeconds, 0), this.fixedStep * this.maxSubsteps);
    let steps = 0;
    while (this.accumulator + EPSILON >= this.fixedStep && steps < this.maxSubsteps) {
      this.substep(this.fixedStep);
      this.accumulator -= this.fixedStep;
      steps++;
    }
    return steps;
  }

  substep(dt) {
    const dt2 = dt * dt;
    let guideIndex = 0;
    for (let start = this.offsets[0]; guideIndex < this.offsets.length - 1; guideIndex++, start = this.offsets[guideIndex]) {
      const end = this.offsets[guideIndex + 1];
      const anchorOffset = guideIndex * 3;
      const rootOffset = start * 3;
      const rootDx = this.anchors[anchorOffset] - this.previousAnchors[anchorOffset];
      const rootDy = this.anchors[anchorOffset + 1] - this.previousAnchors[anchorOffset + 1];
      const rootDz = this.anchors[anchorOffset + 2] - this.previousAnchors[anchorOffset + 2];
      const count = end - start;
      for (let point = start + 1; point < end; point++) {
        const offset = point * 3;
        const t = (point - start) / (count - 1);
        const shock = (1 - t) * (1 - t) * 0.82;
        const x = this.positions[offset], y = this.positions[offset + 1], z = this.positions[offset + 2];
        const vx = (x - this.previous[offset]) * (1 - this.damping);
        const vy = (y - this.previous[offset + 1]) * (1 - this.damping);
        const vz = (z - this.previous[offset + 2]) * (1 - this.damping);
        this.previous[offset] = x;
        this.previous[offset + 1] = y;
        this.previous[offset + 2] = z;
        this.positions[offset] = x + vx + (this.gravity[0] + this.wind[0]) * dt2 + rootDx * shock;
        this.positions[offset + 1] = y + vy + (this.gravity[1] + this.wind[1]) * dt2 + rootDy * shock;
        this.positions[offset + 2] = z + vz + (this.gravity[2] + this.wind[2]) * dt2 + rootDz * shock;
      }
      this.positions[rootOffset] = this.anchors[anchorOffset];
      this.positions[rootOffset + 1] = this.anchors[anchorOffset + 1];
      this.positions[rootOffset + 2] = this.anchors[anchorOffset + 2];
      for (let point = start + 1; point < end; point++) {
        const offset = point * 3;
        const t = (point - start) / (count - 1);
        const stiffness = this.shapeStiffnessTip * t + this.shapeStiffnessRoot * (1 - t) * (1 - t);
        const rx = this.restRelative[offset], ry = this.restRelative[offset + 1], rz = this.restRelative[offset + 2];
        const matrix = this.poseRotation;
        const targetX = this.anchors[anchorOffset] + matrix[0] * rx + matrix[1] * ry + matrix[2] * rz;
        const targetY = this.anchors[anchorOffset + 1] + matrix[3] * rx + matrix[4] * ry + matrix[5] * rz;
        const targetZ = this.anchors[anchorOffset + 2] + matrix[6] * rx + matrix[7] * ry + matrix[8] * rz;
        this.positions[offset] += (targetX - this.positions[offset]) * stiffness;
        this.positions[offset + 1] += (targetY - this.positions[offset + 1]) * stiffness;
        this.positions[offset + 2] += (targetZ - this.positions[offset + 2]) * stiffness;
      }
    }

    const stretchAlpha = this.stretchCompliance / dt2;
    const bendAlpha = this.bendCompliance / dt2;
    for (let iteration = 0; iteration < this.constraintIterations; iteration++) {
      let segment = 0, bend = 0;
      for (let guide = 0; guide < this.offsets.length - 1; guide++) {
        const start = this.offsets[guide], end = this.offsets[guide + 1];
        for (let point = start + 1; point < end; point++, segment++) {
          this.solveDistance(point - 1, point, this.restLengths[segment], point - 1 === start, stretchAlpha);
        }
        for (let point = start + 2; point < end; point++, bend++) {
          this.solveDistance(point - 2, point, this.restBends[bend], point - 2 === start, bendAlpha);
        }
        const anchorOffset = guide * 3, rootOffset = start * 3;
        this.positions[rootOffset] = this.anchors[anchorOffset];
        this.positions[rootOffset + 1] = this.anchors[anchorOffset + 1];
        this.positions[rootOffset + 2] = this.anchors[anchorOffset + 2];
        // Distance and bend constraints in the next iteration would immediately
        // alter an earlier collision projection.  Resolve collision after the
        // final converged iteration so every substep still ends outside all
        // proxies without repeating the same work 24 times.
        if (iteration === this.constraintIterations - 1) {
          for (let point = start + 1; point < end; point++) {
            const offset = point * 3;
            for (let colliderIndex = 0; colliderIndex < this.colliders.length; colliderIndex++) {
              projectCollider(
                this.positions,
                offset,
                this.colliders[colliderIndex],
                this.collisionClearances[point * this.colliders.length + colliderIndex],
              );
            }
          }
        }
      }
    }
    this.previousAnchors.set(this.anchors);
  }

  solveDistance(first, second, restLength, firstFixed, compliance) {
    const a = first * 3, b = second * 3;
    const dx = this.positions[b] - this.positions[a];
    const dy = this.positions[b + 1] - this.positions[a + 1];
    const dz = this.positions[b + 2] - this.positions[a + 2];
    const distance = length3(dx, dy, dz);
    if (distance < EPSILON) return;
    const inverseMass = firstFixed ? 1 : 2;
    const correction = (distance - restLength) / (inverseMass + compliance) / distance;
    if (!firstFixed) {
      this.positions[a] += dx * correction;
      this.positions[a + 1] += dy * correction;
      this.positions[a + 2] += dz * correction;
    }
    this.positions[b] -= dx * correction;
    this.positions[b + 1] -= dy * correction;
    this.positions[b + 2] -= dz * correction;
  }

  copyPositions(target = new Float32Array(this.positions.length)) {
    target.set(this.positions);
    return target;
  }
}

export class GuideFollowExpander {
  constructor(solver, follows, surfaceNormals = null, contactPoseWeights = null) {
    this.solver = solver;
    this.follows = follows;
    this.pointCount = follows.reduce((total, follow) => total + follow.offsets.length, 0);
    this.frameTangents = new Float64Array(solver.positions.length);
    this.frameNormals = new Float64Array(solver.positions.length);
    this.frameBinormals = new Float64Array(solver.positions.length);
    this.surfaceNormals = surfaceNormals;
    this.contactPoseWeights = contactPoseWeights;
    this.restPositions = null;
    // Preserve the authored rest distance for every proxy, then stop free
    // follower tips from moving any deeper into head, neck, shoulders or chest.
    // Long hair needs all four regions even when near-scalp contact normals exist.
    this.followerColliders = solver.colliders;
    this.collisionClearances = null;
    if (surfaceNormals && surfaceNormals.length !== this.pointCount * 3) {
      throw new RangeError('surface normal count must match rendered follow point count');
    }
    if (contactPoseWeights && contactPoseWeights.length !== this.pointCount) {
      throw new RangeError('contact pose weight count must match rendered follow point count');
    }
    if (solver.colliders.length || surfaceNormals) {
      const rest = this.write();
      this.restPositions = Float32Array.from(rest);
      if (this.followerColliders.length) {
        this.collisionClearances = new Float32Array(this.pointCount * this.followerColliders.length);
        for (let point = 0; point < this.pointCount; point++) {
          const offset = point * 3;
          for (let collider = 0; collider < this.followerColliders.length; collider++) {
            const restDistance = signedColliderDistance(
              [rest[offset], rest[offset + 1], rest[offset + 2]],
              this.followerColliders[collider],
            );
            this.collisionClearances[point * this.followerColliders.length + collider] = Math.min(
              solver.collisionMargin,
              restDistance,
            );
          }
        }
      }
    }
  }

  write(target = new Float32Array(this.pointCount * 3)) {
    // Every follower mapped to a guide uses the same local frame.  Build those
    // frames once per simulated point instead of repeating cross products and
    // normalizations for every rendered strand.
    for (let guide = 0; guide < this.solver.offsets.length - 1; guide++) {
      const start = this.solver.offsets[guide], end = this.solver.offsets[guide + 1];
      for (let point = start; point < end; point++) {
        const previous = Math.max(start, point - 1) * 3;
        const next = Math.min(end - 1, point + 1) * 3;
        const offset = point * 3;
        let tx = this.solver.positions[next] - this.solver.positions[previous];
        let ty = this.solver.positions[next + 1] - this.solver.positions[previous + 1];
        let tz = this.solver.positions[next + 2] - this.solver.positions[previous + 2];
        const tangentLength = Math.sqrt(tx * tx + ty * ty + tz * tz) || 1;
        tx /= tangentLength; ty /= tangentLength; tz /= tangentLength;

        let nx, ny, nz;
        if (Math.abs(tz) < 0.92) {
          nx = ty; ny = -tx; nz = 0;
        } else {
          nx = -tz; ny = 0; nz = tx;
        }
        const normalLength = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
        nx /= normalLength; ny /= normalLength; nz /= normalLength;
        const bx = ty * nz - tz * ny;
        const by = tz * nx - tx * nz;
        const bz = tx * ny - ty * nx;

        this.frameTangents[offset] = tx;
        this.frameTangents[offset + 1] = ty;
        this.frameTangents[offset + 2] = tz;
        this.frameNormals[offset] = nx;
        this.frameNormals[offset + 1] = ny;
        this.frameNormals[offset + 2] = nz;
        this.frameBinormals[offset] = bx;
        this.frameBinormals[offset + 1] = by;
        this.frameBinormals[offset + 2] = bz;
      }
    }

    let cursor = 0, outputPoint = 0;
    for (const follow of this.follows) {
      const start = this.solver.offsets[follow.guide];
      const end = this.solver.offsets[follow.guide + 1];
      const count = end - start;
      if (follow.offsets.length !== count) throw new RangeError('follow point count must match its guide');
      for (let local = 0; local < count; local++) {
        const point = start + local;
        const positionOffset = cursor;
        if (this.surfaceNormals && this.restPositions
          && (this.surfaceNormals[positionOffset]
            || this.surfaceNormals[positionOffset + 1]
            || this.surfaceNormals[positionOffset + 2])) {
          // A contact point is pinned to its mesh-audited authored location
          // (with the interpolated head pose below).  Skip frame expansion and
          // coarse proxy collision because both results would be overwritten.
          const restX = this.restPositions[positionOffset];
          const restY = this.restPositions[positionOffset + 1];
          const restZ = this.restPositions[positionOffset + 2];
          const poseWeight = this.contactPoseWeights ? this.contactPoseWeights[outputPoint] / 255 : 0;
          const pivot = this.solver.posePivot;
          const matrix = this.solver.poseRotation;
          const rx = restX - pivot[0], ry = restY - pivot[1], rz = restZ - pivot[2];
          const rotatedX = pivot[0] + matrix[0] * rx + matrix[1] * ry + matrix[2] * rz;
          const rotatedY = pivot[1] + matrix[3] * rx + matrix[4] * ry + matrix[5] * rz;
          const rotatedZ = pivot[2] + matrix[6] * rx + matrix[7] * ry + matrix[8] * rz;
          // Quantized authored surface normals provide a conservative skin for
          // small differences between interpolated bone weights and the fully
          // deformed body mesh.  The bias is zero at bind pose and stays below
          // one millimetre throughout the audited 18 degree head turn.
          const normalScale = 1 / 127;
          const snx = this.surfaceNormals[positionOffset] * normalScale;
          const sny = this.surfaceNormals[positionOffset + 1] * normalScale;
          const snz = this.surfaceNormals[positionOffset + 2] * normalScale;
          let pnx = snx + (matrix[0] * snx + matrix[1] * sny + matrix[2] * snz - snx) * poseWeight;
          let pny = sny + (matrix[3] * snx + matrix[4] * sny + matrix[5] * snz - sny) * poseWeight;
          let pnz = snz + (matrix[6] * snx + matrix[7] * sny + matrix[8] * snz - snz) * poseWeight;
          const normalLength = Math.sqrt(pnx * pnx + pny * pny + pnz * pnz) || 1;
          pnx /= normalLength; pny /= normalLength; pnz /= normalLength;
          const contactSkin = 0.0022 * Math.hypot(matrix[1], matrix[3]);
          target[cursor++] = restX + (rotatedX - restX) * poseWeight + pnx * contactSkin;
          target[cursor++] = restY + (rotatedY - restY) * poseWeight + pny * contactSkin;
          target[cursor++] = restZ + (rotatedZ - restZ) * poseWeight + pnz * contactSkin;
          outputPoint++;
          continue;
        }
        const [u, v, w = 0] = follow.offsets[local];
        const source = point * 3;
        target[cursor++] = this.solver.positions[source] + this.frameNormals[source] * u + this.frameBinormals[source] * v + this.frameTangents[source] * w;
        target[cursor++] = this.solver.positions[source + 1] + this.frameNormals[source + 1] * u + this.frameBinormals[source + 1] * v + this.frameTangents[source + 1] * w;
        target[cursor++] = this.solver.positions[source + 2] + this.frameNormals[source + 2] * u + this.frameBinormals[source + 2] * v + this.frameTangents[source + 2] * w;
        if (this.collisionClearances) {
          for (let collider = 0; collider < this.followerColliders.length; collider++) {
            projectCollider(
              target,
              positionOffset,
              this.followerColliders[collider],
              this.collisionClearances[outputPoint * this.followerColliders.length + collider],
            );
          }
        }
        outputPoint++;
      }
    }
    return target;
  }
}

export function signedColliderDistance(point, collider) {
  const center = collider.shape === 'capsule'
    ? closestCapsulePoint(point[0], point[1], point[2], collider)
    : collider.center;
  return length3(point[0] - center[0], point[1] - center[1], point[2] - center[2]) - collider.radius;
}
