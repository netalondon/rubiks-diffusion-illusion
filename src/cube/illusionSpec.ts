import type { GeneratedScrambleRecord } from './generatedScramble';
import { FACE_ORDER } from './moves';
import type { Face } from './moves';
import { applyMovesAndProjectStickerPlacements } from './stickerPlacement';

export interface IllusionStickerCell {
  sourceFace: Face;
  sourceRow: 0 | 1 | 2;
  sourceCol: 0 | 1 | 2;
  rotationQuarterTurns: 0 | 1 | 2 | 3;
}

export interface IllusionDerivedFace {
  face: Face;
  grid: IllusionStickerCell[][];
}

export interface RubiksIllusionSpec {
  version: 1;
  primeImages: Face[];
  sourceGridSize: 3;
  arrangements: {
    solved: IllusionDerivedFace[];
    scrambled: IllusionDerivedFace[];
  };
  scramble: {
    text: string;
    length: number;
  };
}

export function createRubiksIllusionSpec(record: GeneratedScrambleRecord): RubiksIllusionSpec {
  return {
    version: 1,
    primeImages: FACE_ORDER,
    sourceGridSize: 3,
    arrangements: {
      solved: toDerivedFaces([]),
      scrambled: toDerivedFaces(record.moves)
    },
    scramble: {
      text: record.scramble,
      length: record.length
    }
  };
}

function toDerivedFaces(moves: GeneratedScrambleRecord['moves']): IllusionDerivedFace[] {
  const placementGrid = applyMovesAndProjectStickerPlacements(moves);

  return FACE_ORDER.map((face) => ({
    face,
    grid: placementGrid[face].map((row) =>
      row.map((placement) => ({
        sourceFace: placement.sourceFace,
        sourceRow: placement.sourceRow,
        sourceCol: placement.sourceCol,
        rotationQuarterTurns: placement.rotationQuarterTurns
      }))
    )
  }));
}
