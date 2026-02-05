export type Face = 'U' | 'D' | 'L' | 'R' | 'F' | 'B';
export type Turn = 1 | -1;

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

export type Axis = 'x' | 'y' | 'z';
