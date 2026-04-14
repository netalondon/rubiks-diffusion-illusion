# Local Diffusion Multiview Probe

This folder now has a maintained local runner alongside the archived notebook:
[`rubiks_colab_diffusion_multiview_probe.ipynb`](./rubiks_colab_diffusion_multiview_probe.ipynb).

The local script mirrors the notebook's core behavior:

- one named experiment preset per run
- periodic training-view preview snapshots
- a browser viewer backed by `live/status.json` and `live/history.json`
- canonical outputs plus a timestamped run snapshot on disk

## Install

This experiment uses the same Python stack as the local face sweep.

```bash
cd /home/netalondon/projects/rubiks-diffusion-illusion
python3 -m venv .venv
source .venv/bin/activate

# install a torch build that matches your machine first
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
python3 -m pip install -r experiments/diffusion-multiview-probe/requirements.txt
```

## Run

```bash
cd /home/netalondon/projects/rubiks-diffusion-illusion
source .venv/bin/activate

python3 experiments/diffusion-multiview-probe/run_diffusion_multiview_probe.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions
```

Useful variants:

```bash
# choose a different preset from the notebook
python3 experiments/diffusion-multiview-probe/run_diffusion_multiview_probe.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --experiment geometric_equal

# use the raster parameterization instead of the official-like Fourier one
python3 experiments/diffusion-multiview-probe/run_diffusion_multiview_probe.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --parameterization-mode smooth_raster

# keep the viewer off if you only want file output
python3 experiments/diffusion-multiview-probe/run_diffusion_multiview_probe.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --no-serve-viewer
```

If you start the built-in viewer server, it serves:

- `http://127.0.0.1:8766/viewer/index.html`

## Output Layout

Shared probe output:

- `output/local-diffusion-multiview-probe/probe-summary.json`
- `output/local-diffusion-multiview-probe/live/status.json`
- `output/local-diffusion-multiview-probe/live/history.json`
- `output/local-diffusion-multiview-probe/live/training-preview.png`
- `output/local-diffusion-multiview-probe/viewer/index.html`

Per-run output:

- `output/local-runs/<timestamp>-local-diffusion-multiview-probe-<experiment>/metadata.json`
- `output/local-runs/<timestamp>-local-diffusion-multiview-probe-<experiment>/previews/*.png`
- `output/local-runs/<timestamp>-local-diffusion-multiview-probe-<experiment>/results/...`

Stable final outputs by experiment:

- `output/local-diffusion-multiview-probe/<experiment>/source-faces/*.png`
- `output/local-diffusion-multiview-probe/<experiment>/rendered/solved/*.png`
- `output/local-diffusion-multiview-probe/<experiment>/rendered/scrambled/*.png`

## Viewer Only

If you already have a probe root on disk and just want to inspect it again:

```bash
python3 experiments/diffusion-multiview-probe/run_diffusion_multiview_probe.py serve
```
