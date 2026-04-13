import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import test from 'node:test';
import type { GeneratedScrambleRecord } from '../src/cube/generatedScramble';
import { FACE_ORDER } from '../src/cube/moves';
import { applyMovesAndProjectStickerPlacements } from '../src/cube/stickerPlacement';

test('solved cube sticker placements are identity mappings', () => {
  const placementGrid = applyMovesAndProjectStickerPlacements([]);

  for (const face of FACE_ORDER) {
    for (let row = 0; row < 3; row += 1) {
      for (let col = 0; col < 3; col += 1) {
        const placement = placementGrid[face][row][col];
        assert.equal(placement.sourceFace, face);
        assert.equal(placement.sourceRow, row);
        assert.equal(placement.sourceCol, col);
        assert.equal(placement.rotationQuarterTurns, 0);
      }
    }
  }
});

test('saved scramble still uses every source sticker exactly once', async () => {
  const inputPath = path.resolve('public/generated/non-adjacent-scramble.json');
  const record = JSON.parse(await readFile(inputPath, 'utf8')) as GeneratedScrambleRecord;
  const placementGrid = applyMovesAndProjectStickerPlacements(record.moves);
  const seenSourceStickers = new Set<string>();

  for (const face of FACE_ORDER) {
    for (const row of placementGrid[face]) {
      for (const placement of row) {
        const sourceKey = `${placement.sourceFace}:${placement.sourceRow}:${placement.sourceCol}`;
        assert.equal(seenSourceStickers.has(sourceKey), false, `duplicate source sticker ${sourceKey}`);
        seenSourceStickers.add(sourceKey);
        assert.ok(placement.rotationQuarterTurns >= 0 && placement.rotationQuarterTurns <= 3);
      }
    }
  }

  assert.equal(seenSourceStickers.size, 54);
});
