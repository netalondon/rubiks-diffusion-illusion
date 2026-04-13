import * as THREE from 'three';
import { FACE_NORMALS, FACE_UP_VECTORS } from './model';
import type { Cubie, Sticker, Vec3 } from './model';
import type { Face } from './moves';
import type { FaceArtImages } from './faceArt';

const INTERNAL_COLOR = '#1b1b1b';
const STICKER_COLOR = '#ffffff';
const TILE_TEXTURE_SIZE = 256;

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
  private faceArtImages: FaceArtImages;
  private meshMap: Map<string, THREE.Mesh> = new Map();
  private textureCache: Map<string, THREE.CanvasTexture> = new Map();
  private size: number;
  private gap: number;

  constructor(parent: THREE.Object3D, faceArtImages: FaceArtImages, size = 0.9, gap = 0.08) {
    this.parent = parent;
    this.faceArtImages = faceArtImages;
    this.size = size;
    this.gap = gap;
  }

  build(cubies: Cubie[]): void {
    const geometry = new THREE.BoxGeometry(this.size, this.size, this.size);

    for (const cubie of cubies) {
      const materials = createCubieMaterials();
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
        const material = materials[index] as THREE.MeshStandardMaterial;
        const sticker = findStickerForFace(cubie, face);

        if (!sticker) {
          material.map = null;
          material.color.set(INTERNAL_COLOR);
          material.needsUpdate = true;
          continue;
        }

        material.map = this.getStickerTexture(sticker, face);
        material.color.set(STICKER_COLOR);
        material.needsUpdate = true;
      }
    }
  }

  getMesh(id: string): THREE.Mesh | undefined {
    return this.meshMap.get(id);
  }

  private getStickerTexture(sticker: Sticker, currentFace: Face): THREE.CanvasTexture {
    const rotation = getStickerRotationQuarter(sticker, currentFace);
    const cacheKey = `${sticker.artFace}:${sticker.row}:${sticker.col}:${rotation}`;
    const existing = this.textureCache.get(cacheKey);

    if (existing) {
      return existing;
    }

    const image = this.faceArtImages[sticker.artFace];
    const tileWidth = image.width / 3;
    const tileHeight = image.height / 3;
    const canvas = document.createElement('canvas');
    canvas.width = TILE_TEXTURE_SIZE;
    canvas.height = TILE_TEXTURE_SIZE;

    const context = canvas.getContext('2d');
    if (!context) {
      throw new Error('Canvas 2D context unavailable');
    }

    context.translate(TILE_TEXTURE_SIZE / 2, TILE_TEXTURE_SIZE / 2);
    context.rotate(rotation * (Math.PI / 2));
    context.drawImage(
      image,
      sticker.col * tileWidth,
      sticker.row * tileHeight,
      tileWidth,
      tileHeight,
      -TILE_TEXTURE_SIZE / 2,
      -TILE_TEXTURE_SIZE / 2,
      TILE_TEXTURE_SIZE,
      TILE_TEXTURE_SIZE
    );

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.anisotropy = 4;
    this.textureCache.set(cacheKey, texture);
    return texture;
  }
}

function createCubieMaterials(): THREE.MeshStandardMaterial[] {
  const materials: THREE.MeshStandardMaterial[] = [];
  const faces: Face[] = ['R', 'L', 'U', 'D', 'F', 'B'];

  for (const _face of faces) {
    materials.push(
      new THREE.MeshStandardMaterial({
        color: INTERNAL_COLOR,
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

function findStickerForFace(cubie: Cubie, face: Face): Sticker | undefined {
  const normal = FACE_NORMALS[face];
  return cubie.stickers.find((sticker) => vectorsEqual(sticker.normal, normal));
}

function getStickerRotationQuarter(sticker: Sticker, currentFace: Face): number {
  const faceUp = FACE_UP_VECTORS[currentFace];
  const faceRight = cross(faceUp, FACE_NORMALS[currentFace]);

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
