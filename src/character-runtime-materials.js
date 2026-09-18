import * as THREE from 'three';


const colors = {
  skin: new THREE.Color('#b87962'),
  wetline: new THREE.Color('#9d5a55'),
  scalp: new THREE.Color('#3a2119'),
  brow: new THREE.Color('#321a14'),
  lash: new THREE.Color('#1d100e'),
  sclera: new THREE.Color('#d9d1c9'),
  iris: new THREE.Color('#5f4330'),
  cornea: new THREE.Color('#f4f7f7'),
  caruncle: new THREE.Color('#a96562'),
};

let irisTexture;

function ownedIrisTexture() {
  if (irisTexture) return irisTexture;
  const size = 256;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const context = canvas.getContext('2d');
  const image = context.createImageData(size, size);
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    const nx = (x + 0.5) / size * 2 - 1;
    const ny = (y + 0.5) / size * 2 - 1;
    const radius = Math.hypot(nx, ny);
    const angle = Math.atan2(ny, nx);
    const spoke = 0.5 + 0.5 * Math.sin(angle * 43 + radius * 47 + Math.sin(angle * 7) * 2.5);
    let red = 22, green = 14, blue = 10;
    if (radius > 0.225 && radius < 0.91) {
      const radial = Math.max(0, 1 - Math.abs(radius - 0.52) / 0.42);
      red = 52 + 52 * radial + 22 * spoke;
      green = 43 + 42 * radial + 15 * spoke;
      blue = 27 + 24 * radial + 8 * spoke;
    }
    if (radius > 0.82) {
      const rim = THREE.MathUtils.clamp((radius - 0.82) / 0.13, 0, 1);
      red *= 1 - rim * 0.72;
      green *= 1 - rim * 0.72;
      blue *= 1 - rim * 0.72;
    }
    const offset = (y * size + x) * 4;
    image.data[offset] = red;
    image.data[offset + 1] = green;
    image.data[offset + 2] = blue;
    image.data[offset + 3] = 255;
  }
  context.putImageData(image, 0, 0);
  irisTexture = new THREE.CanvasTexture(canvas);
  irisTexture.name = 'AevryndOwnedProceduralIris_R1085';
  irisTexture.colorSpace = THREE.SRGBColorSpace;
  irisTexture.flipY = false;
  return irisTexture;
}

function tune(material) {
  const name = material.name.toLowerCase();
  material.metalness = 0;
  if (name.includes('cornea')) {
    material.color.copy(colors.cornea);
    material.roughness = 0.06;
    material.transparent = true;
    material.opacity = 0.24;
    material.depthWrite = false;
    material.side = THREE.FrontSide;
    if ('transmission' in material) material.transmission = 0.88;
    if ('ior' in material) material.ior = 1.376;
  } else if (name.includes('sclera')) {
    material.color.copy(colors.sclera);
    material.roughness = 0.38;
  } else if (name.includes('iris')) {
    material.color.set(0xffffff);
    material.map = ownedIrisTexture();
    material.roughness = 0.3;
  } else if (name.includes('caruncle')) {
    material.color.copy(colors.caruncle);
    material.roughness = 0.42;
  } else if (name.includes('scalp')) {
    material.color.copy(colors.scalp);
    material.roughness = 0.62;
  } else if (name.includes('brow')) {
    material.color.copy(colors.brow);
    material.roughness = 0.58;
  } else if (name.includes('lash')) {
    material.color.copy(colors.lash);
    material.roughness = 0.5;
  } else if (name.includes('wetline')) {
    material.color.copy(colors.wetline);
    material.roughness = 0.24;
  } else if (name.includes('skin')) {
    material.color.copy(colors.skin);
    material.roughness = 0.5;
    if ('sheen' in material) material.sheen = 0.12;
    if ('sheenRoughness' in material) material.sheenRoughness = 0.72;
  }
  material.needsUpdate = true;
}

export function applyOwnedCharacterMaterials(root) {
  const seen = new Set();
  root.traverse(node => {
    if (!node.isMesh) return;
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of materials) {
      if (!material || seen.has(material)) continue;
      seen.add(material);
      tune(material);
    }
  });
  return { materialCount: seen.size, palette: Object.fromEntries(Object.entries(colors).map(([key, color]) => [key, `#${color.getHexString()}`])) };
}
