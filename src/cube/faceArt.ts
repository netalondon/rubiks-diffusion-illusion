import type { Face } from './moves';

const FACE_ART_URLS: Record<Face, string> = {
  U: new URL('../assets/face-art/up.png', import.meta.url).href,
  D: new URL('../assets/face-art/down.png', import.meta.url).href,
  L: new URL('../assets/face-art/left.png', import.meta.url).href,
  R: new URL('../assets/face-art/right.png', import.meta.url).href,
  F: new URL('../assets/face-art/front.png', import.meta.url).href,
  B: new URL('../assets/face-art/back.png', import.meta.url).href
};

export type FaceArtImages = Record<Face, HTMLImageElement>;
export type FaceArtMode = 'photo' | 'debug';

const DEBUG_FACE_COLORS: Record<Face, { fill: string; accent: string; ink: string }> = {
  U: { fill: '#fff6bf', accent: '#d4a017', ink: '#342800' },
  D: { fill: '#ffe1c2', accent: '#d96a12', ink: '#3d1e00' },
  L: { fill: '#d8f5cf', accent: '#4b8f2c', ink: '#16330b' },
  R: { fill: '#ffd6d6', accent: '#b43b3b', ink: '#421111' },
  F: { fill: '#d6ecff', accent: '#2e75b6', ink: '#10253a' },
  B: { fill: '#ece0ff', accent: '#6f52b8', ink: '#27173f' }
};

const DEBUG_IMAGE_SIZE = 900;
const DEBUG_TILE_SIZE = DEBUG_IMAGE_SIZE / 3;

export async function loadFaceArtImages(mode: FaceArtMode = 'photo'): Promise<FaceArtImages> {
  if (mode === 'debug') {
    return createDebugFaceArtImages();
  }

  const entries = await Promise.all(
    Object.entries(FACE_ART_URLS).map(async ([face, url]) => [face, await loadImage(url)] as const)
  );

  return Object.fromEntries(entries) as FaceArtImages;
}

export function resolveFaceArtModeFromUrlSearch(search: string): FaceArtMode {
  const params = new URLSearchParams(search);
  return params.get('art') === 'debug' ? 'debug' : 'photo';
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.decoding = 'async';
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`Failed to load face art: ${url}`));
    image.src = url;
  });
}

async function createDebugFaceArtImages(): Promise<FaceArtImages> {
  const entries = await Promise.all(
    (Object.keys(DEBUG_FACE_COLORS) as Face[]).map(async (face) => [face, await createDebugFaceImage(face)] as const)
  );

  return Object.fromEntries(entries) as FaceArtImages;
}

async function createDebugFaceImage(face: Face): Promise<HTMLImageElement> {
  const canvas = document.createElement('canvas');
  canvas.width = DEBUG_IMAGE_SIZE;
  canvas.height = DEBUG_IMAGE_SIZE;

  const context = canvas.getContext('2d');
  if (!context) {
    throw new Error('Canvas 2D context unavailable');
  }

  const colors = DEBUG_FACE_COLORS[face];

  context.fillStyle = colors.fill;
  context.fillRect(0, 0, DEBUG_IMAGE_SIZE, DEBUG_IMAGE_SIZE);

  for (let row = 0; row < 3; row += 1) {
    for (let col = 0; col < 3; col += 1) {
      const x = col * DEBUG_TILE_SIZE;
      const y = row * DEBUG_TILE_SIZE;

      context.fillStyle = row === 1 && col === 1 ? colors.accent : colors.fill;
      context.fillRect(x, y, DEBUG_TILE_SIZE, DEBUG_TILE_SIZE);

      context.strokeStyle = colors.accent;
      context.lineWidth = 12;
      context.strokeRect(x + 6, y + 6, DEBUG_TILE_SIZE - 12, DEBUG_TILE_SIZE - 12);

      context.fillStyle = colors.ink;
      context.textAlign = 'center';
      context.textBaseline = 'middle';

      context.font = 'bold 108px "Space Grotesk", sans-serif';
      context.fillText(face, x + DEBUG_TILE_SIZE / 2, y + DEBUG_TILE_SIZE / 2 - 44);

      context.font = '600 54px "Space Mono", monospace';
      context.fillText(`${row},${col}`, x + DEBUG_TILE_SIZE / 2, y + DEBUG_TILE_SIZE / 2 + 42);
    }
  }

  context.strokeStyle = colors.ink;
  context.lineWidth = 16;
  context.strokeRect(8, 8, DEBUG_IMAGE_SIZE - 16, DEBUG_IMAGE_SIZE - 16);

  return loadImage(canvas.toDataURL('image/png'));
}
