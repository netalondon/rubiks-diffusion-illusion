import * as THREE from 'three';
import type { Face } from '../cube/moves';

const FACE_NORMALS: Record<Face, THREE.Vector3> = {
  R: new THREE.Vector3(1, 0, 0),
  L: new THREE.Vector3(-1, 0, 0),
  U: new THREE.Vector3(0, 1, 0),
  D: new THREE.Vector3(0, -1, 0),
  F: new THREE.Vector3(0, 0, 1),
  B: new THREE.Vector3(0, 0, -1)
};

const FACE_KEYS: Face[] = ['R', 'L', 'U', 'D', 'F', 'B'];

export interface FaceMapping {
  mapping: Record<Face, Face>;
  scores: Record<Face, number>;
}

export function computeFaceMapping(
  cubeRoot: THREE.Object3D,
  camera: THREE.Camera,
  lastMapping: Record<Face, Face>,
  epsilon = 1e-4
): Record<Face, Face> {
  const cubeQuat = cubeRoot.quaternion;
  const cameraQuat = camera.quaternion;

  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(cameraQuat).normalize();
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(cameraQuat).normalize();
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(cameraQuat).normalize();

  const directionByKey: Record<Face, THREE.Vector3> = {
    R: right,
    L: right.clone().negate(),
    U: up,
    D: up.clone().negate(),
    F: forward.clone().negate(),
    B: forward
  };

  const faceWorldNormals: Record<Face, THREE.Vector3> = {
    R: FACE_NORMALS.R.clone().applyQuaternion(cubeQuat).normalize(),
    L: FACE_NORMALS.L.clone().applyQuaternion(cubeQuat).normalize(),
    U: FACE_NORMALS.U.clone().applyQuaternion(cubeQuat).normalize(),
    D: FACE_NORMALS.D.clone().applyQuaternion(cubeQuat).normalize(),
    F: FACE_NORMALS.F.clone().applyQuaternion(cubeQuat).normalize(),
    B: FACE_NORMALS.B.clone().applyQuaternion(cubeQuat).normalize()
  };

  const mapping: Record<Face, Face> = { ...lastMapping };

  for (const key of FACE_KEYS) {
    const dir = directionByKey[key];
    let bestFace: Face = 'R';
    let bestScore = -Infinity;
    let secondScore = -Infinity;

    for (const face of FACE_KEYS) {
      const score = faceWorldNormals[face].dot(dir);
      if (score > bestScore) {
        secondScore = bestScore;
        bestScore = score;
        bestFace = face;
      } else if (score > secondScore) {
        secondScore = score;
      }
    }

    if (bestScore - secondScore >= epsilon) {
      mapping[key] = bestFace;
    }
  }

  return mapping;
}
