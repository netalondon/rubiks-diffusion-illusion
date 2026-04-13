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
Each sticker also has a dark `TOP` bar and a small corner marker. Those show the sticker's original upright direction before any scramble rotation.

Each cell is formatted like:

```text
F[2,1] r3
```

Meaning:

- the tile comes from source face `F`
- it started at row `2`, column `1` inside that face image
- it must be rotated by `3` quarter-turns clockwise when shown in its new position

When using `?art=debug`, you can read that rotation visually:

- `r0`: the `TOP` bar is still at the top
- `r1`: the `TOP` bar moved to the right
- `r2`: the `TOP` bar moved to the bottom
- `r3`: the `TOP` bar moved to the left

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

## Step 2

The next file to generate is a machine-readable arrangement spec:

```bash
npm run export:rubiks-illusion-spec
```

That writes:

```text
public/generated/rubiks-illusion-spec.json
```

This is the handoff file for Python or Colab. It contains:

- the six prime image ids (`U`, `D`, `L`, `R`, `F`, `B`)
- the solved arrangement
- the scrambled arrangement
- for every derived cell: source face, source row, source column, and quarter-turn rotation

Once that file exists, the next coding task is much smaller: "read this JSON in Python and recreate the same derived faces".

## Step 3

Set up the tiny Python bridge once:

```bash
npm run setup:python-bridge
```

Then render the solved and scrambled derived faces from the current source images:

```bash
npm run render:rubiks-illusion-spec
```

That writes:

```text
output/python/rubiks-illusion-render/solved
output/python/rubiks-illusion-render/scrambled
```

Each folder contains:

- six reconstructed face PNGs (`U.png`, `D.png`, `L.png`, `R.png`, `F.png`, `B.png`)
- one `contact-sheet.png`

At that point we have proved the same arrangement operator works outside the browser app.

## Step 4

The reusable Python operator now lives in:

```text
python_bridge/rubiks_illusion_operator.py
```

This is the file we should plan to import in Colab.

The important shape is:

```python
from python_bridge.rubiks_illusion_operator import render_all_arrangements

rendered = render_all_arrangements(spec, source_faces)
solved_faces = rendered["solved"]
scrambled_faces = rendered["scrambled"]
```

Where:

- `spec` is the parsed JSON from `public/generated/rubiks-illusion-spec.json`
- `source_faces` is an in-memory dict like `{"U": pil_image_u, ..., "B": pil_image_b}`

That means Colab will not need to know anything about cube moves or 3D logic.
It will only need to optimize six source images and call this operator.

The first notebook for this flow lives at:

```text
notebooks/rubiks_colab_bootstrap.ipynb
```

It is intentionally small and only bootstraps the runtime, imports the operator, and renders solved/scrambled faces.

The next learning notebook lives at:

```text
notebooks/rubiks_colab_optimization_sandbox.ipynb
```

It stays one step before diffusion: low resolution, toy targets, a differentiable torch version of the same Rubik's arrangement operator, and a small comparison between baseline optimization, stronger smoothness regularization, and an anchor-to-initialization penalty.

The first diffusion-facing notebook lives at:

```text
notebooks/rubiks_colab_diffusion_smoke_test.ipynb
```

It started as the first smoke test bridge into the official Diffusion Illusions code, and now also contains the smoother single-view variant: smooth raster source faces, explicit regularization, one primary target view (`solved:F`), and an export zip cell for getting results back out of Colab.

The next diffusion notebook for comparing light multi-view pressure lives at:

```text
notebooks/rubiks_colab_diffusion_multiview_probe.ipynb
```

It keeps the smoother raster setup, now includes switchable presets for lighter-vs-equal weighting and geometric-vs-semantic prompts, writes outputs to per-experiment folders, saves timestamped run snapshots under `output/colab-runs`, and includes the same export-archive cell so one Colab run produces both new results and a downloadable bundle.
