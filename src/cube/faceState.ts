import { FACE_NORMALS } from './model';
import type { Cubie, Vec3 } from './model';
import { FACE_ORDER } from './moves';
import type { Face } from './moves';

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
  return FACE_ORDER.some((face) => faceHasAdjacentColors(faces[face]));
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
    U: createFaceGrid(),
    D: createFaceGrid(),
    L: createFaceGrid(),
    R: createFaceGrid(),
    F: createFaceGrid(),
    B: createFaceGrid()
  };
}

function createFaceGrid(): FaceGrid {
  return Array.from({ length: 3 }, () => ['', '', '']);
}

function toFaceCoordinates(face: Face, position: Vec3): [number, number] {
  switch (face) {
    case 'U':
      return [position.z + 1, position.x + 1];
    case 'D':
      return [1 - position.z, position.x + 1];
    case 'L':
      return [1 - position.y, position.z + 1];
    case 'R':
      return [1 - position.y, 1 - position.z];
    case 'F':
      return [1 - position.y, position.x + 1];
    case 'B':
      return [1 - position.y, 1 - position.x];
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
