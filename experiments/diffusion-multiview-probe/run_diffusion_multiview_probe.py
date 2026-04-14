from __future__ import annotations

import argparse
import gc
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from python_bridge.live_preview import (
    append_history_entry,
    optional_viewer_server,
    reset_live_history,
    save_labeled_image_grid,
    write_json,
    write_live_viewer,
)

DEFAULT_SPEC_PATH = REPO_ROOT / "public" / "generated" / "rubiks-illusion-spec.json"
DEFAULT_SOURCE_DIR = REPO_ROOT / "src" / "assets" / "face-art"
DEFAULT_OFFICIAL_REPO_DIR = REPO_ROOT.parent / "Diffusion-Illusions"
DEFAULT_PROBE_ROOT = REPO_ROOT / "output" / "local-diffusion-multiview-probe"
DEFAULT_RUNS_ROOT = REPO_ROOT / "output" / "local-runs"
LIVE_DIR_NAME = "live"
VIEWER_DIR_NAME = "viewer"
VIEWER_TITLE = "Rubik Diffusion Multiview Probe"
VIEWER_SUBTITLE = "Live status on top, notebook-style preview history below."
DEFAULT_NEGATIVE_PROMPT = (
    "blurry, noisy, muddy colors, text, watermark, low quality, collage, multiple animals, cropped face"
)

EXPERIMENTS: dict[str, dict[str, Any]] = {
    "geometric_light": {
        "description": (
            "Keep the original circle-vs-stripes setup, but keep the scrambled view lighter "
            "so we can preserve the main solved structure."
        ),
        "views": [
            {
                "name": "solved:F",
                "arrangement": "solved",
                "face": "F",
                "prompt": "a minimal graphic poster of a centered soft pink circle on a warm cream background",
                "weight": 1.0,
            },
            {
                "name": "scrambled:U",
                "arrangement": "scrambled",
                "face": "U",
                "prompt": "a minimal graphic poster with diagonal purple stripes on a pale cream background",
                "weight": 0.35,
            },
        ],
    },
    "geometric_equal": {
        "description": "Give the circle and stripes equal pressure to compare the two-view balance directly.",
        "views": [
            {
                "name": "solved:F",
                "arrangement": "solved",
                "face": "F",
                "prompt": "a minimal graphic poster of a centered soft pink circle on a warm cream background",
                "weight": 1.0,
            },
            {
                "name": "scrambled:U",
                "arrangement": "scrambled",
                "face": "U",
                "prompt": "a minimal graphic poster with diagonal purple stripes on a pale cream background",
                "weight": 1.0,
            },
        ],
    },
    "animals_equal": {
        "description": (
            "Try a more semantic solved-plus-scrambled pair where the scrambled target "
            "contains three stickers from the solved face."
        ),
        "views": [
            {
                "name": "solved:R",
                "arrangement": "solved",
                "face": "R",
                "prompt": "a drawing of a cat",
                "weight": 1.0,
            },
            {
                "name": "scrambled:U",
                "arrangement": "scrambled",
                "face": "U",
                "prompt": "a drawing of a dog",
                "weight": 1.0,
            },
        ],
    },
}

PARAMETERIZATION_DEFAULTS: dict[str, dict[str, Any]] = {
    "official_fourier": {
        "learnable_size": 128,
        "fourier_hidden_dim": 128,
        "fourier_num_features": 128,
        "fourier_scale": 10.0,
        "num_iter": 5000,
        "display_interval": 200,
        "learning_rate": 1e-4,
        "guidance_scale": 100.0,
        "noise_coef": 0.10,
        "tv_coef": 0.0,
        "anchor_coef": 0.0,
        "optimizer_name": "SGD",
        "min_step": 10,
        "max_step": 990,
    },
    "smooth_raster": {
        "learnable_size": 96,
        "num_iter": 325,
        "display_interval": 25,
        "learning_rate": 8e-3,
        "guidance_scale": 80.0,
        "noise_coef": 0.11,
        "tv_coef": 0.08,
        "anchor_coef": 0.005,
        "optimizer_name": "Adam",
        "min_step": 20,
        "max_step": 980,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Rubik diffusion multiview probe with file-based previews."
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run one multiview probe and write preview images for a browser viewer.")
    run_parser.add_argument("--experiment", choices=sorted(EXPERIMENTS), default="animals_equal", help="Which experiment preset to run.")
    run_parser.add_argument("--parameterization-mode", choices=sorted(PARAMETERIZATION_DEFAULTS), default="official_fourier")
    run_parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH), help="Path to rubiks-illusion-spec.json.")
    run_parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory with source face PNGs.")
    run_parser.add_argument(
        "--official-repo-dir",
        default=str(DEFAULT_OFFICIAL_REPO_DIR),
        help="Checkout of the official Diffusion-Illusions repo.",
    )
    run_parser.add_argument(
        "--probe-root",
        default=str(DEFAULT_PROBE_ROOT),
        help="Directory for shared probe outputs, live viewer assets, and summary JSON.",
    )
    run_parser.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help="Directory for timestamped per-run output folders.",
    )
    run_parser.add_argument(
        "--model-name",
        default="runwayml/stable-diffusion-v1-5",
        help="Stable Diffusion checkpoint name.",
    )
    run_parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE_PROMPT, help="Negative prompt.")
    run_parser.add_argument("--num-iter", type=int, default=None, help="Training iterations for this run.")
    run_parser.add_argument("--display-interval", type=int, default=None, help="Preview interval in iterations.")
    run_parser.add_argument(
        "--progress-interval",
        type=int,
        default=5,
        help="How often to refresh the terminal iteration line.",
    )
    run_parser.add_argument("--learnable-size", type=int, default=None, help="Size of each learnable source face.")
    run_parser.add_argument("--fourier-hidden-dim", type=int, default=None, help="Hidden dim for LearnableImageFourier.")
    run_parser.add_argument("--fourier-num-features", type=int, default=None, help="Fourier feature count.")
    run_parser.add_argument("--fourier-scale", type=float, default=None, help="Fourier scale.")
    run_parser.add_argument("--learning-rate", type=float, default=None, help="Optimizer learning rate.")
    run_parser.add_argument("--guidance-scale", type=float, default=None, help="Stable Diffusion guidance scale.")
    run_parser.add_argument("--noise-coef", type=float, default=None, help="SDS noise coefficient.")
    run_parser.add_argument("--tv-coef", type=float, default=None, help="Total variation regularizer coefficient.")
    run_parser.add_argument("--anchor-coef", type=float, default=None, help="Anchor regularizer coefficient.")
    run_parser.add_argument("--min-step", type=int, default=None, help="Stable Diffusion min step.")
    run_parser.add_argument("--max-step", type=int, default=None, help="Stable Diffusion max step.")
    run_parser.add_argument(
        "--serve-viewer",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Serve the live viewer while training.",
    )
    run_parser.add_argument("--viewer-host", default="127.0.0.1", help="Host for the live viewer HTTP server.")
    run_parser.add_argument("--viewer-port", type=int, default=8766, help="Port for the live viewer HTTP server.")
    run_parser.add_argument(
        "--open-viewer",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Open the browser viewer automatically when the server starts.",
    )
    run_parser.add_argument(
        "--allow-cpu",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Allow running on CPU even though it is typically impractical.",
    )

    serve_parser = subparsers.add_parser("serve", help="Serve an existing probe root so the viewer page can poll it.")
    serve_parser.add_argument(
        "--probe-root",
        default=str(DEFAULT_PROBE_ROOT),
        help="Directory containing the viewer and live preview files.",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host.")
    serve_parser.add_argument("--port", type=int, default=8766, help="HTTP bind port.")
    serve_parser.add_argument(
        "--open-viewer",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Open the viewer URL in a browser.",
    )

    args = parser.parse_args()
    if not args.command:
        args.command = "run"
    return args


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_hyperparameters(args: argparse.Namespace) -> dict[str, Any]:
    defaults = dict(PARAMETERIZATION_DEFAULTS[args.parameterization_mode])
    overrides = {
        "learnable_size": args.learnable_size,
        "fourier_hidden_dim": args.fourier_hidden_dim,
        "fourier_num_features": args.fourier_num_features,
        "fourier_scale": args.fourier_scale,
        "num_iter": args.num_iter,
        "display_interval": args.display_interval,
        "learning_rate": args.learning_rate,
        "guidance_scale": args.guidance_scale,
        "noise_coef": args.noise_coef,
        "tv_coef": args.tv_coef,
        "anchor_coef": args.anchor_coef,
        "min_step": args.min_step,
        "max_step": args.max_step,
    }
    for key, value in overrides.items():
        if value is not None:
            defaults[key] = value
    return defaults


def write_live_status(
    live_dir: Path,
    *,
    phase: str,
    message: str,
    experiment_name: str,
    selected_views: list[str],
    run_root: Path | None,
    current_iteration: int | None = None,
    total_iterations: int | None = None,
    training_preview: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "viewer_title": VIEWER_TITLE,
        "viewer_subtitle": VIEWER_SUBTITLE,
        "view_count_label": "Train Views",
        "timeline_helper": "Each preview row is appended below the previous one, like the notebook.",
        "phase": phase,
        "message": message,
        "experiment_name": experiment_name,
        "selected_views": selected_views,
        "updated_at_utc": utc_timestamp(),
        "current_view_count": len(selected_views),
        "current_iteration": current_iteration,
        "total_iterations": total_iterations,
        "run_root": str(run_root) if run_root else None,
        "training_preview": training_preview,
    }
    if extra:
        payload.update(extra)
    write_json(live_dir / "status.json", payload)


def import_runtime_modules(repo_root: Path, official_repo_dir: Path) -> dict[str, Any]:
    if not official_repo_dir.exists():
        raise FileNotFoundError(
            "Missing Diffusion-Illusions checkout at "
            f"{official_repo_dir}. Clone it first with:\n"
            f"  git clone https://github.com/RyannDaGreat/Diffusion-Illusions.git {official_repo_dir}"
        )

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if str(official_repo_dir) not in sys.path:
        sys.path.insert(0, str(official_repo_dir))

    try:
        import rp
        import torch
        import torch.nn as nn
        from python_bridge import (
            batch_to_pil_face_dict,
            clone_rendered_to_cpu,
            load_source_faces,
            load_spec,
            render_all_arrangements_torch,
            save_rendered_faces,
            tensor_to_pil,
        )
        from source.learnable_textures import LearnableImageFourier
        from source.stable_diffusion import StableDiffusion
        from source.stable_diffusion_labels import NegativeLabel
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(
            f"Missing runtime dependency: {error.name}. "
            "Install the local diffusion probe dependencies first."
        ) from error

    return {
        "rp": rp,
        "torch": torch,
        "nn": nn,
        "batch_to_pil_face_dict": batch_to_pil_face_dict,
        "clone_rendered_to_cpu": clone_rendered_to_cpu,
        "load_source_faces": load_source_faces,
        "load_spec": load_spec,
        "render_all_arrangements_torch": render_all_arrangements_torch,
        "save_rendered_faces": save_rendered_faces,
        "tensor_to_pil": tensor_to_pil,
        "LearnableImageFourier": LearnableImageFourier,
        "StableDiffusion": StableDiffusion,
        "NegativeLabel": NegativeLabel,
    }


def build_train_views(experiment_config: dict[str, Any], negative_prompt: str, negative_label_cls: type[Any]) -> list[dict[str, Any]]:
    train_views: list[dict[str, Any]] = []
    for view_config in experiment_config["views"]:
        train_view = dict(view_config)
        train_view["label"] = negative_label_cls(train_view["prompt"], negative_prompt)
        train_views.append(train_view)
    return train_views


def make_run_dirs(experiment_slug: str, *, probe_root: Path, runs_root: Path) -> tuple[Path, Path]:
    output_root = probe_root / experiment_slug
    run_root = runs_root / f"{utc_timestamp()}-local-diffusion-multiview-probe-{experiment_slug}"
    return output_root, run_root


def write_preview_images(
    *,
    live_dir: Path,
    run_root: Path,
    current_iteration: int,
    experiment_name: str,
    rendered_cpu: dict[str, dict[str, Any]],
    train_views: list[dict[str, Any]],
    tensor_to_pil: Any,
) -> dict[str, str]:
    preview_dir = run_root / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    history_dir = live_dir / "history" / run_root.name
    history_dir.mkdir(parents=True, exist_ok=True)

    training_items = [
        (view["name"], tensor_to_pil(rendered_cpu[view["arrangement"]][view["face"]]))
        for view in train_views
    ]
    training_snapshot = preview_dir / f"iter-{current_iteration:05d}-training-views.png"
    history_training = history_dir / f"iter-{current_iteration:05d}-training-views.png"

    save_labeled_image_grid(
        training_items,
        training_snapshot,
        title=f"{experiment_name} preview at iter {current_iteration}",
        max_cols=3,
    )
    shutil.copy2(training_snapshot, history_training)

    live_training = live_dir / "training-preview.png"
    shutil.copy2(training_snapshot, live_training)

    return {
        "training_preview": live_training.name,
        "history_training_preview": relative_to_root(history_training, live_dir),
    }


def cleanup_after_run(torch_module: Any) -> None:
    gc.collect()
    if torch_module.cuda.is_available():
        torch_module.cuda.empty_cache()
        torch_module.cuda.ipc_collect()


def update_progress_line(experiment_name: str, current_iteration: int, total_iterations: int, sampled_views: list[str]) -> None:
    sampled = ",".join(sampled_views) if sampled_views else "-"
    message = f"\r[{experiment_name}] iter {current_iteration}/{total_iterations} | sampled={sampled}"
    sys.stdout.write(message.ljust(120))
    sys.stdout.flush()


def clear_progress_line() -> None:
    sys.stdout.write("\r" + (" " * 140) + "\r")
    sys.stdout.flush()


def run_experiment(args: argparse.Namespace) -> None:
    spec_path = Path(args.spec).resolve()
    source_dir = Path(args.source_dir).resolve()
    official_repo_dir = Path(args.official_repo_dir).resolve()
    probe_root = Path(args.probe_root).resolve()
    runs_root = Path(args.runs_root).resolve()
    live_dir = probe_root / LIVE_DIR_NAME
    experiment_name = args.experiment
    experiment_slug = experiment_name.replace("_", "-")
    experiment_config = EXPERIMENTS[experiment_name]
    hyperparameters = resolve_hyperparameters(args)
    probe_summary_path = probe_root / "probe-summary.json"

    probe_root.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    live_dir.mkdir(parents=True, exist_ok=True)
    write_live_viewer(probe_root / VIEWER_DIR_NAME / "index.html")
    reset_live_history(live_dir)

    write_live_status(
        live_dir,
        phase="starting",
        message="Preparing the local diffusion multiview probe.",
        experiment_name=experiment_name,
        selected_views=[],
        run_root=None,
        extra={
            "parameterization_mode": args.parameterization_mode,
            "description": experiment_config["description"],
        },
    )

    runtime = import_runtime_modules(REPO_ROOT, official_repo_dir)
    rp = runtime["rp"]
    torch = runtime["torch"]
    nn = runtime["nn"]
    batch_to_pil_face_dict = runtime["batch_to_pil_face_dict"]
    clone_rendered_to_cpu = runtime["clone_rendered_to_cpu"]
    load_source_faces = runtime["load_source_faces"]
    load_spec = runtime["load_spec"]
    render_all_arrangements_torch = runtime["render_all_arrangements_torch"]
    save_rendered_faces = runtime["save_rendered_faces"]
    tensor_to_pil = runtime["tensor_to_pil"]
    LearnableImageFourier = runtime["LearnableImageFourier"]
    StableDiffusion = runtime["StableDiffusion"]
    NegativeLabel = runtime["NegativeLabel"]

    spec = load_spec(spec_path)
    face_order = list(spec["primeImages"])
    face_to_index = {face_id: index for index, face_id in enumerate(face_order)}

    device = rp.select_torch_device()
    if str(device) == "cpu" and not args.allow_cpu:
        raise RuntimeError(
            "The local diffusion multiview probe needs a GPU for practical use. "
            "Re-run with --allow-cpu only if you really want a CPU attempt."
        )

    print("Stable Diffusion device:", device)
    print("Probe root:", probe_root)
    print("Run root base:", runs_root)
    print("Experiment:", experiment_name)
    print("Description:", experiment_config["description"])
    print("Parameterization mode:", args.parameterization_mode)

    load_source_faces(source_dir, face_order)
    stable_diffusion = StableDiffusion(device, args.model_name)
    stable_diffusion.max_step = hyperparameters["max_step"]
    stable_diffusion.min_step = hyperparameters["min_step"]
    train_views = build_train_views(experiment_config, args.negative_prompt, NegativeLabel)
    selected_view_names = [view["name"] for view in train_views]

    output_root, run_root = make_run_dirs(experiment_slug, probe_root=probe_root, runs_root=runs_root)
    output_root.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(parents=True, exist_ok=True)

    summary_payload: dict[str, Any] = {"results": []}
    if probe_summary_path.exists():
        import json

        summary_payload = json.loads(probe_summary_path.read_text(encoding="utf8"))

    class RubiksLearnableSourceFacesRaster(nn.Module):
        def __init__(
            self,
            face_ids: list[str],
            size: int,
            stable_diffusion_device: Any,
            base_rgb: tuple[float, float, float] = (0.92, 0.90, 0.84),
            noise_scale: float = 0.03,
        ):
            super().__init__()
            self.face_ids = list(face_ids)
            base = torch.tensor(base_rgb, device=stable_diffusion_device, dtype=torch.float32).view(1, 3, 1, 1)
            base = base.repeat(len(self.face_ids), 1, size, size)
            base = (base + noise_scale * torch.randn_like(base)).clamp(0.02, 0.98)
            self.initial_reference = base.detach().clone()
            self.logits = nn.Parameter(torch.logit(base))

        def forward(self) -> Any:
            return torch.sigmoid(self.logits)

    class RubiksLearnableSourceFacesFourier(nn.Module):
        def __init__(self, face_ids: list[str], size: int):
            super().__init__()
            self.face_ids = list(face_ids)
            self.initial_reference = None
            self.learnable_images = nn.ModuleList(
                [
                    LearnableImageFourier(
                        height=size,
                        width=size,
                        hidden_dim=hyperparameters["fourier_hidden_dim"],
                        num_features=hyperparameters["fourier_num_features"],
                        scale=hyperparameters["fourier_scale"],
                    )
                    for _ in self.face_ids
                ]
            )

        def forward(self) -> Any:
            return torch.stack([image() for image in self.learnable_images])

    def total_variation_loss(batch: Any) -> Any:
        vertical = (batch[:, :, 1:, :] - batch[:, :, :-1, :]).abs().mean()
        horizontal = (batch[:, :, :, 1:] - batch[:, :, :, :-1]).abs().mean()
        return vertical + horizontal

    def anchor_loss(batch: Any, reference: Any) -> Any:
        return (batch - reference).pow(2).mean()

    try:
        with optional_viewer_server(
            probe_root,
            host=args.viewer_host,
            port=args.viewer_port,
            enabled=args.serve_viewer,
            open_viewer=args.open_viewer,
            viewer_path=f"{VIEWER_DIR_NAME}/index.html",
        ):
            append_history_entry(
                live_dir,
                {
                    "entry_type": "run_start",
                    "title": f"Starting {experiment_name}",
                    "message": experiment_config["description"],
                    "selected_views": selected_view_names,
                    "current_view_count": len(selected_view_names),
                    "updated_at_utc": utc_timestamp(),
                },
            )
            write_live_status(
                live_dir,
                phase="running",
                message=f"Starting {experiment_name}.",
                experiment_name=experiment_name,
                selected_views=selected_view_names,
                run_root=run_root,
                total_iterations=hyperparameters["num_iter"],
                extra={
                    "parameterization_mode": args.parameterization_mode,
                    "description": experiment_config["description"],
                },
            )

            if args.parameterization_mode == "official_fourier":
                learnable_faces = RubiksLearnableSourceFacesFourier(
                    face_order,
                    hyperparameters["learnable_size"],
                ).to(device)
                optimizer = torch.optim.SGD(learnable_faces.parameters(), lr=hyperparameters["learning_rate"])
            else:
                learnable_faces = RubiksLearnableSourceFacesRaster(
                    face_order,
                    hyperparameters["learnable_size"],
                    device,
                ).to(device)
                optimizer = torch.optim.Adam(learnable_faces.parameters(), lr=hyperparameters["learning_rate"])

            def get_current_state() -> tuple[Any, dict[str, dict[str, Any]]]:
                current_source_batch = learnable_faces()
                current_rendered = render_all_arrangements_torch(spec, current_source_batch, face_to_index)
                return current_source_batch, current_rendered

            start_time = time.time()
            progress_interval = max(1, args.progress_interval)
            display_interval = max(1, hyperparameters["display_interval"])
            last_sampled_names: list[str] = []

            _, initial_rendered = get_current_state()
            initial_rendered_cpu = clone_rendered_to_cpu(initial_rendered)
            preview_paths = write_preview_images(
                live_dir=live_dir,
                run_root=run_root,
                current_iteration=0,
                experiment_name=experiment_name,
                rendered_cpu=initial_rendered_cpu,
                train_views=train_views,
                tensor_to_pil=tensor_to_pil,
            )
            write_live_status(
                live_dir,
                phase="running",
                message=f"Initial preview ready for {experiment_name}.",
                experiment_name=experiment_name,
                selected_views=selected_view_names,
                run_root=run_root,
                current_iteration=0,
                total_iterations=hyperparameters["num_iter"],
                training_preview=preview_paths["training_preview"],
                extra={
                    "parameterization_mode": args.parameterization_mode,
                    "description": experiment_config["description"],
                },
            )
            append_history_entry(
                live_dir,
                {
                    "entry_type": "preview",
                    "title": f"{experiment_name} · initial preview",
                    "message": "Initial preview before optimization.",
                    "selected_views": selected_view_names,
                    "current_view_count": len(selected_view_names),
                    "current_iteration": 0,
                    "total_iterations": hyperparameters["num_iter"],
                    "updated_at_utc": utc_timestamp(),
                    "training_preview": preview_paths["history_training_preview"],
                    "last_sampled_views": [],
                },
            )

            for iter_num in range(hyperparameters["num_iter"]):
                optimizer.zero_grad(set_to_none=True)
                current_source_batch, current_rendered = get_current_state()

                sampled_views = list(rp.random_batch(train_views, batch_size=1))
                last_sampled_names = [view["name"] for view in sampled_views]
                for view in sampled_views:
                    current_view = current_rendered[view["arrangement"]][view["face"]][None]
                    stable_diffusion.train_step(
                        view["label"].embedding,
                        current_view,
                        noise_coef=hyperparameters["noise_coef"] * view["weight"],
                        guidance_scale=hyperparameters["guidance_scale"],
                    )

                tv_value = torch.zeros((), device=device)
                anchor_value = torch.zeros((), device=device)
                regularizer_loss = torch.zeros((), device=device)

                if hyperparameters["tv_coef"] > 0:
                    tv_value = total_variation_loss(current_source_batch)
                    regularizer_loss = regularizer_loss + hyperparameters["tv_coef"] * tv_value

                if hyperparameters["anchor_coef"] > 0 and getattr(learnable_faces, "initial_reference", None) is not None:
                    anchor_value = anchor_loss(current_source_batch, learnable_faces.initial_reference)
                    regularizer_loss = regularizer_loss + hyperparameters["anchor_coef"] * anchor_value

                if regularizer_loss.requires_grad:
                    regularizer_loss.backward()

                optimizer.step()

                current_iteration = iter_num + 1
                if current_iteration == 1 or current_iteration % progress_interval == 0 or current_iteration == hyperparameters["num_iter"]:
                    update_progress_line(experiment_name, current_iteration, hyperparameters["num_iter"], last_sampled_names)

                if current_iteration % display_interval == 0 or iter_num == 0:
                    clear_progress_line()
                    print(
                        f"Saved preview at iteration {current_iteration}/{hyperparameters['num_iter']} "
                        f"| sampled={last_sampled_names} | tv={tv_value.item():.4f} | anchor={anchor_value.item():.4f}"
                    )
                    _, preview_rendered = get_current_state()
                    preview_rendered_cpu = clone_rendered_to_cpu(preview_rendered)
                    preview_paths = write_preview_images(
                        live_dir=live_dir,
                        run_root=run_root,
                        current_iteration=current_iteration,
                        experiment_name=experiment_name,
                        rendered_cpu=preview_rendered_cpu,
                        train_views=train_views,
                        tensor_to_pil=tensor_to_pil,
                    )
                    write_live_status(
                        live_dir,
                        phase="running",
                        message=f"{experiment_name} preview at iteration {current_iteration}.",
                        experiment_name=experiment_name,
                        selected_views=selected_view_names,
                        run_root=run_root,
                        current_iteration=current_iteration,
                        total_iterations=hyperparameters["num_iter"],
                        training_preview=preview_paths["training_preview"],
                        extra={
                            "parameterization_mode": args.parameterization_mode,
                            "description": experiment_config["description"],
                            "last_sampled_views": last_sampled_names,
                        },
                    )
                    append_history_entry(
                        live_dir,
                        {
                            "entry_type": "preview",
                            "title": f"{experiment_name} · iter {current_iteration}",
                            "message": f"Preview at iteration {current_iteration}.",
                            "selected_views": selected_view_names,
                            "current_view_count": len(selected_view_names),
                            "current_iteration": current_iteration,
                            "total_iterations": hyperparameters["num_iter"],
                            "updated_at_utc": utc_timestamp(),
                            "training_preview": preview_paths["history_training_preview"],
                            "last_sampled_views": last_sampled_names,
                        },
                    )
                    update_progress_line(experiment_name, current_iteration, hyperparameters["num_iter"], last_sampled_names)

            final_source_batch, final_rendered = get_current_state()
            clear_progress_line()
            final_source_faces = batch_to_pil_face_dict(final_source_batch.detach().cpu(), face_order)
            final_rendered_cpu = clone_rendered_to_cpu(final_rendered)
            preview_paths = write_preview_images(
                live_dir=live_dir,
                run_root=run_root,
                current_iteration=hyperparameters["num_iter"],
                experiment_name=experiment_name,
                rendered_cpu=final_rendered_cpu,
                train_views=train_views,
                tensor_to_pil=tensor_to_pil,
            )

            source_output_dir = output_root / "source-faces"
            render_output_dir = output_root / "rendered"
            run_source_dir = run_root / "results" / "source-faces"
            run_render_dir = run_root / "results" / "rendered"
            for directory in [source_output_dir, render_output_dir, run_source_dir, run_render_dir]:
                directory.mkdir(parents=True, exist_ok=True)

            for face_id, image in final_source_faces.items():
                image.save(source_output_dir / f"{face_id}.png")
                image.save(run_source_dir / f"{face_id}.png")

            save_rendered_faces(
                {face_id: tensor_to_pil(image) for face_id, image in final_rendered_cpu["solved"].items()},
                render_output_dir / "solved",
            )
            save_rendered_faces(
                {face_id: tensor_to_pil(image) for face_id, image in final_rendered_cpu["scrambled"].items()},
                render_output_dir / "scrambled",
            )
            save_rendered_faces(
                {face_id: tensor_to_pil(image) for face_id, image in final_rendered_cpu["solved"].items()},
                run_render_dir / "solved",
            )
            save_rendered_faces(
                {face_id: tensor_to_pil(image) for face_id, image in final_rendered_cpu["scrambled"].items()},
                run_render_dir / "scrambled",
            )

            shutil.copy2(
                REPO_ROOT / "experiments" / "diffusion-multiview-probe" / "rubiks_colab_diffusion_multiview_probe.ipynb",
                run_root / "notebook-source.ipynb",
            )
            shutil.copy2(Path(__file__).resolve(), run_root / "script-source.py")

            metadata = {
                "status": "success",
                "experiment": experiment_name,
                "description": experiment_config["description"],
                "timestamp_utc": utc_timestamp(),
                "model_name": args.model_name,
                "device": str(device),
                "parameterization_mode": args.parameterization_mode,
                "negative_prompt": args.negative_prompt,
                "train_views": [
                    {
                        "name": view["name"],
                        "arrangement": view["arrangement"],
                        "face": view["face"],
                        "prompt": view["prompt"],
                        "weight": view["weight"],
                    }
                    for view in train_views
                ],
                "hyperparameters": {
                    "num_iter": hyperparameters["num_iter"],
                    "display_interval": display_interval,
                    "learnable_size": hyperparameters["learnable_size"],
                    "fourier_hidden_dim": hyperparameters.get("fourier_hidden_dim"),
                    "fourier_num_features": hyperparameters.get("fourier_num_features"),
                    "fourier_scale": hyperparameters.get("fourier_scale"),
                    "learning_rate": hyperparameters["learning_rate"],
                    "optimizer_name": hyperparameters["optimizer_name"],
                    "guidance_scale": hyperparameters["guidance_scale"],
                    "noise_coef": hyperparameters["noise_coef"],
                    "tv_coef": hyperparameters["tv_coef"],
                    "anchor_coef": hyperparameters["anchor_coef"],
                    "min_step": stable_diffusion.min_step,
                    "max_step": stable_diffusion.max_step,
                },
                "elapsed_seconds": round(time.time() - start_time, 2),
                "last_sampled_views": last_sampled_names,
                "saved_paths": {
                    "canonical_output_root": str(output_root),
                    "source_output_dir": str(source_output_dir),
                    "render_output_dir": str(render_output_dir),
                    "run_root": str(run_root),
                    "metadata_path": str(run_root / "metadata.json"),
                    "preview_dir": str(run_root / "previews"),
                },
            }
            write_json(run_root / "metadata.json", metadata)
            summary_payload.setdefault("results", []).append(metadata)
            write_json(probe_summary_path, summary_payload)

            print(f"Completed {experiment_name} in {metadata['elapsed_seconds']:.1f}s")
            print("Saved run root:", run_root)

            write_live_status(
                live_dir,
                phase="completed",
                message=f"Completed {experiment_name} in {metadata['elapsed_seconds']:.1f}s.",
                experiment_name=experiment_name,
                selected_views=selected_view_names,
                run_root=run_root,
                current_iteration=hyperparameters["num_iter"],
                total_iterations=hyperparameters["num_iter"],
                training_preview=preview_paths["training_preview"],
                extra={
                    "parameterization_mode": args.parameterization_mode,
                    "description": experiment_config["description"],
                    "last_sampled_views": last_sampled_names,
                    "summary_path": relative_to_root(probe_summary_path, probe_root),
                },
            )
            append_history_entry(
                live_dir,
                {
                    "entry_type": "run_complete",
                    "title": f"Completed {experiment_name}",
                    "message": f"Finished in {metadata['elapsed_seconds']:.1f}s.",
                    "selected_views": selected_view_names,
                    "current_view_count": len(selected_view_names),
                    "updated_at_utc": utc_timestamp(),
                },
            )
    except Exception as error:
        clear_progress_line()
        result = {
            "status": "failed",
            "experiment": experiment_name,
            "description": experiment_config["description"],
            "timestamp_utc": utc_timestamp(),
            "parameterization_mode": args.parameterization_mode,
            "selected_views": selected_view_names,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        summary_payload.setdefault("results", []).append(result)
        write_json(probe_summary_path, summary_payload)
        write_live_status(
            live_dir,
            phase="failed",
            message=f"Run failed for {experiment_name}: {type(error).__name__}: {error}",
            experiment_name=experiment_name,
            selected_views=selected_view_names,
            run_root=run_root if "run_root" in locals() else None,
            extra={
                "parameterization_mode": args.parameterization_mode,
                "description": experiment_config["description"],
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )
        append_history_entry(
            live_dir,
            {
                "entry_type": "run_failed",
                "title": f"Failed {experiment_name}",
                "message": f"{type(error).__name__}: {error}",
                "selected_views": selected_view_names,
                "current_view_count": len(selected_view_names),
                "updated_at_utc": utc_timestamp(),
            },
        )
        print(f"Run failed for {experiment_name}: {type(error).__name__}: {error}")
        raise
    finally:
        cleanup_after_run(torch)

    print("\nProbe finished. Summary saved to:", probe_summary_path)


def serve_existing_viewer(args: argparse.Namespace) -> None:
    probe_root = Path(args.probe_root).resolve()
    write_live_viewer(probe_root / VIEWER_DIR_NAME / "index.html")
    history_path = probe_root / LIVE_DIR_NAME / "history.json"
    if not history_path.exists():
        write_json(history_path, {"entries": []})
    with optional_viewer_server(
        probe_root,
        host=args.host,
        port=args.port,
        enabled=True,
        open_viewer=args.open_viewer,
        viewer_path=f"{VIEWER_DIR_NAME}/index.html",
    ):
        print("Press Ctrl+C to stop the viewer server.")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("\nStopped viewer server.")


def main() -> None:
    args = parse_args()
    if args.command == "serve":
        serve_existing_viewer(args)
        return
    run_experiment(args)


if __name__ == "__main__":
    main()
