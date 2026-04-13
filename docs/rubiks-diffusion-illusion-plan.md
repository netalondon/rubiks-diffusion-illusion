# Rubik's Cube Diffusion Illusion: Step 1

This repo already has the most important non-ML part:

- six prime images: [`src/assets/face-art/*.png`](../src/assets/face-art)
- a deterministic arrangement operator: the saved scramble in [`public/generated/non-adjacent-scramble.json`](../public/generated/non-adjacent-scramble.json)
- a renderer that applies tile permutations and tile rotations to the face images

That means your project fits the paper's general setup:

- prime images: the six face images (`U`, `D`, `L`, `R`, `F`, `B`)
- arrangement operator 1: identity, which gives the solved cube
- arrangement operator 2: the saved scramble, which gives the scrambled cube
- derived images: the six visible faces before the scramble and the six visible faces after the scramble

Before touching diffusion code, the first thing to understand is the exact tile mapping.

## What To Run

```bash
npm run inspect:saved-scramble
```

That prints a `3x3` summary for each visible face after the saved scramble.

For a visual check in the browser, run the app and open the local Vite URL with `?art=debug` appended:

```text
http://localhost:5173/?art=debug
```

That switches the cube from photo face art to generated debug tiles labeled like `F` and `2,1`.

Each cell is formatted like:

```text
F[2,1] r3
```

Meaning:

- the tile comes from source face `F`
- it started at row `2`, column `1` inside that face image
- it must be rotated by `3` quarter-turns clockwise when shown in its new position

## Why This Matters

This is the exact custom arrangement operator you will eventually need inside a Colab notebook.

Once we can describe the scramble as "take this tile from this face, rotate it like this, paste it here", we can do the same operation in PyTorch and optimize the six source images against prompts for:

- the solved cube faces
- the scrambled cube faces

## Small Next Steps

1. Verify the printed mapping feels intuitive by comparing a few cells against the live app.
2. Create a no-AI baseline by manually designing six simple `3x3` label images and confirming the scramble rearranges them exactly as expected.
3. Recreate the same tile permutation in Python or Colab.
4. Only then plug a diffusion notebook into that custom operator.
