import type { Move } from '../cube/moves';
import { parseMove } from '../cube/moves';

export function bindKeyboard(onMove: (move: Move) => void): () => void {
  const handler = (event: KeyboardEvent) => {
    if (event.repeat) {
      return;
    }

    const move = parseMove(event.key, event.shiftKey);
    if (!move) {
      return;
    }
    event.preventDefault();
    onMove(move);
  };

  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
