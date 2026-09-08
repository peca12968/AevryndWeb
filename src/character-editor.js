import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { classifyMaterial, layerDefinitions, refineMaterial } from './character-materials.js';

await (window.aevryndAgeGate ?? Promise.resolve(true));

const editor = document.querySelector('[data-character-editor]');

if (editor) {
  const viewport = editor.querySelector('[data-editor-viewport]');
  const status = editor.querySelector('[data-editor-status]');
  const orbitInput = editor.querySelector('[data-editor-orbit]');
  const orbitOutput = editor.querySelector('[data-orbit-output]');
  const shapePanel = editor.querySelector('[data-editor-shapes]');
  const resetButton = editor.querySelector('[data-editor-reset]');
  const viewButtons = [...editor.querySelectorAll('[data-editor-view]')];
  const clothingButtons = [...editor.querySelectorAll('[data-editor-clothing]')];
  const nudityDialog = editor.querySelector('[data-nudity-confirm]');
  const nudityApprove = editor.querySelector('[data-nudity-approve]');
  const nudityCancel = editor.querySelector('[data-nudity-cancel]');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const layerPanel = editor.querySelector('[data-editor-layers]');
  const layerInputs = new Map();
  const layerVisibility = new Map(layerDefinitions.map(layer => [layer.id, true]));
  let pendingNudityAction = null;
  let nudityAccepted = false;
  let wireframe = false;
  let comparison = 'refined';
  let originalModel = null;
  let refinedModel = null;
  let loadingOriginal = false;
  let comparisonRequest = 0;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x20272d);

  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .95;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.className = 'orbit-cursor-grab orbit-touch-disabled';
  renderer.domElement.setAttribute('aria-hidden', 'true');
  viewport.prepend(renderer.domElement);

  const environment = new RoomEnvironment();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environmentTarget = pmrem.fromScene(environment, .04);
  scene.environment = environmentTarget.texture;
  scene.environmentIntensity = .5;
  environment.dispose();
  pmrem.dispose();
  const ambient = new THREE.HemisphereLight(0xfff5eb, 0x465260, .65);
  scene.add(ambient);
  const keyLight = new THREE.DirectionalLight(0xfff0df, 2.6);
  keyLight.position.set(3.5, 5, 4.5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  Object.assign(keyLight.shadow.camera, { left: -1.3, right: 1.3, top: 1.9, bottom: -1, near: .1, far: 12 });
  keyLight.shadow.normalBias = .0015;
  keyLight.shadow.bias = -.00008;
  keyLight.target.position.set(0, 1, 0);
  scene.add(keyLight.target);
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight(0xdde8ff, .65);
  fillLight.position.set(-4, 2.5, 3);
  scene.add(fillLight);
  const rimLight = new THREE.DirectionalLight(0xffffff, 1.1);
  rimLight.position.set(1, 3, -4);
  scene.add(rimLight);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(2.8, 96), new THREE.MeshStandardMaterial({ color: 0x252d34, roughness: .94 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -.009;
  floor.receiveShadow = true;
  scene.add(floor);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = !reducedMotion.matches;
  controls.dampingFactor = 0.075;
  controls.enablePan = false;
  controls.rotateSpeed = 0.72;
  controls.zoomSpeed = 0.85;
  controls.minPolarAngle = THREE.MathUtils.degToRad(15);
  controls.maxPolarAngle = THREE.MathUtils.degToRad(165);

  const views = {
    face: { target: new THREE.Vector3(0, 1.585, 0.055), distance: 0.58, fov: 28, min: 0.28, max: 1.7 },
    body: { target: new THREE.Vector3(0, 0.88, 0), distance: 3.2, fov: 30, min: 1.15, max: 5.5 }
  };
  const shapes = [
    { key: 'jawWidth', label: '下顎寬度', initial: 0 },
    { key: 'chinLength', label: '下巴長度', initial: 0 },
    { key: 'noseWidth', label: '鼻翼寬度', initial: 0 },
    { key: 'mouthWidth', label: '嘴部寬度', initial: 0 },
    { key: 'lipThickness', label: '嘴唇厚度', initial: 0 }
  ];

  let model = null;
  let upper = null;
  let pants = null;
  let currentView = 'face';
  let currentAngle = 0;
  let clothingOn = true;
  let loadingTimer = 0;
  let nudityReturnFocus = null;

  function setControlsDisabled(disabled) {
    editor.querySelectorAll('button, input').forEach(control => { control.disabled = disabled; });
  }

  function resize() {
    const width = Math.max(1, viewport.clientWidth);
    const height = Math.max(1, viewport.clientHeight);
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  function normalizedAngle(radians) {
    const degrees = Math.round(THREE.MathUtils.radToDeg(radians));
    return ((degrees + 180) % 360 + 360) % 360 - 180;
  }

  function updateOrbitReadout(angle) {
    const normalized = ((Math.round(angle) + 180) % 360 + 360) % 360 - 180;
    currentAngle = normalized;
    orbitInput.value = String(normalized);
    orbitOutput.value = `${normalized}°`;
    orbitOutput.textContent = `${normalized}°`;
  }

  function setView(name, angle = currentAngle) {
    currentView = name;
    const view = views[name];
    camera.fov = view.fov;
    camera.updateProjectionMatrix();
    controls.target.copy(view.target);
    controls.minDistance = view.min;
    controls.maxDistance = view.max;
    const radians = THREE.MathUtils.degToRad(angle);
    camera.position.set(
      view.target.x + Math.sin(radians) * view.distance,
      view.target.y,
      view.target.z + Math.cos(radians) * view.distance
    );
    controls.update();
    viewButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.editorView === name)));
    updateOrbitReadout(angle);
  }

  function setClothing(visible) {
    clothingOn = visible;
    layerDefinitions.filter(layer => layer.clothing).forEach(layer => layerVisibility.set(layer.id, visible));
    applyLayers();
  }

  function applyLayers() {
    for (const root of [refinedModel, originalModel]) {
      root?.traverse(node => {
        if (!node.isMesh) return;
        const materials = Array.isArray(node.material) ? node.material : [node.material];
        materials.forEach(material => {
          material.visible = layerVisibility.get(classifyMaterial(material.name)) ?? true;
          material.wireframe = wireframe;
        });
      });
    }
    layerInputs.forEach((input, id) => { input.checked = layerVisibility.get(id); });
    const clothes = layerDefinitions.filter(layer => layer.clothing).map(layer => layerVisibility.get(layer.id));
    clothingOn = clothes.every(Boolean);
    clothingButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.editorClothing === 'on' ? clothingOn : clothes.every(value => !value))));
  }

  function buildLayerControls() {
    let group = '';
    layerDefinitions.forEach(layer => {
      if (group !== layer.group) {
        const heading = document.createElement('p');
        heading.className = 'layer-group-heading';
        heading.textContent = group = layer.group;
        layerPanel.append(heading);
      }
      const label = document.createElement('label');
      label.className = 'character-layer-row';
      const input = document.createElement('input');
      input.type = 'checkbox'; input.checked = true; input.disabled = true;
      input.dataset.characterLayer = layer.id;
      input.addEventListener('change', () => {
        const visible = input.checked;
        const apply = () => { layerVisibility.set(layer.id, visible); applyLayers(); };
        if (layer.clothing && !visible && !nudityAccepted) {
          input.checked = true;
          pendingNudityAction = apply;
          openNudityDialog(input);
        } else apply();
      });
      label.append(input, document.createTextNode(layer.label));
      layerPanel.append(label); layerInputs.set(layer.id, input);
    });
  }

  function setLighting(name) {
    const presets = { studio: [2.6, .65, 1.1, .5], daylight: [2.1, 1.2, .5, .75], contour: [2.9, .15, 1.8, .25] };
    const [key, fill, rim, env] = presets[name];
    keyLight.intensity = key; fillLight.intensity = fill; rimLight.intensity = rim; scene.environmentIntensity = env;
    keyLight.position.set(name === 'contour' ? -3.5 : 3.5, 5, name === 'contour' ? 1.5 : 4.5);
    editor.querySelectorAll('[data-editor-light]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.editorLight === name)));
  }

  async function setComparison(name) {
    const request = ++comparisonRequest;
    if (name === 'original' && !originalModel) {
      if (loadingOriginal) return;
      loadingOriginal = true;
      status.hidden = false;
      status.textContent = '正在準備原始模型比較…';
      try {
        const gltf = await new GLTFLoader().loadAsync('./assets/character-third-pants.glb');
        originalModel = gltf.scene;
        originalModel.traverse(node => { if (node.isMesh) { node.castShadow = true; node.receiveShadow = true; } });
        scene.add(originalModel);
        originalModel.visible = false;
      } catch {
        status.textContent = '原始模型暫時無法載入，精修模型仍可操作。';
        return;
      } finally { loadingOriginal = false; }
    }
    if (request !== comparisonRequest) return;
    comparison = name;
    model = name === 'original' ? originalModel : refinedModel;
    refinedModel.visible = name === 'refined';
    if (originalModel) originalModel.visible = name === 'original';
    shapePanel.querySelectorAll('[data-editor-shape]').forEach(input => setMorph(input.dataset.editorShape, input.value));
    applyLayers();
    status.hidden = true;
    editor.querySelectorAll('[data-editor-comparison]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.editorComparison === name)));
    editor.querySelector('[data-editor-version]').textContent = name === 'refined' ? '精修模型' : '原始模型 · 同一燈光';
  }

  function closeNudityDialog() {
    if (!nudityDialog || nudityDialog.hidden) return;
    nudityDialog.hidden = true;
    document.body.classList.remove('nudity-dialog-open');
    nudityReturnFocus?.focus();
    nudityReturnFocus = null;
    pendingNudityAction = null;
  }

  function openNudityDialog(button) {
    if (!nudityDialog) return;
    nudityReturnFocus = button;
    nudityDialog.hidden = false;
    document.body.classList.add('nudity-dialog-open');
    nudityApprove?.focus();
  }

  function setMorph(key, rawValue) {
    const value = Number(rawValue) / 100;
    if (!model) return;
    model.traverse(node => {
      if (!node.morphTargetDictionary || !node.morphTargetInfluences) return;
      const minimum = node.morphTargetDictionary[`${key}_minimum`];
      const maximum = node.morphTargetDictionary[`${key}_maximum`];
      if (minimum !== undefined) node.morphTargetInfluences[minimum] = value < 0 ? -value : 0;
      if (maximum !== undefined) node.morphTargetInfluences[maximum] = value > 0 ? value : 0;
    });
  }

  function buildShapeControls() {
    shapePanel.replaceChildren();
    const heading = document.createElement('p');
    heading.className = 'shape-heading';
    heading.textContent = '臉部塑形';
    shapePanel.append(heading);
    shapes.forEach(shape => {
      const label = document.createElement('label');
      label.textContent = shape.label;
      const output = document.createElement('output');
      output.textContent = String(shape.initial);
      const input = document.createElement('input');
      input.type = 'range';
      input.min = '-100';
      input.max = '100';
      input.step = '1';
      input.value = String(shape.initial);
      input.dataset.editorShape = shape.key;
      input.disabled = true;
      input.addEventListener('input', () => {
        output.value = input.value;
        output.textContent = input.value;
        setMorph(shape.key, input.value);
      });
      label.append(output, input);
      shapePanel.append(label);
    });
  }

  function resetEditor() {
    layerDefinitions.forEach(layer => layerVisibility.set(layer.id, true));
    wireframe = false;
    editor.querySelector('[data-editor-wireframe]').setAttribute('aria-pressed', 'false');
    setLighting('studio');
    setComparison('refined');
    setClothing(true);
    shapePanel.querySelectorAll('[data-editor-shape]').forEach(input => {
      const shape = shapes.find(item => item.key === input.dataset.editorShape);
      input.value = String(shape.initial);
      const output = input.parentElement.querySelector('output');
      output.value = String(shape.initial);
      output.textContent = String(shape.initial);
      setMorph(shape.key, shape.initial);
    });
    setView('face', 0);
  }

  function fail(message = '模型載入失敗，請重新整理後再試。') {
    clearTimeout(loadingTimer);
    status.hidden = false;
    status.textContent = message;
    setControlsDisabled(true);
  }

  buildShapeControls();
  buildLayerControls();
  new ResizeObserver(resize).observe(viewport);
  resize();
  setView('face', 0);

  new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).load('./assets/character-female-refined.glb', async gltf => {
    clearTimeout(loadingTimer);
    model = refinedModel = gltf.scene;
    model.traverse(node => {
      if (node.isMesh) {
        node.castShadow = true;
        node.receiveShadow = true;
        node.material = Array.isArray(node.material)
          ? node.material.map(material => refineMaterial(material, renderer.capabilities.getMaxAnisotropy()))
          : refineMaterial(node.material, renderer.capabilities.getMaxAnisotropy());
      }
    });
    upper = model.getObjectByName('Upper');
    pants = model.getObjectByName('Pants');
    scene.add(model);
    try { await renderer.compileAsync(scene, camera); } catch { fail('目前裝置無法完成角色材質編譯，請更新瀏覽器後再試。'); return; }
    shapes.forEach(shape => setMorph(shape.key, shape.initial));
    setClothing(true);
    setView('face', 0);
    setControlsDisabled(false);
    status.hidden = true;
  }, progress => {
    if (progress.total > 0) status.textContent = `正在準備三維角色… ${Math.round(progress.loaded / progress.total * 100)}%`;
  }, () => fail());
  loadingTimer = window.setTimeout(() => fail('模型載入逾時，請檢查連線後重新整理。'), 90000);

  viewButtons.forEach(button => button.addEventListener('click', () => setView(button.dataset.editorView)));
  clothingButtons.forEach(button => button.addEventListener('click', () => {
    if (button.dataset.editorClothing === 'on') {
      closeNudityDialog();
      setClothing(true);
      return;
    }
    if (layerDefinitions.filter(layer => layer.clothing).every(layer => !layerVisibility.get(layer.id))) return;
    if (nudityAccepted) { setClothing(false); return; }
    pendingNudityAction = () => setClothing(false);
    openNudityDialog(button);
  }));
  nudityApprove?.addEventListener('click', () => {
    nudityAccepted = true;
    pendingNudityAction?.();
    closeNudityDialog();
  });
  nudityCancel?.addEventListener('click', closeNudityDialog);
  nudityDialog?.addEventListener('click', event => {
    if (event.target === nudityDialog) closeNudityDialog();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && nudityDialog && !nudityDialog.hidden) closeNudityDialog();
    if (event.key === 'Tab' && nudityDialog && !nudityDialog.hidden) {
      event.preventDefault();
      (document.activeElement === nudityApprove ? nudityCancel : nudityApprove)?.focus();
    }
  });
  orbitInput.addEventListener('input', () => setView(currentView, Number(orbitInput.value)));
  resetButton.addEventListener('click', resetEditor);
  editor.querySelectorAll('[data-editor-light]').forEach(button => button.addEventListener('click', () => setLighting(button.dataset.editorLight)));
  editor.querySelectorAll('[data-editor-comparison]').forEach(button => button.addEventListener('click', () => setComparison(button.dataset.editorComparison)));
  editor.querySelector('[data-editor-wireframe]').addEventListener('click', event => {
    wireframe = !wireframe; event.currentTarget.setAttribute('aria-pressed', String(wireframe)); applyLayers();
  });
  editor.querySelectorAll('[data-editor-angle]').forEach(button => button.addEventListener('click', () => setView(currentView, Number(button.dataset.editorAngle))));
  controls.addEventListener('change', () => updateOrbitReadout(normalizedAngle(controls.getAzimuthalAngle())));
  controls.addEventListener('start', () => renderer.domElement.className = 'orbit-cursor-grabbing orbit-touch-disabled');
  controls.addEventListener('end', () => renderer.domElement.className = 'orbit-cursor-grab orbit-touch-disabled');
  viewport.addEventListener('keydown', event => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    setView(currentView, currentAngle + (event.key === 'ArrowLeft' ? -5 : 5));
  });
  reducedMotion.addEventListener('change', () => { controls.enableDamping = !reducedMotion.matches; });

  let viewportVisible = true;
  new IntersectionObserver(entries => { viewportVisible = entries[0].isIntersecting; }).observe(viewport);
  renderer.setAnimationLoop(() => {
    if (!viewportVisible || document.hidden) return;
    controls.update();
    renderer.render(scene, camera);
  });
  renderer.domElement.addEventListener('webglcontextlost', event => {
    event.preventDefault(); renderer.setAnimationLoop(null); fail('3D 顯示已中斷，請重新整理頁面以恢復。');
  });
}
