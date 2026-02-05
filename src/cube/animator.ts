import * as THREE from 'three';
import type { CubeModel } from './model';
import type { Face, Move } from './moves';
import { FACE_INFO } from './moves';
import type { CubeRenderer } from './renderer';

interface ActiveTurn {
  move: Move;
  group: THREE.Group;
  cubieIds: string[];
  elapsed: number;
  duration: number;
}

export class CubeAnimator {
  private parent: THREE.Object3D;
  private model: CubeModel;
  private renderer: CubeRenderer;
  private queue: Move[] = [];
  private active: ActiveTurn | null = null;
  private durationMs: number;

  constructor(parent: THREE.Object3D, model: CubeModel, renderer: CubeRenderer, durationMs = 250) {
    this.parent = parent;
    this.model = model;
    this.renderer = renderer;
    this.durationMs = durationMs;
  }

  enqueue(move: Move): void {
    this.queue.push(move);
  }

  update(deltaMs: number): void {
    if (!this.active && this.queue.length > 0) {
      const next = this.queue.shift();
      if (next) {
        this.active = this.startMove(next);
      }
    }

    if (!this.active) {
      return;
    }

    const { axis, axisSign } = FACE_INFO[this.active.move.face];
    const dir = -this.active.move.turns * axisSign;

    this.active.elapsed += deltaMs;
    const progress = Math.min(this.active.elapsed / this.active.duration, 1);
    const angle = dir * (Math.PI / 2) * progress;

    if (axis === 'x') {
      this.active.group.rotation.x = angle;
    } else if (axis === 'y') {
      this.active.group.rotation.y = angle;
    } else {
      this.active.group.rotation.z = angle;
    }

    if (progress >= 1) {
      this.finishMove();
    }
  }

  isIdle(): boolean {
    return !this.active && this.queue.length === 0;
  }

  private startMove(move: Move): ActiveTurn {
    const group = new THREE.Group();
    this.parent.add(group);

    const cubieIds = getLayerCubieIds(this.model, move.face);
    for (const id of cubieIds) {
      const mesh = this.renderer.getMesh(id);
      if (mesh) {
        group.attach(mesh);
      }
    }

    return {
      move,
      group,
      cubieIds,
      elapsed: 0,
      duration: this.durationMs
    };
  }

  private finishMove(): void {
    if (!this.active) return;

    for (const id of this.active.cubieIds) {
      const mesh = this.renderer.getMesh(id);
      if (mesh) {
        this.parent.attach(mesh);
      }
    }

    this.parent.remove(this.active.group);

    this.model.applyMove(this.active.move);
    this.renderer.applyModel(this.model.getCubies());

    this.active = null;
  }
}

function getLayerCubieIds(model: CubeModel, face: Face): string[] {
  const { axis, layer } = FACE_INFO[face];
  return model
    .getCubies()
    .filter((cubie) => cubie.position[axis] === layer)
    .map((cubie) => cubie.id);
}
