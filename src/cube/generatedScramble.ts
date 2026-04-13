import type { Move } from './moves';

export const GENERATED_SCRAMBLE_PATH = '/generated/non-adjacent-scramble.json';

export interface GeneratedScrambleRecord {
  scramble: string;
  moves: Move[];
  length: number;
  attempts: number;
  elapsedMs: number;
  foundAt: string;
  adjacencyRule: 'within-face-only';
  scrambleRule: 'official-like';
}

export async function loadGeneratedScramble(
  path: string = GENERATED_SCRAMBLE_PATH
): Promise<GeneratedScrambleRecord | null> {
  const response = await fetch(path, { cache: 'no-store' });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to load generated scramble from ${path}: ${response.status}`);
  }

  return (await response.json()) as GeneratedScrambleRecord;
}
