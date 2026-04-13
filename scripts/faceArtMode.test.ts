import assert from 'node:assert/strict';
import test from 'node:test';
import { resolveFaceArtModeFromUrlSearch } from '../src/cube/faceArt';

test('face art mode defaults to photo', () => {
  assert.equal(resolveFaceArtModeFromUrlSearch(''), 'photo');
  assert.equal(resolveFaceArtModeFromUrlSearch('?art=photo'), 'photo');
});

test('face art mode enables debug labels with the art query parameter', () => {
  assert.equal(resolveFaceArtModeFromUrlSearch('?art=debug'), 'debug');
  assert.equal(resolveFaceArtModeFromUrlSearch('?foo=1&art=debug'), 'debug');
});
