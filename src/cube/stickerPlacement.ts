import { CubeModel, FACE_NORMALS, FACE_UP_VECTORS } from './model';
import type { Cubie, Sticker, StickerIndex, Vec3 } from './model';
import { FACE_ORDER } from './moves';
import type { Face, Move } from './moves';

export interface StickerPlacement {
  cubieId: string;
  sourceFace: Face;
  sourceRow: StickerIndex;
  sourceCol: StickerIndex;
  visibleFace: Face;
  visibleRow: StickerIndex;
  visibleCol: StickerIndex;
  rotationQuarterTurns: 0 | 1 | 2 | 3;
}

export type StickerPlacementGrid = Record<Face, StickerPlacement[][]>;

export function applyMovesAndProjectStickerPlacements(moves: Move[]): StickerPlacementGrid {
  const cube = new CubeModel();

  for (const move of moves) {
    cube.applyMove(move);
  }

  return createStickerPlacementGrid(projectVisibleStickerPlacements(cube.getCubies()));
}

export function projectVisibleStickerPlacements(cubies: Cubie[]): StickerPlacement[] {
  return cubies
    .flatMap((cubie) =>
      cubie.stickers.map((sticker) => {
        const visibleFace = toVisibleFace(sticker.normal);
        const [visibleRow, visibleCol] = toFaceCoordinates(visibleFace, cubie.position);

        return {
          cubieId: cubie.id,
          sourceFace: sticker.artFace,
          sourceRow: sticker.row,
          sourceCol: sticker.col,
          visibleFace,
          visibleRow,
          visibleCol,
          rotationQuarterTurns: getStickerRotationQuarterTurns(sticker, visibleFace)
        };
      })
    )
    .sort(comparePlacements);
}

export function createStickerPlacementGrid(placements: StickerPlacement[]): StickerPlacementGrid {
  const grid = Object.fromEntries(
    FACE_ORDER.map((face) => [face, createEmptyFaceGrid<StickerPlacement | null>(null)])
  ) as Record<Face, Array<Array<StickerPlacement | null>>>;

  for (const placement of placements) {
    grid[placement.visibleFace][placement.visibleRow][placement.visibleCol] = placement;
  }

  return Object.fromEntries(
    FACE_ORDER.map((face) => {
      const faceGrid = grid[face].map((row) =>
        row.map((placement) => {
          if (!placement) {
            throw new Error(`Missing sticker placement for ${face}`);
          }
          return placement;
        })
      );

      return [face, faceGrid];
    })
  ) as StickerPlacementGrid;
}

function comparePlacements(a: StickerPlacement, b: StickerPlacement): number {
  return (
    FACE_ORDER.indexOf(a.visibleFace) - FACE_ORDER.indexOf(b.visibleFace) ||
    a.visibleRow - b.visibleRow ||
    a.visibleCol - b.visibleCol
  );
}

function createEmptyFaceGrid<T>(value: T): T[][] {
  return Array.from({ length: 3 }, () => [value, value, value]);
}

function toFaceCoordinates(face: Face, position: Vec3): [StickerIndex, StickerIndex] {
  switch (face) {
    case 'U':
      return [toStickerIndex(position.z + 1), toStickerIndex(position.x + 1)];
    case 'D':
      return [toStickerIndex(1 - position.z), toStickerIndex(position.x + 1)];
    case 'L':
      return [toStickerIndex(1 - position.y), toStickerIndex(position.z + 1)];
    case 'R':
      return [toStickerIndex(1 - position.y), toStickerIndex(1 - position.z)];
    case 'F':
      return [toStickerIndex(1 - position.y), toStickerIndex(position.x + 1)];
    case 'B':
      return [toStickerIndex(1 - position.y), toStickerIndex(1 - position.x)];
  }
}

function toVisibleFace(normal: Vec3): Face {
  for (const face of FACE_ORDER) {
    const expected = FACE_NORMALS[face];
    if (expected.x === normal.x && expected.y === normal.y && expected.z === normal.z) {
      return face;
    }
  }

  throw new Error(`Unsupported sticker normal: ${JSON.stringify(normal)}`);
}

function getStickerRotationQuarterTurns(sticker: Sticker, visibleFace: Face): 0 | 1 | 2 | 3 {
  const faceUp = FACE_UP_VECTORS[visibleFace];
  const faceRight = cross(faceUp, FACE_NORMALS[visibleFace]);

  if (vectorsEqual(sticker.up, faceUp)) return 0;
  if (vectorsEqual(sticker.up, faceRight)) return 1;
  if (vectorsEqual(sticker.up, negate(faceUp))) return 2;
  return 3;
}

function cross(a: Vec3, b: Vec3): Vec3 {
  return {
    x: a.y * b.z - a.z * b.y,
    y: a.z * b.x - a.x * b.z,
    z: a.x * b.y - a.y * b.x
  };
}

function negate(vector: Vec3): Vec3 {
  return {
    x: -vector.x,
    y: -vector.y,
    z: -vector.z
  };
}

function vectorsEqual(a: Vec3, b: Vec3): boolean {
  return a.x === b.x && a.y === b.y && a.z === b.z;
}

function toStickerIndex(value: number): StickerIndex {
  if (value === 0 || value === 1 || value === 2) {
    return value;
  }

  throw new Error(`Invalid sticker index: ${value}`);
}
