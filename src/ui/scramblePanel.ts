import type { FaceArtMode } from '../cube/faceArt';
import { loadGeneratedScramble } from '../cube/generatedScramble';
import type { CubeAnimator } from '../cube/animator';

export interface ScrambleControls {
  button: HTMLButtonElement;
  status: HTMLParagraphElement;
  scramble: HTMLParagraphElement;
}

export function createScrambleControls(
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
      ? 'Art mode: debug labels. The TOP bar marks the sticker edge that was up in the source face image.'
      : 'Art mode: photos. Add ?art=debug to verify sticker mapping visually.';
  panel.append(artModeLabel);

  if (artMode === 'debug') {
    const rotationHint = document.createElement('p');
    rotationHint.className = 'scramble-panel__meta';
    rotationHint.textContent =
      'Rotation check: after scrambling, watch where that TOP bar ends up. Right side means r1, bottom means r2, left side means r3.';
    panel.append(rotationHint);
  }

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

export async function initializeGeneratedScramble(
  controls: ScrambleControls,
  animator: CubeAnimator
): Promise<void> {
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
