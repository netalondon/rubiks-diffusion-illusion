import { CubeModel } from './model';
import type { Cubie, StickerIndex } from './model';
import { FACE_ORDER } from './moves';
import type { Face, Move } from './moves';
import { createFaceGrid, getStickerRotationQuarterTurns, toFaceCoordinates, toVisibleFace } from './projection';

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
    FACE_ORDER.map((face) => [face, createFaceGrid<StickerPlacement | null>(null)])
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
