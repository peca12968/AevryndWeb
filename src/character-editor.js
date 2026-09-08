import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

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
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x20272d);

  const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.className = 'orbit-cursor-grab orbit-touch-disabled';
  renderer.domElement.setAttribute('aria-hidden', 'true');
  viewport.prepend(renderer.domElement);

  scene.add(new THREE.HemisphereLight(0xfff8ed, 0x3f4a50, 2.1));
  const keyLight = new THREE.DirectionalLight(0xffead2, 3.4);
  keyLight.position.set(3.5, 5, 4.5);
  keyLight.castShadow = true;
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight(0xc9ddff, 1.15);
  fillLight.position.set(-4, 2.5, 3);
  scene.add(fillLight);
  const rimLight = new THREE.DirectionalLight(0xffffff, 1.4);
  rimLight.position.set(1, 3, -4);
  scene.add(rimLight);

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
    { key: 'chinLength', label: '下巴長度', initial: 100 },
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
    if (upper) upper.visible = visible;
    if (pants) pants.visible = visible;
    clothingButtons.forEach(button => button.setAttribute('aria-pressed', String((button.dataset.editorClothing === 'on') === visible)));
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
    status.textContent = message;
    setControlsDisabled(true);
  }

  buildShapeControls();
  new ResizeObserver(resize).observe(viewport);
  resize();
  setView('face', 0);

  new GLTFLoader().load('./assets/character-third-pants.glb', gltf => {
    clearTimeout(loadingTimer);
    model = gltf.scene;
    model.traverse(node => {
      if (node.isMesh) {
        node.castShadow = true;
        node.receiveShadow = true;
      }
    });
    upper = model.getObjectByName('Upper');
    pants = model.getObjectByName('Pants');
    scene.add(model);
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
  clothingButtons.forEach(button => button.addEventListener('click', () => setClothing(button.dataset.editorClothing === 'on')));
  orbitInput.addEventListener('input', () => setView(currentView, Number(orbitInput.value)));
  resetButton.addEventListener('click', resetEditor);
  controls.addEventListener('change', () => updateOrbitReadout(normalizedAngle(controls.getAzimuthalAngle())));
  controls.addEventListener('start', () => renderer.domElement.className = 'orbit-cursor-grabbing orbit-touch-disabled');
  controls.addEventListener('end', () => renderer.domElement.className = 'orbit-cursor-grab orbit-touch-disabled');
  viewport.addEventListener('keydown', event => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    setView(currentView, currentAngle + (event.key === 'ArrowLeft' ? -5 : 5));
  });
  reducedMotion.addEventListener('change', () => { controls.enableDamping = !reducedMotion.matches; });

  renderer.setAnimationLoop(() => {
    controls.update();
    renderer.render(scene, camera);
  });
}
