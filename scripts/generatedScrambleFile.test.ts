import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { writeGeneratedScrambleFile } from './generatedScrambleFile';

test('writeGeneratedScrambleFile creates a JSON file the app can load later', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'cube-craft-scramble-'));
  const targetPath = path.join(directory, 'public', 'generated', 'non-adjacent-scramble.json');
  const record: GeneratedScrambleRecord = {
    scramble: "R U2 F'",
    moves: [
      { face: 'R', turns: 1 },
      { face: 'U', turns: 2 },
      { face: 'F', turns: -1 }
    ],
    length: 3,
    attempts: 12,
    elapsedMs: 45,
    foundAt: '2026-04-13T10:00:00.000Z',
    adjacencyRule: 'within-face-only',
    scrambleRule: 'official-like'
  };

  const writtenPath = await writeGeneratedScrambleFile(record, targetPath);
  const fileContents = await readFile(writtenPath, 'utf8');

  assert.equal(writtenPath, targetPath);
  assert.deepEqual(JSON.parse(fileContents), record);
});
