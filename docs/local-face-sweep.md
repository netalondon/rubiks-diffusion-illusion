# Local Face Sweep

This turns [`notebooks/rubiks_colab_face_sweep.ipynb`](../notebooks/rubiks_colab_face_sweep.ipynb) into a local script-driven experiment.

## How Progress Displays Locally

The terminal does **not** try to print images inline.

Instead, the local runner does two things:

- prints text progress in the terminal
- writes preview PNGs plus a `status.json` file under `output/local-view-count-sweep/live`

If you start the built-in viewer server, you can watch the latest previews in a browser at:

- `http://127.0.0.1:8765/viewer/index.html`

The viewer polls `live/status.json` every few seconds and refreshes:

- the selected training-view grid
- the current source-face sheet
- the latest solved-face contact sheet
- the latest scrambled-face contact sheet

That gives a notebook-like feedback loop, but through files and a browser instead of notebook cells.

## Local Prerequisites

You need:

- this repo
- a local checkout of the official Diffusion-Illusions repo
- a GPU-capable PyTorch install that matches your machine
- the Python packages in [`requirements-local-face-sweep.txt`](../requirements-local-face-sweep.txt)

PyTorch is intentionally **not** listed in `requirements-local-face-sweep.txt`, because the correct wheel depends on your machine and whether you want CUDA or CPU-only.

## Picking A Torch Install

There is no single perfect `torch` package that inspects your exact GPU and always picks the ideal build automatically.

In practice:

- `pip install torch torchvision torchaudio` is the simplest starting point
- on Linux with an NVIDIA GPU, that often installs a CUDA-enabled build and is usually worth trying first
- if you want to be explicit, install a specific CUDA wheel instead

The easiest way to decide is:

```bash
nvidia-smi
```

If that command works and shows an NVIDIA GPU, you should install a CUDA-enabled PyTorch build.

### For This Machine

For the current local machine, `nvidia-smi` showed:

- NVIDIA driver `581.60`
- CUDA version `13.0`
- GPU `NVIDIA RTX 500 Ada Generation`

PyTorch's current official Linux `pip` installer offers CUDA `11.8`, `12.6`, and `12.8` wheels. For this machine, the best explicit choice is:

```bash
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

If you prefer to try the general command first, this is also reasonable:

```bash
python3 -m pip install torch torchvision torchaudio
```

Then verify what you got:

```bash
python3 - <<'PY'
import torch
print(torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
PY
```

You want:

- `cuda available: True`
- your NVIDIA GPU name in the `device:` line

If `torch.cuda.is_available()` is `False`, reinstall using the explicit `cu128` command above.

### CPU-Only Fallback

If you do not have an NVIDIA GPU, you can install a CPU-only build:

```bash
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

That is fine for basic imports and small checks, but the actual face sweep will be extremely slow on CPU.

Suggested setup:

```bash
cd /home/netalondon/projects
git clone https://github.com/RyannDaGreat/Diffusion-Illusions.git

cd /home/netalondon/projects/rubiks-diffusion-illusion
python3 -m venv .venv
source .venv/bin/activate

# install a torch build that matches your machine first
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
python3 -m pip install -r requirements-local-face-sweep.txt
```

## Run The Sweep

```bash
cd /home/netalondon/projects/rubiks-diffusion-illusion
source .venv/bin/activate

python3 scripts/run_local_face_sweep.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions
```

Useful variants:

```bash
# run just one count while testing the setup
python3 scripts/run_local_face_sweep.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --view-counts 3

# preview more often
python3 scripts/run_local_face_sweep.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --display-interval 10

# keep the viewer off if you only want file output
python3 scripts/run_local_face_sweep.py run \
  --official-repo-dir /home/netalondon/projects/Diffusion-Illusions \
  --no-serve-viewer
```

## Output Layout

Shared sweep output:

- `output/local-view-count-sweep/sweep-summary.json`
- `output/local-view-count-sweep/live/status.json`
- `output/local-view-count-sweep/live/*.png`
- `output/local-view-count-sweep/viewer/index.html`

Per-run output:

- `output/local-runs/<timestamp>-local-view-sweep-<count>/metadata.json`
- `output/local-runs/<timestamp>-local-view-sweep-<count>/previews/*.png`
- `output/local-runs/<timestamp>-local-view-sweep-<count>/results/...`

Stable final outputs by count:

- `output/local-view-count-sweep/<count>-views/source-faces/*.png`
- `output/local-view-count-sweep/<count>-views/rendered/solved/*.png`
- `output/local-view-count-sweep/<count>-views/rendered/scrambled/*.png`

## Viewer Only

If you already have a sweep root on disk and just want to inspect it again:

```bash
python3 scripts/run_local_face_sweep.py serve
```

Or point it at a custom root:

```bash
python3 scripts/run_local_face_sweep.py serve \
  --sweep-root /some/other/output/local-view-count-sweep \
  --port 8765
```
