import * as THREE from '../lib/three/three.module.js';
import { OrbitControls } from '../lib/three/OrbitControls.js';
import { GLTFLoader } from '../lib/three/GLTFLoader.js';

const root = document.querySelector('[data-character-editor]');
if (root) {
  const viewport = root.querySelector('[data-editor-viewport]');
  const status = root.querySelector('[data-editor-status]');
  const restricted = document.querySelector('[data-age-restricted-content]');
  const inputs = [...root.querySelectorAll('button,input')];
  inputs.forEach(input => input.disabled = true);
  let initialized = false;
  const start = async () => {
    if (initialized || restricted?.hasAttribute('inert')) return;
    initialized = true;
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1.15;
      viewport.append(renderer.domElement);
      const scene = new THREE.Scene();
      scene.background = new THREE.Color('#20272d');
      const camera = new THREE.PerspectiveCamera(35, 1, .01, 100);
      const controls = new OrbitControls(camera, renderer.domElement);
      controls.enablePan = false;
      controls.enableDamping = false;
      controls.minPolarAngle = .15;
      controls.maxPolarAngle = Math.PI - .15;
      scene.add(new THREE.HemisphereLight(0xe5f1ff, 0x615246, 2));
      for (const [color, intensity, x, y, z] of [[0xffeee3,3,2,3,4],[0xd3e5ff,2,-3,2,1],[0xffffff,2,0,3,-3]]) {
        const light = new THREE.DirectionalLight(color,intensity);
        light.position.set(x,y,z);scene.add(light);
      }
      const gltf = await new GLTFLoader().loadAsync('/media/character-editor/character.glb', progress => {
        status.textContent = progress.total ? `載入角色 ${Math.round(progress.loaded / progress.total * 100)}%` : '正在載入三維角色…';
      });
      const character = gltf.scene;
      scene.add(character);
      const body = character.getObjectByName('Body');
      const upper = character.getObjectByName('Upper');
      const pants = character.getObjectByName('Pants');
      if (!body || !upper) throw new Error('角色資產缺少必要的身體或上衣網格');
      const morphMeshes = [];
      character.traverse(mesh => { if (mesh.morphTargetDictionary && mesh.morphTargetInfluences) morphMeshes.push(mesh); });
      if (!morphMeshes.length) throw new Error('角色塑形資料尚未就緒');
      character.updateMatrixWorld(true);
      const bounds = new THREE.Box3().setFromObject(character);
      const center = bounds.getCenter(new THREE.Vector3());
      const height = bounds.max.y - bounds.min.y;
      if (!Number.isFinite(height) || height < .1) throw new Error('角色比例資料無效');
      const draw = () => { renderer.render(scene,camera); };
      const orbit = root.querySelector('[data-editor-orbit]');
      let view = 'face';
      const changeView = value => {
        view = value;
        const target = center.clone(); target.y = bounds.min.y + height * (view === 'face' ? .9 : .5);
        const distance = height * (view === 'face' ? .52 : 1.95);
        controls.target.copy(target);
        camera.position.copy(target).add(new THREE.Vector3(0,0,distance));
        controls.minDistance = height * .2; controls.maxDistance = height * 4;
        controls.update();
        root.querySelectorAll('[data-editor-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.editorView === view)));
        draw();
      };
      const setClothing = clothed => {
        upper.visible = clothed;
        if (pants) pants.visible = clothed;
        root.querySelectorAll('[data-editor-clothing]').forEach(button => button.setAttribute('aria-pressed', String((button.dataset.editorClothing === 'on') === clothed)));
        draw();
      };
      const shapePanel = root.querySelector('[data-editor-shapes]');
      // 名稱由同一份匯出資產提供，不以切換截圖冒充連續塑形。
      const definitions = [['jawWidth','下顎寬度'],['chinLength','下巴長度'],['noseWidth','鼻翼寬度'],['mouthWidth','嘴部寬度'],['lipThickness','嘴唇厚度'],['waistWidth','腰部寬度'],['hipWidth','臀部寬度'],['shoulderWidth','肩部寬度']];
      const available = definitions.filter(([axis]) => ['minimum','maximum'].every(end => morphMeshes.some(mesh => mesh.morphTargetDictionary[`${axis}_${end}`] !== undefined)));
      const axes = available.map(([axis]) => axis);
      const labels = available.map(([,label]) => label);
      const names = axes.flatMap(axis => [`${axis}_minimum`,`${axis}_maximum`]);
      const defaultValues = { chinLength: 1 };
      if (axes.length < 5) throw new Error('塑形名稱不完整');
      for (let index = 0; index < names.length; index += 2) {
        const pair = names.slice(index,index + 2);
        const label = document.createElement('label');
        label.textContent = labels[index / 2];
        const output = document.createElement('output'); output.textContent = '0';
        const slider = document.createElement('input');
        slider.type = 'range';slider.min = '-1';slider.max = '1';slider.step = '.01';
        slider.dataset.shapeAxis = axes[index / 2];
        slider.value = String(defaultValues[slider.dataset.shapeAxis] ?? 0);
        slider.addEventListener('input', () => {
          const value = Number(slider.value);output.value = value.toFixed(2);
          for (const mesh of morphMeshes) {
            pair.forEach((name,side) => { const slot = mesh.morphTargetDictionary[name]; if (slot !== undefined) mesh.morphTargetInfluences[slot] = Math.max(0,side ? value : -value); });
          }
          draw();
        });
        label.append(output,slider);shapePanel.append(label);slider.dispatchEvent(new Event('input'));
      }
      controls.addEventListener('change', () => {
        const degrees = Math.round(THREE.MathUtils.radToDeg(controls.getAzimuthalAngle()));
        orbit.value = String(degrees);root.querySelector('[data-orbit-output]').value = `${degrees}°`;draw();
      });
      const rotate = degrees => {
        const offset = camera.position.clone().sub(controls.target);
        const spherical = new THREE.Spherical().setFromVector3(offset);
        spherical.theta = THREE.MathUtils.degToRad(degrees);
        camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));controls.update();
      };
      orbit.addEventListener('input', () => rotate(Number(orbit.value)));
      viewport.addEventListener('keydown', event => { if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault();rotate(Number(orbit.value) + (event.key === 'ArrowLeft' ? -5 : 5)); } });
      root.querySelectorAll('[data-editor-view]').forEach(button => button.addEventListener('click', () => changeView(button.dataset.editorView)));
      root.querySelectorAll('[data-editor-clothing]').forEach(button => button.addEventListener('click', () => setClothing(button.dataset.editorClothing === 'on')));
      root.querySelector('[data-editor-reset]').addEventListener('click', () => {
        shapePanel.querySelectorAll('input').forEach(slider => {
          slider.value = String(defaultValues[slider.dataset.shapeAxis] ?? 0);
          slider.dispatchEvent(new Event('input'));
        });
        setClothing(true);changeView('face');
      });
      const resize = new ResizeObserver(() => {
        const width = viewport.clientWidth, height = viewport.clientHeight;
        if (!width || !height) return;
        renderer.setSize(width,height,false);camera.aspect = width / height;camera.updateProjectionMatrix();draw();
      });
      resize.observe(viewport);
      inputs.forEach(input => input.disabled = false);
      setClothing(true);changeView('face');status.textContent = '拖曳環繞 · 滾輪縮放 · 同一角色';
      window.addEventListener('pagehide', () => { resize.disconnect();controls.dispose();renderer.dispose(); }, {once:true});
    } catch (error) {
      status.textContent = '三維角色尚未成功載入，請稍後重新整理。';
      console.error('Character editor initialization failed',error);
      renderer?.dispose();
    }
  };
  // 成人確認由使用者操作，確認前不載入人體資產。
  const observer = new MutationObserver(() => { if (!restricted?.hasAttribute('inert')) { observer.disconnect();start(); } });
  if (restricted) observer.observe(restricted,{attributes:true,attributeFilter:['inert']});
  start();
}
