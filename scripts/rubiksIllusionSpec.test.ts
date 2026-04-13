import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { createRubiksIllusionSpec } from '../src/cube/illusionSpec';

test('createRubiksIllusionSpec exports solved and scrambled arrangements', async () => {
  const inputPath = path.resolve('public/generated/non-adjacent-scramble.json');
  const record = JSON.parse(await readFile(inputPath, 'utf8')) as GeneratedScrambleRecord;
  const spec = createRubiksIllusionSpec(record);

  assert.equal(spec.version, 1);
  assert.deepEqual(spec.primeImages, ['U', 'D', 'L', 'R', 'F', 'B']);
  assert.equal(spec.arrangements.solved.length, 6);
  assert.equal(spec.arrangements.scrambled.length, 6);

  const solvedFrontTopLeft = spec.arrangements.solved.find((face) => face.face === 'F')?.grid[0][0];
  assert.deepEqual(solvedFrontTopLeft, {
    sourceFace: 'F',
    sourceRow: 0,
    sourceCol: 0,
    rotationQuarterTurns: 0
  });

  const scrambledFrontTopLeft = spec.arrangements.scrambled.find((face) => face.face === 'F')?.grid[0][0];
  assert.deepEqual(scrambledFrontTopLeft, {
    sourceFace: 'R',
    sourceRow: 0,
    sourceCol: 0,
    rotationQuarterTurns: 0
  });
});
