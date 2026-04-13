import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { createRubiksIllusionSpec } from '../src/cube/illusionSpec';

const DEFAULT_INPUT_PATH = 'public/generated/non-adjacent-scramble.json';
const DEFAULT_OUTPUT_PATH = 'public/generated/rubiks-illusion-spec.json';

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const record = await loadSavedScramble(options.input);
  const spec = createRubiksIllusionSpec(record);
  const outputPath = path.resolve(options.output);

  await writeFile(outputPath, `${JSON.stringify(spec, null, 2)}\n`, 'utf8');
  console.log(`Saved Rubik's illusion spec to ${outputPath}`);
}

async function loadSavedScramble(inputPath: string): Promise<GeneratedScrambleRecord> {
  const fileContents = await readFile(path.resolve(inputPath), 'utf8');
  return JSON.parse(fileContents) as GeneratedScrambleRecord;
}

function parseArgs(argv: string[]): { input: string; output: string } {
  let input = DEFAULT_INPUT_PATH;
  let output = DEFAULT_OUTPUT_PATH;

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
