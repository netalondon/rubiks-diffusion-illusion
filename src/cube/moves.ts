export type Face = 'U' | 'D' | 'L' | 'R' | 'F' | 'B';
export type Turn = 1 | -1 | 2;
export type Axis = 'x' | 'y' | 'z';

export interface Move {
  face: Face;
  turns: Turn;
}

export const FACE_ORDER: Face[] = ['U', 'D', 'L', 'R', 'F', 'B'];

export function isFace(value: string): value is Face {
  return FACE_ORDER.includes(value as Face);
}

export function parseMove(key: string, shiftKey: boolean): Move | null {
  const face = key.toUpperCase();
  if (!isFace(face)) {
    return null;
  }
  return {
    face,
    turns: shiftKey ? -1 : 1
  };
}

export const FACE_INFO = {
  U: { axis: 'y', axisSign: 1, layer: 1 },
  D: { axis: 'y', axisSign: -1, layer: -1 },
  L: { axis: 'x', axisSign: -1, layer: -1 },
  R: { axis: 'x', axisSign: 1, layer: 1 },
  F: { axis: 'z', axisSign: 1, layer: 1 },
  B: { axis: 'z', axisSign: -1, layer: -1 }
} as const;

export const SCRAMBLE_TURNS: Turn[] = [1, -1, 2];

export function formatMove(move: Move): string {
  if (move.turns === -1) {
    return `${move.face}'`;
  }
  if (move.turns === 2) {
    return `${move.face}2`;
  }
  return move.face;
}

export function formatScramble(moves: Move[]): string {
  return moves.map(formatMove).join(' ');
}

export function generateOfficialLikeScramble(length: number, random: () => number = Math.random): Move[] {
  if (!Number.isInteger(length) || length <= 0) {
    throw new Error(`Scramble length must be a positive integer, received: ${length}`);
  }

  const moves: Move[] = [];

  while (moves.length < length) {
    const candidates = FACE_ORDER.filter((face) => isAllowedNextFace(moves, face));
    const face = candidates[Math.floor(random() * candidates.length)];
    const turns = SCRAMBLE_TURNS[Math.floor(random() * SCRAMBLE_TURNS.length)];
    moves.push({ face, turns });
  }

  return moves;
}

export function getQuarterTurnCount(turns: Turn): number {
  return turns === 2 ? 2 : 1;
}

export function getQuarterTurnDirection(turns: Exclude<Turn, 2> | 2): 1 | -1 {
  return turns === -1 ? 1 : -1;
}

function isAllowedNextFace(scramble: Move[], nextFace: Face): boolean {
  const lastMove = scramble[scramble.length - 1];
  if (lastMove?.face === nextFace) {
    return false;
  }

  const secondLastMove = scramble[scramble.length - 2];
  if (!lastMove || !secondLastMove) {
    return true;
  }

  const recentAxis = FACE_INFO[lastMove.face].axis;
  return !(
    FACE_INFO[secondLastMove.face].axis === recentAxis &&
    FACE_INFO[nextFace].axis === recentAxis
  );
}
