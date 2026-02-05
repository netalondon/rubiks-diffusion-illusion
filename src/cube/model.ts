import type { Axis, Face, Move } from './moves';
import { FACE_INFO } from './moves';

export interface Vec3 {
  x: number;
  y: number;
  z: number;
}

export interface Cubie {
  id: string;
  position: Vec3;
  colors: Partial<Record<Face, string>>;
}

const FACE_COLORS: Record<Face, string> = {
  U: '#f5f5f5',
  D: '#f9d648',
  L: '#f48c2a',
  R: '#d93025',
  F: '#34a853',
  B: '#1a73e8'
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
      cubie.position = rotatePosition(cubie.position, axis, dir);
      cubie.colors = rotateColors(cubie.colors, axis, dir);
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
        const colors: Partial<Record<Face, string>> = {};
        if (y === 1) colors.U = FACE_COLORS.U;
        if (y === -1) colors.D = FACE_COLORS.D;
        if (x === -1) colors.L = FACE_COLORS.L;
        if (x === 1) colors.R = FACE_COLORS.R;
        if (z === 1) colors.F = FACE_COLORS.F;
        if (z === -1) colors.B = FACE_COLORS.B;

        cubies.push({
          id: `c${index++}`,
          position: { x, y, z },
          colors
        });
      }
    }
  }

  return cubies;
}

function isOnLayer(position: Vec3, axis: Axis, layer: number): boolean {
  return position[axis] === layer;
}

function rotatePosition(position: Vec3, axis: Axis, dir: number): Vec3 {
  const { x, y, z } = position;

  if (axis === 'x') {
    return dir === 1 ? { x, y: -z, z: y } : { x, y: z, z: -y };
  }
  if (axis === 'y') {
    return dir === 1 ? { x: z, y, z: -x } : { x: -z, y, z: x };
  }
  return dir === 1 ? { x: -y, y: x, z } : { x: y, y: -x, z };
}

const ROTATE_MAP_POS: Record<Axis, Partial<Record<Face, Face>>> = {
  x: { U: 'F', F: 'D', D: 'B', B: 'U' },
  y: { R: 'F', F: 'L', L: 'B', B: 'R' },
  z: { R: 'D', D: 'L', L: 'U', U: 'R' }
};

const ROTATE_MAP_NEG: Record<Axis, Partial<Record<Face, Face>>> = {
  x: invertMap(ROTATE_MAP_POS.x),
  y: invertMap(ROTATE_MAP_POS.y),
  z: invertMap(ROTATE_MAP_POS.z)
};

function invertMap(map: Partial<Record<Face, Face>>): Partial<Record<Face, Face>> {
  const inverted: Partial<Record<Face, Face>> = {};
  for (const [from, to] of Object.entries(map) as Array<[Face, Face]>) {
    inverted[to] = from;
  }
  return inverted;
}

function rotateColors(colors: Partial<Record<Face, string>>, axis: Axis, dir: number): Partial<Record<Face, string>> {
  const map = dir === 1 ? ROTATE_MAP_POS[axis] : ROTATE_MAP_NEG[axis];
  const rotated: Partial<Record<Face, string>> = {};

  for (const [face, color] of Object.entries(colors) as Array<[Face, string]>) {
    rotated[map[face] ?? face] = color;
  }

  return rotated;
}
