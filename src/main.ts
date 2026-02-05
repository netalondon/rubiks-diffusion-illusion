import './style.css';
import * as THREE from 'three';
import { CubeModel } from './cube/model';
import { CubeRenderer } from './cube/renderer';
import { CubeAnimator } from './cube/animator';
import { bindKeyboard } from './input/keyboard';
import { bindCubeDrag } from './input/mouse';
import { setupScene } from './scene/setup';

const app = document.querySelector<HTMLDivElement>('#app');
if (!app) {
  throw new Error('Missing #app element');
}

const { scene, camera, renderer } = setupScene(app);

const cubeRoot = new THREE.Group();
scene.add(cubeRoot);

const model = new CubeModel();
const cubeRenderer = new CubeRenderer(cubeRoot);
const animator = new CubeAnimator(cubeRoot, model, cubeRenderer);

cubeRenderer.build(model.getCubies());

bindKeyboard(cubeRoot, camera, (move) => {
  animator.enqueue(move);
});

bindCubeDrag(renderer.domElement, cubeRoot, camera);

let lastTime = performance.now();

function animate(time: number) {
  const delta = time - lastTime;
  lastTime = time;

  animator.update(delta);
  renderer.render(scene, camera);

  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
