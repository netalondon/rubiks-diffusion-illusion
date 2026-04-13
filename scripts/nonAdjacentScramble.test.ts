import assert from 'node:assert/strict';
import test from 'node:test';
import { faceHasAdjacentColors } from '../src/cube/faceState';
import { FACE_INFO, generateOfficialLikeScramble } from '../src/cube/moves';

test('face adjacency ignores diagonal-only matches', () => {
  const face = [
    ['red', 'blue', 'green'],
    ['orange', 'red', 'yellow'],
    ['white', 'teal', 'purple']
  ];

  assert.equal(faceHasAdjacentColors(face), false);
});

test('face adjacency catches orthogonal matches', () => {
  const face = [
    ['red', 'blue', 'green'],
    ['orange', 'red', 'red'],
    ['white', 'teal', 'purple']
  ];

  assert.equal(faceHasAdjacentColors(face), true);
});

test('generated scrambles avoid repeated faces and triple-axis runs', () => {
  const seededValues = [0.02, 0.31, 0.64, 0.91, 0.18, 0.47, 0.73];
  let index = 0;
  const scramble = generateOfficialLikeScramble(60, () => {
    const value = seededValues[index % seededValues.length];
    index += 1;
    return value;
  });

  assert.equal(scramble.length, 60);

  for (let moveIndex = 1; moveIndex < scramble.length; moveIndex += 1) {
    assert.notEqual(scramble[moveIndex].face, scramble[moveIndex - 1].face);
  }

  for (let moveIndex = 2; moveIndex < scramble.length; moveIndex += 1) {
    const currentAxis = FACE_INFO[scramble[moveIndex].face].axis;
    const previousAxis = FACE_INFO[scramble[moveIndex - 1].face].axis;
    const secondPreviousAxis = FACE_INFO[scramble[moveIndex - 2].face].axis;

    assert.equal(currentAxis === previousAxis && previousAxis === secondPreviousAxis, false);
  }
});
