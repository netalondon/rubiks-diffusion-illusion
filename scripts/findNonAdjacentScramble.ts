import { performance } from 'node:perf_hooks';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { projectVisibleFaces, hasWithinFaceAdjacentColors } from '../src/cube/faceState';
import { CubeModel } from '../src/cube/model';
import { formatScramble, generateOfficialLikeScramble } from '../src/cube/moves';
import { DEFAULT_OUTPUT_PATH, writeGeneratedScrambleFile } from './generatedScrambleFile';

interface SearchOptions {
  length: number;
  maxAttempts: number;
  progressEvery: number;
  output: string;
}

const DEFAULT_OPTIONS: SearchOptions = {
  length: 20,
  maxAttempts: Number.POSITIVE_INFINITY,
  progressEvery: 10_000,
  output: DEFAULT_OUTPUT_PATH
};

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const startedAt = performance.now();

  for (let attempts = 1; attempts <= options.maxAttempts; attempts += 1) {
    const scramble = generateOfficialLikeScramble(options.length);
    const cube = new CubeModel();

    for (const move of scramble) {
      cube.applyMove(move);
    }

    const faces = projectVisibleFaces(cube.getCubies());
    if (!hasWithinFaceAdjacentColors(faces)) {
      const elapsedMs = performance.now() - startedAt;
      const record = createGeneratedScrambleRecord(scramble, attempts, elapsedMs);
      const outputPath = await writeGeneratedScrambleFile(record, options.output);
      console.log(`Found scramble after ${attempts.toLocaleString()} attempts in ${formatElapsed(elapsedMs)}.`);
      console.log(formatScramble(scramble));
      console.log(`Saved to ${outputPath}.`);
      return;
    }

    if (attempts % options.progressEvery === 0) {
      const elapsedMs = performance.now() - startedAt;
      const attemptsPerSecond = attempts / (elapsedMs / 1_000);
      console.log(
        `Checked ${attempts.toLocaleString()} scrambles in ${formatElapsed(elapsedMs)} (${attemptsPerSecond.toFixed(1)} / sec).`
      );
    }
  }

  const elapsedMs = performance.now() - startedAt;
  console.error(
    `No scramble found after ${options.maxAttempts.toLocaleString()} attempts in ${formatElapsed(elapsedMs)}.`
  );
  process.exitCode = 1;
}

function parseArgs(argv: string[]): SearchOptions {
  const options = { ...DEFAULT_OPTIONS };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = argv[index + 1];

    switch (arg) {
      case '--length':
        options.length = parsePositiveInteger(arg, value);
        index += 1;
        break;
      case '--max-attempts':
        options.maxAttempts = parsePositiveInteger(arg, value);
        index += 1;
        break;
      case '--progress-every':
        options.progressEvery = parsePositiveInteger(arg, value);
        index += 1;
        break;
      case '--output':
        if (!value) {
          throw new Error(`Missing value for ${arg}`);
        }
        options.output = value;
        index += 1;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
}

function parsePositiveInteger(flag: string, value: string | undefined): number {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`Expected a positive integer for ${flag}, received: ${value}`);
  }

  return parsed;
}

function formatElapsed(milliseconds: number): string {
  if (milliseconds < 1_000) {
    return `${milliseconds.toFixed(0)}ms`;
  }

  const totalSeconds = milliseconds / 1_000;
  if (totalSeconds < 60) {
    return `${totalSeconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds - minutes * 60;
  return `${minutes}m ${seconds.toFixed(1)}s`;
}

function createGeneratedScrambleRecord(
  scramble: ReturnType<typeof generateOfficialLikeScramble>,
  attempts: number,
  elapsedMs: number
): GeneratedScrambleRecord {
  return {
    scramble: formatScramble(scramble),
    moves: scramble,
    length: scramble.length,
    attempts,
    elapsedMs,
    foundAt: new Date().toISOString(),
    adjacencyRule: 'within-face-only',
    scrambleRule: 'official-like'
  };
}

try {
  await main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exitCode = 1;
}
