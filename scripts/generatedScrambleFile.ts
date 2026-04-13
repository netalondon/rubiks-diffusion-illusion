import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';

export const DEFAULT_OUTPUT_PATH = 'public/generated/non-adjacent-scramble.json';

export async function writeGeneratedScrambleFile(
  record: GeneratedScrambleRecord,
  outputPath: string = DEFAULT_OUTPUT_PATH
): Promise<string> {
  const resolvedPath = path.resolve(outputPath);
  await mkdir(path.dirname(resolvedPath), { recursive: true });
  await writeFile(resolvedPath, `${JSON.stringify(record, null, 2)}\n`, 'utf8');
  return resolvedPath;
}
