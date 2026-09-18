import * as THREE from 'three';


function includeCurve(curve, first, last, longCurveStride) {
  const points = last - first;
  return points < 20 || longCurveStride <= 1 || curve % longCurveStride !== longCurveStride - 1;
}

function createRibbonGeometry(curveOffsets, radii, longCurveStride) {
  let segmentCount = 0;
  let renderedCurveCount = 0;
  for (let curve = 0; curve + 1 < curveOffsets.length; curve++) {
    if (!includeCurve(curve, curveOffsets[curve], curveOffsets[curve + 1], longCurveStride)) continue;
    segmentCount += Math.max(0, curveOffsets[curve + 1] - curveOffsets[curve] - 1);
    renderedCurveCount++;
  }
  const vertexCount = segmentCount * 4;
  const pointIndex = new Float32Array(vertexCount);
  const side = new Float32Array(vertexCount);
  const along = new Float32Array(vertexCount);
  const radius = new Float32Array(vertexCount);
  const indices = new Uint32Array(segmentCount * 6);
  let segment = 0;
  for (let curve = 0; curve + 1 < curveOffsets.length; curve++) {
    const first = curveOffsets[curve];
    const last = curveOffsets[curve + 1];
    if (!includeCurve(curve, first, last, longCurveStride)) continue;
    for (let point = first; point + 1 < last; point++, segment++) {
      const vertex = segment * 4;
      pointIndex.set([point, point, point + 1, point + 1], vertex);
      side.set([-1, 1, -1, 1], vertex);
      along.set([0, 0, 1, 1], vertex);
      radius.set([radii[point], radii[point], radii[point + 1], radii[point + 1]], vertex);
      const index = segment * 6;
      indices.set([vertex, vertex + 2, vertex + 1, vertex + 2, vertex + 3, vertex + 1], index);
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('aPointIndex', new THREE.BufferAttribute(pointIndex, 1));
  geometry.setAttribute('aSide', new THREE.BufferAttribute(side, 1));
  geometry.setAttribute('aAlong', new THREE.BufferAttribute(along, 1));
  geometry.setAttribute('aRadius', new THREE.BufferAttribute(radius, 1));
  geometry.setIndex(new THREE.BufferAttribute(indices, 1));
  geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 100);
  return { geometry, segmentCount, renderedCurveCount, vertexCount, indexCount: indices.length };
}


export class HairStrandRenderer {
  constructor(runtime, { viewportWidth = 900, viewportHeight = 900, longCurveStride = 4 } = {}) {
    this.runtime = runtime;
    this.textureWidth = 512;
    this.textureHeight = Math.ceil(runtime.manifest.geometry.pointCount / this.textureWidth);
    this.textureData = new Float32Array(this.textureWidth * this.textureHeight * 4);
    this.positionTexture = new THREE.DataTexture(
      this.textureData,
      this.textureWidth,
      this.textureHeight,
      THREE.RGBAFormat,
      THREE.FloatType,
    );
    this.positionTexture.name = 'AevryndHairPositions_R1085';
    this.positionTexture.minFilter = THREE.NearestFilter;
    this.positionTexture.magFilter = THREE.NearestFilter;
    this.positionTexture.generateMipmaps = false;
    this.positionTexture.needsUpdate = true;
    const built = createRibbonGeometry(runtime.curveOffsets, runtime.radii, longCurveStride);
    this.segmentCount = built.segmentCount;
    this.renderedCurveCount = built.renderedCurveCount;
    this.vertexCount = built.vertexCount;
    this.indexCount = built.indexCount;
    this.material = new THREE.ShaderMaterial({
      name: 'AevryndOwnedHairRibbon_R1085',
      glslVersion: THREE.GLSL3,
      transparent: false,
      alphaToCoverage: true,
      blending: THREE.NoBlending,
      depthWrite: true,
      side: THREE.FrontSide,
      uniforms: {
        uPositions: { value: this.positionTexture },
        uTextureWidth: { value: this.textureWidth },
        uViewport: { value: new THREE.Vector2(viewportWidth, viewportHeight) },
        uMinimumHalfWidthPx: { value: 0.42 },
        uWidthScale: { value: 2.35 },
        uRootColor: { value: new THREE.Color(0x3a2118) },
        uTipColor: { value: new THREE.Color(0x845038) },
      },
      vertexShader: `
        uniform sampler2D uPositions;
        uniform int uTextureWidth;
        uniform vec2 uViewport;
        uniform float uMinimumHalfWidthPx;
        uniform float uWidthScale;
        in float aPointIndex;
        in float aSide;
        in float aAlong;
        in float aRadius;
        out float vAcross;
        out float vAlong;
        out vec3 vViewTangent;
        out vec3 vLocalPosition;

        vec3 readPoint(int index) {
          return texelFetch(uPositions, ivec2(index % uTextureWidth, index / uTextureWidth), 0).xyz;
        }

        void main() {
          int point = int(aPointIndex + 0.5);
          int other = point + (aAlong < 0.5 ? 1 : -1);
          vec3 local = readPoint(point);
          vec3 otherLocal = readPoint(other);
          vec4 viewPoint = modelViewMatrix * vec4(local, 1.0);
          vec4 otherViewPoint = modelViewMatrix * vec4(otherLocal, 1.0);
          vec4 clip = projectionMatrix * viewPoint;
          vec4 otherClip = projectionMatrix * otherViewPoint;
          vec2 pointPx = clip.xy / clip.w * uViewport * 0.5;
          vec2 otherPx = otherClip.xy / otherClip.w * uViewport * 0.5;
          vec2 direction = normalize(pointPx - otherPx + vec2(1e-5));
          vec2 normal = vec2(-direction.y, direction.x);
          float projectedRadiusPx = aRadius * uWidthScale * projectionMatrix[1][1] * uViewport.y / max(0.001, -2.0 * viewPoint.z);
          float halfWidthPx = max(uMinimumHalfWidthPx, projectedRadiusPx);
          clip.xy += normal * aSide * halfWidthPx * 2.0 / uViewport * clip.w;
          gl_Position = clip;
          vAcross = aSide;
          vAlong = aAlong;
          vViewTangent = normalize(viewPoint.xyz - otherViewPoint.xyz);
          vLocalPosition = local;
        }
      `,
      fragmentShader: `
        precision highp float;
        uniform vec3 uRootColor;
        uniform vec3 uTipColor;
        in float vAcross;
        in float vAlong;
        in vec3 vViewTangent;
        in vec3 vLocalPosition;
        out vec4 outColor;
        void main() {
          float faceEllipse = pow(vLocalPosition.x / 0.078, 2.0) + pow((vLocalPosition.z - 1.385) / 0.082, 2.0);
          if (vLocalPosition.z < 1.455 && faceEllipse < 1.0) discard;
          if (vLocalPosition.z < 1.31 && abs(vLocalPosition.x) < 0.105) discard;
          float edge = 1.0 - smoothstep(0.48, 1.0, abs(vAcross));
          float longitudinal = mix(0.92, 0.74, vAlong);
          vec3 lightDirection = normalize(vec3(0.36, 0.58, 0.73));
          float anisotropic = pow(max(0.0, 1.0 - abs(dot(normalize(vViewTangent), lightDirection))), 12.0);
          vec3 color = mix(uRootColor, uTipColor, 0.28 + 0.52 * vAlong);
          color += vec3(0.24, 0.13, 0.075) * anisotropic;
          float alpha = edge * longitudinal;
          if (alpha < 0.08) discard;
          outColor = vec4(color, alpha);
        }
      `,
    });
    this.material.forceSinglePass = true;
    this.mesh = new THREE.Mesh(built.geometry, this.material);
    this.mesh.name = 'AevryndDynamicHairRibbons_R1085';
    if (runtime.manifest.coordinateSystem === 'hair-object local metres, Blender Z up') this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.frustumCulled = false;
    this.updateFrame(1);
  }

  setViewport(width, height) {
    this.material.uniforms.uViewport.value.set(width, height);
  }

  updateFrame(frame) {
    const positions = this.runtime.evaluateFrame(frame);
    for (let point = 0, source = 0, target = 0; point < this.runtime.manifest.geometry.pointCount; point++, source += 3, target += 4) {
      this.textureData[target] = positions[source];
      this.textureData[target + 1] = positions[source + 1];
      this.textureData[target + 2] = positions[source + 2];
      this.textureData[target + 3] = 1;
    }
    this.positionTexture.needsUpdate = true;
    return positions;
  }

  dispose() {
    this.mesh.geometry.dispose();
    this.material.dispose();
    this.positionTexture.dispose();
  }
}
