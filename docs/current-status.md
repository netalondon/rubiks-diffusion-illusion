# Current Status

This file is the short handoff for a fresh Codex thread.

Use it together with:

- [`docs/rubiks-diffusion-illusion-plan.md`](./rubiks-diffusion-illusion-plan.md)
- [`public/generated/rubiks-illusion-spec.json`](../public/generated/rubiks-illusion-spec.json)
- [`python_bridge/rubiks_illusion_operator.py`](../python_bridge/rubiks_illusion_operator.py)
- [`python_bridge/rubiks_illusion_torch.py`](../python_bridge/rubiks_illusion_torch.py)

## Project Goal

Optimize the six Rubik's cube face images so that:

- solved faces read as one set of images
- scrambled faces read as another set of images

The Rubik-specific tile movement and rotation logic is already implemented and verified. The open problem is the diffusion optimization side.

## What Is Solid

- The browser app's scramble mapping is correct.
- `?art=debug` in the web app makes sticker provenance and rotation visible.
- The machine-readable arrangement export exists at `public/generated/rubiks-illusion-spec.json`.
- The Python PIL renderer reproduces the web app behavior.
- The differentiable torch renderer matches the PIL renderer closely enough for optimization experiments.
- The archived Colab/bootstrap notebooks still capture useful historical experiments, but the active workflow is now local-script driven.

## Best-Known Diffusion Setup

The current best practical setup for experimentation is:

- parameterization: `LearnableImageFourier`
- optimizer: `SGD`
- learnable size: `128x128`
- hidden dim: `128`
- Fourier features: `128`
- Fourier scale: `10`
- one sampled training view per iteration
- `guidance_scale = 100`
- `noise_coef = 0.10`
- `min_step = 10`
- `max_step = 990`
- no explicit TV regularization
- no anchor-to-initialization penalty

This is intentionally close to the official Diffusion Illusions notebooks, but reduced from `256` to `128` because the larger version ran out of memory in Colab for the Rubik setup.

## Why 128x128

The more official-looking `256x256`, `hidden_dim=256`, `num_features=256` setup caused CUDA out-of-memory errors in Colab when combined with:

- six learnable source faces
- Rubik arrangement rendering
- Stable Diffusion VAE encoding
- multiple target views

The reduced `128x128` configuration worked and produced noticeably better results than the earlier over-regularized smooth raster experiments.

## Archived Notebook Roles

- [`notebooks/archive/rubiks_colab_bootstrap.ipynb`](../notebooks/archive/rubiks_colab_bootstrap.ipynb)
  Runtime/bootstrap notebook. Use this to confirm the repo loads and the Rubik operator runs in Colab.

- [`notebooks/archive/rubiks_colab_optimization_sandbox.ipynb`](../notebooks/archive/rubiks_colab_optimization_sandbox.ipynb)
  Pre-diffusion notebook. Uses direct pixel optimization and toy targets to prove gradients flow through the Rubik operator.

- [`notebooks/archive/rubiks_colab_diffusion_smoke_test.ipynb`](../notebooks/archive/rubiks_colab_diffusion_smoke_test.ipynb)
  Small diffusion bridge notebook. Good for checking whether diffusion gradients affect Rubik-rendered outputs at all.

- [`notebooks/archive/rubiks_colab_diffusion_multiview_probe.ipynb`](../notebooks/archive/rubiks_colab_diffusion_multiview_probe.ipynb)
  Main interactive experiment notebook. This is where most prompt, weighting, and official-like setup comparisons happened.

- [`notebooks/archive/rubiks_colab_face_sweep.ipynb`](../notebooks/archive/rubiks_colab_face_sweep.ipynb)
  Hands-off overnight notebook. Starts from the proven `solved:R + scrambled:U` seed pair and sweeps from `3` to `12` target views.

The maintained experiment path is now the local runner documented in
[`docs/local-face-sweep.md`](./local-face-sweep.md).

## Official Repo Usage

We clone the official Diffusion Illusions repo to reuse:

- `source/stable_diffusion.py`
- `source/learnable_textures.py`
- `source/negative_label.py`
- the official notebook training pattern

We do **not** use the official geometry/operator logic. That part is replaced by this repo's Rubik-specific arrangement operator.

## What Worked

- The non-ML Rubik pipeline is solid end to end.
- Single-view diffusion runs can produce recognizable structure.
- Simpler semantic prompts worked better than some geometric toy prompts in the official-like Fourier regime.
- `solved:R` with `scrambled:U` is a good seed pair because scrambled `U` contains three stickers from prime face `R`.
- A sweep over individual target views is a better stress test than sweeping over paired face ids.

## What Did Not Work Well

- Strong smooth/anchor bias kept images too close to blank cream backgrounds.
- Equal-weight multi-view runs at larger official sizes hit memory limits.
- Fourier + SDS often produces the classic magenta/green textured shortcut behavior.
- Free-tier Colab GPU availability became a real blocker; at one point Colab explicitly refused GPU assignment due to usage limits.

## Current External Blockers

- Access to a stronger local or remote GPU machine is still the main blocker for the next full face sweep runs.

## Recommended Next Experiments

Once stronger compute is available, the recommended order is:

1. Run the local face sweep script and inspect `output/local-view-count-sweep/sweep-summary.json`.
2. Identify the highest view count that still produces coherent structure.
3. Re-run that stable count locally for closer qualitative inspection of saved previews and rendered outputs.
4. Only after that, tune prompts, view order, or weighting further.

## Working Tree Note

At the time this file was written, there were still local uncommitted edits in:

- `notebooks/archive/rubiks_colab_bootstrap.ipynb`
- `notebooks/archive/rubiks_colab_diffusion_multiview_probe.ipynb`

Those may reflect active experiments and should be reviewed before overwriting or cleaning them in a fresh thread.
