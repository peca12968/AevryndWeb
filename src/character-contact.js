import * as THREE from 'three';
import { MeshBVH, getTriangleHitPointInfo } from 'three-mesh-bvh';
import { classifyMaterial } from './character-materials.js';

function bakeRegion(meshes, minimumY) {
  const sources = [], positions = [], indices = [];
  const point = new THREE.Vector3();
  for (const mesh of meshes) {
    const geometry = mesh.geometry;
    const map = new Map();
    const points = [];
    for (let i = 0; i < geometry.attributes.position.count; i++) {
      points.push(mesh.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld));
    }
    for (let i = 0; i < geometry.index.count; i += 3) {
      const tri = [geometry.index.getX(i), geometry.index.getX(i + 1), geometry.index.getX(i + 2)];
      if (tri.every(index => points[index].y < minimumY)) continue;
      for (const index of tri) {
        if (!map.has(index)) {
          map.set(index, sources.length);
          sources.push({ mesh, index });
          point.copy(points[index]); positions.push(point.x, point.y, point.z);
        }
        indices.push(map.get(index));
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  return { geometry, sources };
}

// 同步驗證後才把候選值交給畫面，保留全部其他塑形設定。
export function applyGuardedMorph(root, guard, key, requested) {
  const nodes = [];
  root?.traverse(node => { if (node.morphTargetDictionary) nodes.push({ node, previous: [...node.morphTargetInfluences] }); });
  const set = value => nodes.forEach(({ node }) => {
    const min = node.morphTargetDictionary[`${key}_minimum`], max = node.morphTargetDictionary[`${key}_maximum`];
    if (min !== undefined) node.morphTargetInfluences[min] = Math.max(0, -value / 100);
    if (max !== undefined) node.morphTargetInfluences[max] = Math.max(0, value / 100);
  });
  const restore = () => nodes.forEach(({ node, previous }) => { node.morphTargetInfluences.splice(0, previous.length, ...previous); });
  const first = nodes[0]?.node;
  const previous = first ? ((first.morphTargetInfluences[first.morphTargetDictionary[`${key}_maximum`]] ?? 0)
    - (first.morphTargetInfluences[first.morphTargetDictionary[`${key}_minimum`]] ?? 0)) * 100 : 0;
  if (Math.abs(requested - previous) < 1e-7) return { value: requested, limited: false };
  set(requested);
  if (!guard || guard.isClear()) return { value: requested, limited: false };
  restore();
  let safe = previous, unsafe = requested;
  for (let i = 0; i < 7; i++) {
    const value = (safe + unsafe) / 2;
    set(value);
    if (guard.isClear()) safe = value; else unsafe = value;
  }
  const accepted = requested > previous ? Math.floor(safe) : Math.ceil(safe);
  set(accepted);
  if (guard.isClear()) return { value: accepted, limited: true };
  restore(); guard.refit();
  return { value: previous, limited: true };
}

// 只處理目前網站可變動的臉部塑形；身體、衣物與髮型的靜態接觸在資產重建時修整。
export class CharacterContactGuard {
  constructor(root) {
    root.updateMatrixWorld(true);
    root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
    const bodyMeshes = [], hairMeshes = [];
    root.getObjectByName('Body').traverse(node => { if (node.isMesh) bodyMeshes.push(node); });
    root.traverse(node => {
      if (!node.isMesh) return;
      const material = Array.isArray(node.material) ? node.material[0] : node.material;
      if (['hair', 'scalp', 'flyaways'].includes(classifyMaterial(material.name))) hairMeshes.push(node);
    });
    const body = bakeRegion(bodyMeshes, 1.40);
    const hair = bakeRegion(hairMeshes, 1.38);
    this.bodyGeometry = body.geometry;
    this.bodySources = body.sources;
    this.hairGeometry = hair.geometry;
    this.bodyTree = new MeshBVH(this.bodyGeometry, { targetLeafSize: 8 });
    this.hairGeometry.boundsTree = new MeshBVH(this.hairGeometry, { targetLeafSize: 8 });
    this.identity = new THREE.Matrix4();
    this.point = new THREE.Vector3();
    this.delta = new THREE.Vector3();
    this.closest = { point: new THREE.Vector3() };
    this.hit = {};
    this.anchors = [];
    const hairPositions = this.hairGeometry.attributes.position;
    // 額頭、下顎附近保留內外判斷，防止整片細髮進入身體卻沒有留下邊界交線。
    for (let i = 0; i < hairPositions.count; i++) {
      this.point.fromBufferAttribute(hairPositions, i);
      if (this.point.y < 1.43 || this.point.z < .015 || this.point.y > 1.65) continue;
      if (this.bodyTree.closestPointToPoint(this.point, this.closest, 0, .03)) this.anchors.push(this.point.clone());
    }
  }

  refit() {
    const position = this.bodyGeometry.attributes.position;
    for (let i = 0; i < this.bodySources.length; i++) {
      const source = this.bodySources[i];
      source.mesh.getVertexPosition(source.index, this.point).applyMatrix4(source.mesh.matrixWorld);
      position.setXYZ(i, this.point.x, this.point.y, this.point.z);
    }
    position.needsUpdate = true;
    this.bodyTree.refit();
  }

  isClear() {
    this.refit();
    if (this.bodyTree.intersectsGeometry(this.hairGeometry, this.identity)) return false;
    for (const point of this.anchors) {
      if (!this.bodyTree.closestPointToPoint(point, this.closest, 0, .03)) continue;
      getTriangleHitPointInfo(this.closest.point, this.bodyGeometry, this.closest.faceIndex, this.hit);
      const signed = this.delta.copy(point).sub(this.closest.point).dot(this.hit.face.normal);
      if (signed < -.00004) return false;
    }
    return true;
  }

  dispose() { this.bodyGeometry.dispose(); this.hairGeometry.dispose(); }
}

// 測試與資產驗收共用正式的三角形接触檢查。
export function inspectBodyContact(root, acceptedLayers) {
  root.updateMatrixWorld(true);
  root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
  const meshes = [];
  root.getObjectByName('Body').traverse(mesh => { if (mesh.isMesh) meshes.push(mesh); });
  const body = bakeRegion(meshes, -Infinity).geometry;
  const tree = new MeshBVH(body);
  const hit = {}, result = { point: new THREE.Vector3() }, delta = new THREE.Vector3();
  let inside = 0, minimum = Infinity, samples = 0;
  root.traverse(mesh => {
    if (!mesh.isMesh) return;
    const mat = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    if (!acceptedLayers.includes(classifyMaterial(mat.name))) return;
    const points = [];
    for (let i = 0; i < mesh.geometry.attributes.position.count; i++) {
      points.push(mesh.getVertexPosition(i, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld));
    }
    const check = point => {
      tree.closestPointToPoint(point, result);
      getTriangleHitPointInfo(result.point, body, result.faceIndex, hit);
      const signed = delta.copy(point).sub(result.point).dot(hit.face.normal);
      minimum = Math.min(minimum, signed);
      if (signed < -.00005) inside++;
      samples++;
    };
    points.forEach(check);
    const index = mesh.geometry.index;
    for (let i = 0; i < index.count; i += 3) {
      const a = points[index.getX(i)], b = points[index.getX(i + 1)], c = points[index.getX(i + 2)];
      check(new THREE.Vector3().add(a).add(b).add(c).multiplyScalar(1 / 3));
      check(new THREE.Vector3().addVectors(a, b).multiplyScalar(.5));
      check(new THREE.Vector3().addVectors(b, c).multiplyScalar(.5));
      check(new THREE.Vector3().addVectors(c, a).multiplyScalar(.5));
    }
  });
  body.dispose();
  return { samples, inside, minimum };
}

export function inspectLayerIntersections(root) {
  root.updateMatrixWorld(true);
  root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
  const groups = new Map();
  root.traverse(mesh => {
    if (!mesh.isMesh) return;
    const mat = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    const layer = classifyMaterial(mat.name);
    if (!groups.has(layer)) groups.set(layer, []);
    groups.get(layer).push(mesh);
  });
  const bodyMeshes = [];
  root.getObjectByName('Body').traverse(mesh => { if (mesh.isMesh) bodyMeshes.push(mesh); });
  groups.set('body', bodyMeshes);
  const layers = ['body', 'inner', 'jacket', 'pants', 'scalp', 'hair', 'flyaways'];
  const baked = new Map(layers.map(layer => {
    const geometry = bakeRegion(groups.get(layer) ?? [], -Infinity).geometry;
    return [layer, { geometry, tree: new MeshBVH(geometry) }];
  }));
  const pairs = layers.slice(1).map(layer => ['body', layer]);
  pairs.push(['inner', 'jacket'], ['pants', 'inner'], ['pants', 'jacket']);
  for (const hair of ['scalp', 'hair', 'flyaways']) for (const cloth of ['inner', 'jacket', 'pants']) pairs.push([hair, cloth]);
  const results = [];
  for (const [a, b] of pairs) {
    let intersections = 0;
    baked.get(a).tree.bvhcast(baked.get(b).tree, new THREE.Matrix4(), {
      intersectsTriangles(first, second) { if (first.intersectsTriangle(second)) intersections++; return false; },
    });
    results.push({ pair: `${a}/${b}`, intersections });
  }
  baked.forEach(({ geometry }) => geometry.dispose());
  return results;
}
