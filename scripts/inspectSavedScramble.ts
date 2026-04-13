import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { FACE_ORDER } from '../src/cube/moves';
import { applyMovesAndProjectStickerPlacements } from '../src/cube/stickerPlacement';

const DEFAULT_INPUT_PATH = 'public/generated/non-adjacent-scramble.json';

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const record = await loadSavedScramble(options.input);
  const placementGrid = applyMovesAndProjectStickerPlacements(record.moves);

  const summary = {
    input: path.resolve(options.input),
    scramble: record.scramble,
    length: record.length,
    faces: Object.fromEntries(
      FACE_ORDER.map((face) => [
        face,
        placementGrid[face].map((row) =>
          row.map(
            (placement) =>
              `${placement.sourceFace}[${placement.sourceRow},${placement.sourceCol}] r${placement.rotationQuarterTurns}`
          )
        )
      ])
    )
  };

  const json = `${JSON.stringify(summary, null, 2)}\n`;

  if (options.output) {
    const resolvedOutput = path.resolve(options.output);
    await writeFile(resolvedOutput, json, 'utf8');
    console.log(`Saved sticker placement summary to ${resolvedOutput}`);
    return;
  }

  process.stdout.write(json);
}

async function loadSavedScramble(inputPath: string): Promise<GeneratedScrambleRecord> {
  const fileContents = await readFile(path.resolve(inputPath), 'utf8');
  return JSON.parse(fileContents) as GeneratedScrambleRecord;
}

function parseArgs(argv: string[]): { input: string; output?: string } {
  let input = DEFAULT_INPUT_PATH;
  let output: string | undefined;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = argv[index + 1];

    switch (arg) {
      case '--input':
        if (!value) {
          throw new Error(`Missing value for ${arg}`);
        }
        input = value;
        index += 1;
        break;
      case '--output':
        if (!value) {
          throw new Error(`Missing value for ${arg}`);
        }
        output = value;
        index += 1;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return { input, output };
}

try {
  await main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exitCode = 1;
}
