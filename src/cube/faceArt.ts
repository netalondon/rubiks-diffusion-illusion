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

export async function loadFaceArtImages(): Promise<FaceArtImages> {
  const entries = await Promise.all(
    Object.entries(FACE_ART_URLS).map(async ([face, url]) => [face, await loadImage(url)] as const)
  );

  return Object.fromEntries(entries) as FaceArtImages;
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
