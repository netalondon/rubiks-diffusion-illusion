import * as THREE from 'three';
export interface SceneBundle {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
}

export function setupScene(container: HTMLElement): SceneBundle {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#e9e4db');

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(5, 5, 6.5);
  camera.lookAt(0, 0, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight('#ffffff', 0.6);
  scene.add(ambientLight);

  const keyLight = new THREE.DirectionalLight('#ffffff', 0.8);
  keyLight.position.set(6, 8, 5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight('#fff1d6', 0.4);
  fillLight.position.set(-6, 4, -3);
  scene.add(fillLight);

  function resize() {
    const { clientWidth, clientHeight } = container;
    camera.aspect = clientWidth / clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(clientWidth, clientHeight);
  }

  window.addEventListener('resize', resize);
  resize();

  return { scene, camera, renderer };
}
