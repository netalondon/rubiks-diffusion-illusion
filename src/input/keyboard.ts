import type { Move } from '../cube/moves';
import type { Face } from '../cube/moves';
import { isFace } from '../cube/moves';
import type * as THREE from 'three';
import { computeFaceMapping } from './faceMapping';

export function bindKeyboard(
  cubeRoot: THREE.Object3D,
  camera: THREE.Camera,
  onMove: (move: Move) => void
): () => void {
  let lastMapping: Record<Face, Face> = {
    R: 'R',
    L: 'L',
    U: 'U',
    D: 'D',
    F: 'F',
    B: 'B'
  };

  const handler = (event: KeyboardEvent) => {
    if (event.repeat) {
      return;
    }

    const key = event.key.toUpperCase();
    if (!isFace(key)) {
      return;
    }

    const mapping = computeFaceMapping(cubeRoot, camera, lastMapping);
    lastMapping = mapping;

    const move: Move = {
      face: mapping[key],
      turns: event.shiftKey ? -1 : 1
    };

    event.preventDefault();
    onMove(move);
  };

  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
