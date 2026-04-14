import type { Cubie } from './model';
import type { Face } from './moves';
import { createFaceGrid, toFaceCoordinates, toVisibleFace } from './projection';

export type FaceGrid = string[][];
export type VisibleFaces = Record<Face, FaceGrid>;

export function projectVisibleFaces(cubies: Cubie[]): VisibleFaces {
  const faces = createVisibleFaces();

  for (const cubie of cubies) {
    for (const sticker of cubie.stickers) {
      const visibleFace = toVisibleFace(sticker.normal);
      const [row, column] = toFaceCoordinates(visibleFace, cubie.position);
      faces[visibleFace][row][column] = sticker.artFace;
    }
  }

  return faces;
}

export function hasWithinFaceAdjacentColors(faces: VisibleFaces): boolean {
  return (Object.keys(faces) as Face[]).some((face) => faceHasAdjacentColors(faces[face]));
}

export function faceHasAdjacentColors(face: FaceGrid): boolean {
  for (let row = 0; row < face.length; row += 1) {
    for (let column = 0; column < face[row].length; column += 1) {
      const color = face[row][column];
      if (!color) {
        continue;
      }

      if (row + 1 < face.length && face[row + 1][column] === color) {
        return true;
      }

      if (column + 1 < face[row].length && face[row][column + 1] === color) {
        return true;
      }
    }
  }

  return false;
}

function createVisibleFaces(): VisibleFaces {
  return {
    U: createFaceGrid(''),
    D: createFaceGrid(''),
    L: createFaceGrid(''),
    R: createFaceGrid(''),
    F: createFaceGrid(''),
    B: createFaceGrid('')
  };
}
