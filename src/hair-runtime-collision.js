import * as THREE from 'three';
import { MeshBVH } from 'three-mesh-bvh';


function findBody(root) {
  let selected = null;
  root.traverse(node => {
    if (!node.isMesh || !node.geometry?.attributes?.position) return;
    const names = (Array.isArray(node.material) ? node.material : [node.material]).map(material => material?.name?.toLowerCase() || '');
    if (!names.some(name => name.includes('skin'))) return;
    if (!selected || node.geometry.attributes.position.count > selected.geometry.attributes.position.count) selected = node;
  });
  if (!selected) throw new Error('owned skin body mesh was not found for hair collision audit');
  return selected;
}

function bakeWorldGeometry(mesh) {
  mesh.updateWorldMatrix(true, false);
  if (mesh.isSkinnedMesh) mesh.skeleton.update();
  const source = mesh.geometry;
  const positions = new Float32Array(source.attributes.position.count * 3);
  const normals = new Float32Array(source.attributes.position.count * 3);
  const point = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const normalMatrix = new THREE.Matrix3().getNormalMatrix(mesh.matrixWorld);
  for (let index = 0; index < source.attributes.position.count; index++) {
    mesh.getVertexPosition(index, point).applyMatrix4(mesh.matrixWorld).toArray(positions, index * 3);
    normal.fromBufferAttribute(source.attributes.normal, index).applyNormalMatrix(normalMatrix).normalize().toArray(normals, index * 3);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
  if (source.index) geometry.setIndex(new THREE.BufferAttribute(new source.index.array.constructor(source.index.array), 1));
  else geometry.setIndex(Array.from({ length: source.attributes.position.count }, (_, index) => index));
  return geometry;
}

export function auditDynamicHairBodyCollision(root, runtime, hairMesh, frames = [1, 11, 20, 21, 31, 33, 41, 51, 61]) {
  root.updateMatrixWorld(true);
  hairMesh.updateWorldMatrix(true, false);
  const bodyMesh = findBody(root);
  const bodyMatrixDeterminant = bodyMesh.matrixWorld.determinant();
  const body = bakeWorldGeometry(bodyMesh);
  const tree = new MeshBVH(body, { targetLeafSize: 8 });
  const closest = { point: new THREE.Vector3() };
  const point = new THREE.Vector3();
  const delta = new THREE.Vector3();
  const surfaceNormal = new THREE.Vector3();
  const normalA = new THREE.Vector3();
  const normalB = new THREE.Vector3();
  const normalC = new THREE.Vector3();
  const normalAttribute = body.attributes.normal;
  const bodyIndex = body.index;
  const frameResults = [];
  let penetrations = 0;
  let minimumSignedClearanceM = Infinity;
  const worst = [];
  const started = performance.now();
  for (const frame of frames) {
    const positions = runtime.evaluateFrame(frame);
    let framePenetrations = 0;
    let frameMinimumSignedClearanceM = Infinity;
    for (let index = 0; index < positions.length; index += 3) {
      point.fromArray(positions, index).applyMatrix4(hairMesh.matrixWorld);
      tree.closestPointToPoint(point, closest);
      const triangle = closest.faceIndex * 3;
      const a = bodyIndex.getX(triangle);
      const b = bodyIndex.getX(triangle + 1);
      const c = bodyIndex.getX(triangle + 2);
      surfaceNormal.copy(normalA.fromBufferAttribute(normalAttribute, a))
        .add(normalB.fromBufferAttribute(normalAttribute, b))
        .add(normalC.fromBufferAttribute(normalAttribute, c)).normalize();
      const signed = delta.copy(point).sub(closest.point).dot(surfaceNormal);
      if (signed < -0.00005) {
        worst.push({ frame, pointIndex: index / 3, signedClearanceM: signed, point: point.toArray(), closest: closest.point.toArray(), normal: surfaceNormal.toArray() });
        worst.sort((a, b) => a.signedClearanceM - b.signedClearanceM);
        if (worst.length > 12) worst.length = 12;
      }
      frameMinimumSignedClearanceM = Math.min(frameMinimumSignedClearanceM, signed);
      if (signed < -0.00005) framePenetrations++;
    }
    penetrations += framePenetrations;
    minimumSignedClearanceM = Math.min(minimumSignedClearanceM, frameMinimumSignedClearanceM);
    frameResults.push({ frame, penetrations: framePenetrations, minimumSignedClearanceM: frameMinimumSignedClearanceM });
  }
  body.dispose();
  return {
    bodyMesh: bodyMesh.name,
    bodyVertices: body.attributes.position.count,
    bodyTriangles: body.index.count / 3,
    bodyMatrixDeterminant,
    frames: frameResults,
    pointInstances: frames.length * runtime.manifest.geometry.pointCount,
    penetrations,
    minimumSignedClearanceM,
    worst,
    elapsedMs: performance.now() - started,
    thresholdM: -0.00005,
    status: penetrations === 0 ? 'PASS' : 'FAIL',
  };
}
