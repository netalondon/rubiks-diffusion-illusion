import * as THREE from 'three';

interface DragOptions {
  sensitivity?: number;
}

export function bindCubeDrag(
  element: HTMLElement,
  cubeRoot: THREE.Object3D,
  camera: THREE.Camera,
  options: DragOptions = {}
): () => void {
  const sensitivity = options.sensitivity ?? 0.005;
  let isDragging = false;
  let startX = 0;
  let startY = 0;
  const startQuaternion = new THREE.Quaternion();

  const onPointerDown = (event: PointerEvent) => {
    if (event.button !== 0) {
      return;
    }
    isDragging = true;
    startX = event.clientX;
    startY = event.clientY;
    startQuaternion.copy(cubeRoot.quaternion);
    element.setPointerCapture(event.pointerId);
    event.preventDefault();
  };

  const onPointerMove = (event: PointerEvent) => {
    if (!isDragging) {
      return;
    }
    const deltaX = event.clientX - startX;
    const deltaY = event.clientY - startY;

    const rotationY = deltaX * sensitivity;
    const rotationX = deltaY * sensitivity;

    const qy = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), rotationY);
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).normalize();
    const qx = new THREE.Quaternion().setFromAxisAngle(right, rotationX);

    cubeRoot.quaternion.copy(startQuaternion).premultiply(qy).premultiply(qx).normalize();
    event.preventDefault();
  };

  const stopDrag = (event: PointerEvent) => {
    if (!isDragging) {
      return;
    }
    isDragging = false;
    element.releasePointerCapture(event.pointerId);
    event.preventDefault();
  };

  element.addEventListener('pointerdown', onPointerDown);
  element.addEventListener('pointermove', onPointerMove);
  element.addEventListener('pointerup', stopDrag);
  element.addEventListener('pointercancel', stopDrag);

  return () => {
    element.removeEventListener('pointerdown', onPointerDown);
    element.removeEventListener('pointermove', onPointerMove);
    element.removeEventListener('pointerup', stopDrag);
    element.removeEventListener('pointercancel', stopDrag);
  };
}
