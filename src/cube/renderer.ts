import * as THREE from 'three';
import type { Cubie, Vec3 } from './model';
import type { Face } from './moves';

const INTERNAL_COLOR = '#1b1b1b';

const FACE_TO_INDEX: Record<Face, number> = {
  R: 0,
  L: 1,
  U: 2,
  D: 3,
  F: 4,
  B: 5
};

export class CubeRenderer {
  private parent: THREE.Object3D;
  private meshMap: Map<string, THREE.Mesh> = new Map();
  private size: number;
  private gap: number;

  constructor(parent: THREE.Object3D, size = 0.9, gap = 0.08) {
    this.parent = parent;
    this.size = size;
    this.gap = gap;
  }

  build(cubies: Cubie[]): void {
    const geometry = new THREE.BoxGeometry(this.size, this.size, this.size);

    for (const cubie of cubies) {
      const materials = createCubieMaterials(cubie);
      const mesh = new THREE.Mesh(geometry, materials);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.meshMap.set(cubie.id, mesh);
      this.parent.add(mesh);
    }

    this.applyModel(cubies);
  }

  applyModel(cubies: Cubie[]): void {
    for (const cubie of cubies) {
      const mesh = this.meshMap.get(cubie.id);
      if (!mesh) continue;
      const position = toWorldPosition(cubie.position, this.size + this.gap);
      mesh.position.set(position.x, position.y, position.z);
      mesh.rotation.set(0, 0, 0);

      const materials = mesh.material as THREE.Material[];
      for (const [face, index] of Object.entries(FACE_TO_INDEX) as Array<[Face, number]>) {
        const color = cubie.colors[face] ?? INTERNAL_COLOR;
        (materials[index] as THREE.MeshStandardMaterial).color.set(color);
      }
    }
  }

  getMesh(id: string): THREE.Mesh | undefined {
    return this.meshMap.get(id);
  }
}

function createCubieMaterials(cubie: Cubie): THREE.MeshStandardMaterial[] {
  const materials: THREE.MeshStandardMaterial[] = [];
  const faces: Face[] = ['R', 'L', 'U', 'D', 'F', 'B'];

  for (const face of faces) {
    materials.push(
      new THREE.MeshStandardMaterial({
        color: cubie.colors[face] ?? INTERNAL_COLOR,
        roughness: 0.25,
        metalness: 0.05
      })
    );
  }

  return materials;
}

function toWorldPosition(position: Vec3, spacing: number): Vec3 {
  return {
    x: position.x * spacing,
    y: position.y * spacing,
    z: position.z * spacing
  };
}
