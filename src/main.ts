import './style.css';
import * as THREE from 'three';
import { loadFaceArtImages, resolveFaceArtModeFromUrlSearch } from './cube/faceArt';
import type { FaceArtMode } from './cube/faceArt';
import { CubeModel } from './cube/model';
import { CubeRenderer } from './cube/renderer';
import { CubeAnimator } from './cube/animator';
import { loadGeneratedScramble } from './cube/generatedScramble';
import { bindKeyboard } from './input/keyboard';
import { bindCubeDrag } from './input/mouse';
import { setupScene } from './scene/setup';

const app = document.querySelector<HTMLDivElement>('#app');
if (!app) {
  throw new Error('Missing #app element');
}
const appRoot = app;

async function bootstrap() {
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

bootstrap().catch((error) => {
  console.error(error);
  appRoot.textContent = 'Failed to load cube face artwork.';
});

interface ScrambleControls {
  button: HTMLButtonElement;
  status: HTMLParagraphElement;
  scramble: HTMLParagraphElement;
}

function createScrambleControls(
  appRoot: HTMLDivElement,
  animator: CubeAnimator,
  artMode: FaceArtMode
): ScrambleControls {
  const panel = document.createElement('section');
  panel.className = 'scramble-panel';

  const heading = document.createElement('h2');
  heading.className = 'scramble-panel__title';
  heading.textContent = 'Saved Scramble';
  panel.append(heading);

  const status = document.createElement('p');
  status.className = 'scramble-panel__status';
  status.textContent = 'Loading saved scramble...';
  panel.append(status);

  const artModeLabel = document.createElement('p');
  artModeLabel.className = 'scramble-panel__meta';
  artModeLabel.textContent =
    artMode === 'debug'
      ? 'Art mode: debug labels. Remove ?art=debug to return to photos.'
      : 'Art mode: photos. Add ?art=debug to verify sticker mapping visually.';
  panel.append(artModeLabel);

  const scramble = document.createElement('p');
  scramble.className = 'scramble-panel__text';
  scramble.hidden = true;
  panel.append(scramble);

  const button = document.createElement('button');
  button.className = 'scramble-panel__button';
  button.type = 'button';
  button.textContent = 'Run Saved Scramble';
  button.disabled = true;
  panel.append(button);

  appRoot.append(panel);

  function updateButtonState(): void {
    if (button.dataset.ready !== 'true') {
      button.disabled = true;
      return;
    }

    button.disabled = !animator.isIdle();
  }

  let rafId = 0;
  const syncButtonState = () => {
    updateButtonState();
    rafId = requestAnimationFrame(syncButtonState);
  };
  rafId = requestAnimationFrame(syncButtonState);

  window.addEventListener('beforeunload', () => cancelAnimationFrame(rafId), { once: true });

  return { button, status, scramble };
}

async function initializeGeneratedScramble(controls: ScrambleControls, animator: CubeAnimator): Promise<void> {
  try {
    const record = await loadGeneratedScramble();
    if (!record) {
      controls.status.textContent = 'No saved scramble found at /generated/non-adjacent-scramble.json.';
      controls.scramble.hidden = true;
      controls.button.dataset.ready = 'false';
      controls.button.disabled = true;
      return;
    }

    controls.status.textContent = `Loaded ${record.length}-move scramble found after ${record.attempts.toLocaleString()} attempts.`;
    controls.scramble.textContent = record.scramble;
    controls.scramble.hidden = false;
    controls.button.dataset.ready = 'true';
    controls.button.disabled = !animator.isIdle();
    controls.button.addEventListener('click', () => {
      if (!animator.isIdle()) {
        return;
      }

      for (const move of record.moves) {
        animator.enqueue(move);
      }
    });
  } catch (error) {
    controls.status.textContent = error instanceof Error ? error.message : String(error);
    controls.scramble.hidden = true;
    controls.button.dataset.ready = 'false';
    controls.button.disabled = true;
  }
}
