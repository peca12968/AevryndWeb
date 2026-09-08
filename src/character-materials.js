import * as THREE from 'three';

export const layerDefinitions = [
  { id: 'skin', label: '身體皮膚', group: '人體' },
  { id: 'lips', label: '嘴唇', group: '人體' },
  { id: 'nails', label: '手指甲・腳趾甲', group: '人體' },
  { id: 'ears', label: '耳朵', group: '人體' },
  { id: 'sclera', label: '眼白', group: '五官與毛髮' },
  { id: 'iris', label: '虹膜纖維', group: '五官與毛髮' },
  { id: 'pupil', label: '瞳孔', group: '五官與毛髮' },
  { id: 'brows', label: '眉毛細絲', group: '五官與毛髮' },
  { id: 'lashes', label: '睫毛', group: '五官與毛髮' },
  { id: 'scalp', label: '頭皮髮根', group: '五官與毛髮' },
  { id: 'hair', label: '主髮束', group: '五官與毛髮' },
  { id: 'flyaways', label: '碎髮', group: '五官與毛髮' },
  { id: 'inner', label: '內搭織物', group: '服裝', clothing: true },
  { id: 'jacket', label: '皮革外套', group: '服裝', clothing: true },
  { id: 'pants', label: '長褲', group: '服裝', clothing: true }
];

export function classifyMaterial(name) {
  const n = name.toLowerCase();
  if (n.startsWith('brow')) return 'brows';
  if (n.includes('lash')) return 'lashes';
  if (n.includes('scalp')) return 'scalp';
  if (n.includes('flyaway')) return 'flyaways';
  if (n.startsWith('hair_')) return 'hair';
  if (n.includes('sclera')) return 'sclera';
  if (n.includes('iris')) return 'iris';
  if (n.includes('pupil')) return 'pupil';
  if (n.includes('pants_')) return 'pants';
  if (n.includes('leather')) return 'jacket';
  if (n.includes('cloth')) return 'inner';
  if (n.includes('lips')) return 'lips';
  if (n.includes('nails')) return 'nails';
  if (n.includes('ears')) return 'ears';
  return 'skin';
}

export function refineMaterial(source, maxAnisotropy) {
  const material = new THREE.MeshPhysicalMaterial();
  if (source.isMeshPhysicalMaterial) material.copy(source);
  else THREE.MeshStandardMaterial.prototype.copy.call(material, source);
  material.defines = { STANDARD: '', PHYSICAL: '' };
  const layer = classifyMaterial(source.name);
  material.name = source.name;
  material.userData.layer = layer;
  material.envMapIntensity = .65;
  for (const key of ['map', 'normalMap', 'roughnessMap', 'metalnessMap']) {
    if (material[key]) material[key].anisotropy = Math.min(8, maxAnisotropy);
  }
  if (['skin', 'lips', 'ears', 'nails'].includes(layer)) {
    material.ior = 1.4;
    material.specularIntensity = .75;
    if (layer === 'skin' || layer === 'ears') {
      // 正規化包覆漫反射只近似表皮散射；不將其標示為體積次表面散射。
      material.onBeforeCompile = shader => {
        const original = 'reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );';
        const wrapped = `
          float signedNL = dot(geometryNormal, directLight.direction);
          vec3 wrap = vec3(0.20, 0.08, 0.035);
          vec3 skinDiffuse = clamp((vec3(signedNL) + wrap) / (1.0 + wrap), 0.0, 1.0) / (1.0 + wrap);
          reflectedLight.directDiffuse += mix(vec3(dotNL), skinDiffuse, 0.35) * directLight.color * BRDF_Lambert(material.diffuseColor);
        `;
        shader.fragmentShader = shader.fragmentShader.replace('#include <lights_physical_pars_fragment>',
          THREE.ShaderChunk.lights_physical_pars_fragment.replace(original, wrapped));
      };
      material.customProgramCacheKey = () => 'female-skin-wrap-v1';
    }
  }
  if (['sclera', 'iris', 'pupil'].includes(layer)) {
    material.clearcoat = 1;
    material.clearcoatRoughness = .08;
    material.ior = 1.376;
    material.envMapIntensity = 1;
  }
  if (['hair', 'flyaways', 'scalp', 'brows', 'lashes'].includes(layer)) {
    material.roughness = layer === 'scalp' ? .72 : .62;
    material.roughnessMap = null;
    material.specularIntensity = .45;
    material.anisotropy = layer === 'hair' || layer === 'flyaways' ? .4 : 0;
    material.anisotropyRotation = Math.PI / 2;
    if (material.alphaTest > 0) material.alphaToCoverage = true;
    // 原始髮絲法線標示 DX；WebGL 切線空間需反轉綠色通道。
    if (material.normalMap && material.normalMap.name.includes('dx')) material.normalScale.y *= -1;
  }
  if (layer === 'inner' || layer === 'pants') {
    material.metalness = 0;
    material.sheen = .22;
    material.sheenColor.setRGB(.2, .23, .28);
    material.sheenRoughness = .75;
  }
  return material;
}
