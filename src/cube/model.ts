import type { Axis, Face, Move } from './moves';
import { FACE_INFO } from './moves';

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export type StickerIndex = 0 | 1 | 2;

export interface Sticker {
  artFace: Face;
  row: StickerIndex;
  col: StickerIndex;
  normal: Vec3;
  up: Vec3;
}

export interface Cubie {
  id: string;
  position: Vec3;
  stickers: Sticker[];
}

export const FACE_NORMALS: Record<Face, Vec3> = {
  U: { x: 0, y: 1, z: 0 },
  D: { x: 0, y: -1, z: 0 },
  L: { x: -1, y: 0, z: 0 },
  R: { x: 1, y: 0, z: 0 },
  F: { x: 0, y: 0, z: 1 },
  B: { x: 0, y: 0, z: -1 }
};

export const FACE_UP_VECTORS: Record<Face, Vec3> = {
  U: { x: 0, y: 0, z: -1 },
  D: { x: 0, y: 0, z: 1 },
  L: { x: 0, y: 1, z: 0 },
  R: { x: 0, y: 1, z: 0 },
  F: { x: 0, y: 1, z: 0 },
  B: { x: 0, y: 1, z: 0 }
};

export class CubeModel {
  private cubies: Cubie[];

  constructor() {
    this.cubies = createSolvedCubies();
  }

  getCubies(): Cubie[] {
    return this.cubies;
  }

  applyMove(move: Move): void {
    const { axis, axisSign, layer } = FACE_INFO[move.face];
    const dir = -move.turns * axisSign;

    for (const cubie of this.cubies) {
      if (!isOnLayer(cubie.position, axis, layer)) {
        continue;
      }
      cubie.position = rotateVector(cubie.position, axis, dir);
      cubie.stickers = cubie.stickers.map((sticker) => ({
        ...sticker,
        normal: rotateVector(sticker.normal, axis, dir),
        up: rotateVector(sticker.up, axis, dir)
      }));
    }
  }
}

function createSolvedCubies(): Cubie[] {
  const cubies: Cubie[] = [];
  const coords = [-1, 0, 1];
  let index = 0;

  for (const x of coords) {
    for (const y of coords) {
      for (const z of coords) {
        const position = { x, y, z };
        const stickers: Sticker[] = [];
        if (y === 1) stickers.push(createSolvedSticker('U', position));
        if (y === -1) stickers.push(createSolvedSticker('D', position));
        if (x === -1) stickers.push(createSolvedSticker('L', position));
        if (x === 1) stickers.push(createSolvedSticker('R', position));
        if (z === 1) stickers.push(createSolvedSticker('F', position));
        if (z === -1) stickers.push(createSolvedSticker('B', position));

        cubies.push({
          id: `c${index++}`,
          position,
          stickers
        });
      }
    }
  }

  return cubies;
}

function isOnLayer(position: Vec3, axis: Axis, layer: number): boolean {
  return position[axis] === layer;
}

function createSolvedSticker(face: Face, position: Vec3): Sticker {
  return {
    artFace: face,
    row: getStickerRow(face, position),
    col: getStickerCol(face, position),
    normal: cloneVec3(FACE_NORMALS[face]),
    up: cloneVec3(FACE_UP_VECTORS[face])
  };
}

function getStickerRow(face: Face, position: Vec3): StickerIndex {
  if (face === 'U') return toStickerIndex(position.z + 1);
  if (face === 'D') return toStickerIndex(1 - position.z);
  return toStickerIndex(1 - position.y);
}

function getStickerCol(face: Face, position: Vec3): StickerIndex {
  if (face === 'F') return toStickerIndex(position.x + 1);
  if (face === 'B') return toStickerIndex(1 - position.x);
  if (face === 'R') return toStickerIndex(1 - position.z);
  if (face === 'L') return toStickerIndex(position.z + 1);
  return toStickerIndex(position.x + 1);
}

function toStickerIndex(value: number): StickerIndex {
  if (value === 0 || value === 1 || value === 2) {
    return value;
  }
  throw new Error(`Invalid sticker index: ${value}`);
}

function cloneVec3(vector: Vec3): Vec3 {
  return {
    x: vector.x,
    y: vector.y,
    z: vector.z
  };
}

function rotateVector(vector: Vec3, axis: Axis, dir: number): Vec3 {
  const { x, y, z } = vector;

  if (axis === 'x') {
    return dir === 1 ? { x, y: -z, z: y } : { x, y: z, z: -y };
  }
  if (axis === 'y') {
    return dir === 1 ? { x: z, y, z: -x } : { x: -z, y, z: x };
  }
  return dir === 1 ? { x: -y, y: x, z } : { x: y, y: -x, z };
}
