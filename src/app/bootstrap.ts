import * as THREE from 'three';
import { loadFaceArtImages, resolveFaceArtModeFromUrlSearch } from '../cube/faceArt';
import { CubeModel } from '../cube/model';
import { CubeRenderer } from '../cube/renderer';
import { CubeAnimator } from '../cube/animator';
import { bindKeyboard } from '../input/keyboard';
import { bindCubeDrag } from '../input/mouse';
import { setupScene } from '../scene/setup';
import { createScrambleControls, initializeGeneratedScramble } from '../ui/scramblePanel';

export async function bootstrapApp(appRoot: HTMLDivElement): Promise<void> {
  const { scene, camera, renderer } = setupScene(appRoot);
  const artMode = resolveFaceArtModeFromUrlSearch(window.location.search);
  const faceArtImages = await loadFaceArtImages(artMode);

  const cubeRoot = new THREE.Group();
  scene.add(cubeRoot);

  const model = new CubeModel();
  const cubeRenderer = new CubeRenderer(cubeRoot, faceArtImages);
  const animator = new CubeAnimator(cubeRoot, model, cubeRenderer);

  cubeRenderer.build(model.getCubies());
  const scrambleControls = createScrambleControls(appRoot, animator, artMode);
  void initializeGeneratedScramble(scrambleControls, animator);

  bindKeyboard(cubeRoot, camera, (move) => {
    animator.enqueue(move);
  });

  bindCubeDrag(renderer.domElement, cubeRoot, camera);
  startRenderLoop(scene, camera, renderer, animator);
}

function startRenderLoop(
  scene: THREE.Scene,
  camera: THREE.Camera,
  renderer: THREE.WebGLRenderer,
  animator: CubeAnimator
): void {
  let lastTime = performance.now();

  function animate(time: number) {
    const delta = time - lastTime;
    lastTime = time;

    animator.update(delta);
    renderer.render(scene, camera);

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}
