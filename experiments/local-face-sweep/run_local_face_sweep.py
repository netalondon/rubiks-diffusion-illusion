from __future__ import annotations

import argparse
import gc
import shutil
import sys
import time
import traceback
import webbrowser
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from python_bridge.local_face_sweep import (
    DEFAULT_NEGATIVE_PROMPT,
    DEFAULT_SCRAMBLED_PROMPT,
    DEFAULT_SOLVED_PROMPT,
    DEFAULT_VIEW_GROWTH_ORDER,
    append_history_entry,
    reset_live_history,
    save_labeled_image_grid,
    write_json,
    write_live_viewer,
)
from python_bridge.rubiks_illusion_operator import load_spec, save_contact_sheet

DEFAULT_SPEC_PATH = REPO_ROOT / "public" / "generated" / "rubiks-illusion-spec.json"
DEFAULT_SOURCE_DIR = REPO_ROOT / "src" / "assets" / "face-art"
DEFAULT_OFFICIAL_REPO_DIR = REPO_ROOT.parent / "Diffusion-Illusions"
DEFAULT_SWEEP_ROOT = REPO_ROOT / "output" / "local-view-count-sweep"
DEFAULT_RUNS_ROOT = REPO_ROOT / "output" / "local-runs"
LIVE_DIR_NAME = "live"
VIEWER_DIR_NAME = "viewer"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local Rubik + diffusion face-count sweep with file-based previews."
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the experiment and write preview images for a browser viewer.")
    run_parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH), help="Path to rubiks-illusion-spec.json.")
    run_parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Directory with source face PNGs.")
    run_parser.add_argument(
        "--official-repo-dir",
        default=str(DEFAULT_OFFICIAL_REPO_DIR),
        help="Checkout of the official Diffusion-Illusions repo.",
    )
    run_parser.add_argument(
        "--sweep-root",
        default=str(DEFAULT_SWEEP_ROOT),
        help="Directory for shared local sweep outputs, live viewer assets, and summary JSON.",
    )
    run_parser.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help="Directory for timestamped per-run output folders.",
    )
    run_parser.add_argument(
        "--view-counts",
        default="",
        help="Comma-separated list of view counts to run. Defaults to the archived face-sweep range.",
    )
    run_parser.add_argument("--iterations-per-view", type=int, default=1000, help="Training iterations per selected view.")
    run_parser.add_argument("--display-interval", type=int, default=50, help="Preview interval in iterations.")
    run_parser.add_argument(
        "--progress-interval",
        type=int,
        default=5,
        help="How often to refresh the terminal iteration line.",
    )
    run_parser.add_argument("--learnable-size", type=int, default=128, help="Size of each learnable source face.")
    run_parser.add_argument("--fourier-hidden-dim", type=int, default=128, help="Hidden dim for LearnableImageFourier.")
    run_parser.add_argument("--fourier-num-features", type=int, default=128, help="Fourier feature count.")
    run_parser.add_argument("--fourier-scale", type=float, default=10.0, help="Fourier scale.")
    run_parser.add_argument("--learning-rate", type=float, default=1e-4, help="SGD learning rate.")
    run_parser.add_argument("--guidance-scale", type=float, default=100.0, help="Stable Diffusion guidance scale.")
    run_parser.add_argument("--noise-coef", type=float, default=0.10, help="SDS noise coefficient.")
    run_parser.add_argument("--min-step", type=int, default=10, help="Stable Diffusion min step.")
    run_parser.add_argument("--max-step", type=int, default=990, help="Stable Diffusion max step.")
    run_parser.add_argument("--solved-prompt", default=DEFAULT_SOLVED_PROMPT, help="Prompt for solved training views.")
    run_parser.add_argument(
        "--scrambled-prompt",
        default=DEFAULT_SCRAMBLED_PROMPT,
        help="Prompt for scrambled training views.",
    )
    run_parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE_PROMPT, help="Negative prompt.")
    run_parser.add_argument(
        "--continue-after-failure",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Continue to later view counts if one run fails.",
    )
    run_parser.add_argument(
        "--serve-viewer",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Serve the live viewer while training.",
    )
    run_parser.add_argument("--viewer-host", default="127.0.0.1", help="Host for the live viewer HTTP server.")
    run_parser.add_argument("--viewer-port", type=int, default=8765, help="Port for the live viewer HTTP server.")
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

    serve_parser = subparsers.add_parser("serve", help="Serve an existing sweep root so the viewer page can poll it.")
    serve_parser.add_argument(
        "--sweep-root",
        default=str(DEFAULT_SWEEP_ROOT),
        help="Directory containing the viewer and live preview files.",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host.")
    serve_parser.add_argument("--port", type=int, default=8765, help="HTTP bind port.")
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


def parse_view_counts(raw_value: str, max_views: int) -> list[int]:
    if not raw_value.strip():
        return list(range(3, max_views + 1))

    counts: list[int] = []
    for part in raw_value.split(","):
        count = int(part.strip())
        if count < 1 or count > max_views:
            raise ValueError(f"View count {count} is out of range 1..{max_views}")
        counts.append(count)
    return counts


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def build_train_views(
    selected_views: list[tuple[str, str]],
    *,
    solved_prompt: str,
    scrambled_prompt: str,
    negative_prompt: str,
    negative_label_cls: type[Any],
) -> list[dict[str, Any]]:
    views: list[dict[str, Any]] = []
    for arrangement, face in selected_views:
        prompt = solved_prompt if arrangement == "solved" else scrambled_prompt
        views.append(
            {
                "name": f"{arrangement}:{face}",
                "arrangement": arrangement,
                "face": face,
                "prompt": prompt,
                "weight": 1.0,
                "label": negative_label_cls(prompt, negative_prompt),
            }
        )
    return views


def ensure_official_repo(official_repo_dir: Path) -> None:
    if official_repo_dir.exists():
        return

    raise FileNotFoundError(
        "Missing Diffusion-Illusions checkout at "
        f"{official_repo_dir}. Clone it first with:\n"
        f"  git clone https://github.com/RyannDaGreat/Diffusion-Illusions.git {official_repo_dir}"
    )


def write_live_status(
    live_dir: Path,
    *,
    phase: str,
    message: str,
    selected_views: list[str],
    run_root: Path | None,
    current_view_count: int | None = None,
    current_iteration: int | None = None,
    total_iterations: int | None = None,
    training_preview: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "phase": phase,
        "message": message,
        "selected_views": selected_views,
        "updated_at_utc": utc_timestamp(),
        "current_view_count": current_view_count,
        "current_iteration": current_iteration,
        "total_iterations": total_iterations,
        "run_root": str(run_root) if run_root else None,
        "training_preview": training_preview,
    }
    if extra:
        payload.update(extra)
    write_json(live_dir / "status.json", payload)


def import_runtime_modules(repo_root: Path, official_repo_dir: Path) -> dict[str, Any]:
    ensure_official_repo(official_repo_dir)

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
            "Install the local sweep dependencies first. See experiments/local-face-sweep/README.md."
        ) from error

    return {
        "rp": rp,
        "torch": torch,
        "nn": nn,
        "batch_to_pil_face_dict": batch_to_pil_face_dict,
        "clone_rendered_to_cpu": clone_rendered_to_cpu,
        "load_source_faces": load_source_faces,
        "render_all_arrangements_torch": render_all_arrangements_torch,
        "save_rendered_faces": save_rendered_faces,
        "tensor_to_pil": tensor_to_pil,
        "LearnableImageFourier": LearnableImageFourier,
        "StableDiffusion": StableDiffusion,
        "NegativeLabel": NegativeLabel,
    }


def write_preview_images(
    *,
    live_dir: Path,
    run_root: Path,
    current_iteration: int,
    current_view_count: int,
    train_views: list[dict[str, Any]],
    rendered_cpu: dict[str, dict[str, Any]],
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
        title=f"{current_view_count} views preview at iter {current_iteration}",
        max_cols=3,
    )
    shutil.copy2(training_snapshot, history_training)

    live_training = live_dir / "training-preview.png"
    shutil.copy2(training_snapshot, live_training)

    return {
        "training_preview": live_training.name,
        "history_training_preview": relative_to_root(history_training, live_dir),
    }


def make_run_dirs(view_count: int, *, sweep_root: Path, runs_root: Path) -> tuple[Path, Path]:
    count_slug = f"{view_count}-views"
    output_root = sweep_root / count_slug
    run_root = runs_root / f"{utc_timestamp()}-local-view-sweep-{count_slug}"
    return output_root, run_root


@contextmanager
def optional_viewer_server(sweep_root: Path, *, host: str, port: int, enabled: bool, open_viewer: bool):
    write_live_viewer(sweep_root / VIEWER_DIR_NAME / "index.html")
    if not enabled:
        yield None
        return

    class QuietSimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

    handler = partial(QuietSimpleHTTPRequestHandler, directory=str(sweep_root))
    server = ThreadingHTTPServer((host, port), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    viewer_url = f"http://{host}:{port}/{VIEWER_DIR_NAME}/index.html"
    print(f"Live viewer: {viewer_url}")
    if open_viewer:
        webbrowser.open(viewer_url)

    try:
        yield viewer_url
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def cleanup_after_run(torch_module: Any) -> None:
    gc.collect()
    if torch_module.cuda.is_available():
        torch_module.cuda.empty_cache()
        torch_module.cuda.ipc_collect()


def update_progress_line(view_count: int, current_iteration: int, total_iterations: int, sampled_views: list[str]) -> None:
    sampled = ",".join(sampled_views) if sampled_views else "-"
    message = f"\r[{view_count} views] iter {current_iteration}/{total_iterations} | sampled={sampled}"
    sys.stdout.write(message.ljust(120))
    sys.stdout.flush()


def clear_progress_line() -> None:
    sys.stdout.write("\r" + (" " * 140) + "\r")
    sys.stdout.flush()


def run_experiment(args: argparse.Namespace) -> None:
    spec_path = Path(args.spec).resolve()
    source_dir = Path(args.source_dir).resolve()
    official_repo_dir = Path(args.official_repo_dir).resolve()
    sweep_root = Path(args.sweep_root).resolve()
    runs_root = Path(args.runs_root).resolve()
    live_dir = sweep_root / LIVE_DIR_NAME

    spec = load_spec(spec_path)
    face_order = list(spec["primeImages"])
    face_to_index = {face_id: index for index, face_id in enumerate(face_order)}
    view_growth_order = DEFAULT_VIEW_GROWTH_ORDER
    view_counts = parse_view_counts(args.view_counts, len(view_growth_order))

    runtime = import_runtime_modules(REPO_ROOT, official_repo_dir)
    rp = runtime["rp"]
    torch = runtime["torch"]
    nn = runtime["nn"]
    batch_to_pil_face_dict = runtime["batch_to_pil_face_dict"]
    clone_rendered_to_cpu = runtime["clone_rendered_to_cpu"]
    load_source_faces = runtime["load_source_faces"]
    render_all_arrangements_torch = runtime["render_all_arrangements_torch"]
    save_rendered_faces = runtime["save_rendered_faces"]
    tensor_to_pil = runtime["tensor_to_pil"]
    LearnableImageFourier = runtime["LearnableImageFourier"]
    StableDiffusion = runtime["StableDiffusion"]
    NegativeLabel = runtime["NegativeLabel"]

    device = rp.select_torch_device()
    if str(device) == "cpu" and not args.allow_cpu:
        raise RuntimeError(
            "The local face sweep needs a GPU for practical use. Re-run with --allow-cpu only if you really want a CPU attempt."
        )

    sweep_root.mkdir(parents=True, exist_ok=True)
    runs_root.mkdir(parents=True, exist_ok=True)
    live_dir.mkdir(parents=True, exist_ok=True)
    write_live_viewer(sweep_root / VIEWER_DIR_NAME / "index.html")
    reset_live_history(live_dir)

    print("Stable Diffusion device:", device)
    print("Sweep root:", sweep_root)
    print("Run root base:", runs_root)
    print("View counts:", view_counts)

    load_source_faces(source_dir, face_order)
    stable_diffusion = StableDiffusion(device, "runwayml/stable-diffusion-v1-5")
    stable_diffusion.max_step = args.max_step
    stable_diffusion.min_step = args.min_step

    sweep_summary_path = sweep_root / "sweep-summary.json"
    sweep_results: list[dict[str, Any]] = []

    class RubiksLearnableSourceFacesFourier(nn.Module):
        def __init__(self, face_ids: list[str], size: int):
            super().__init__()
            self.face_ids = list(face_ids)
            self.learnable_images = nn.ModuleList(
                [
                    LearnableImageFourier(
                        height=size,
                        width=size,
                        hidden_dim=args.fourier_hidden_dim,
                        num_features=args.fourier_num_features,
                        scale=args.fourier_scale,
                    )
                    for _ in self.face_ids
                ]
            )

        def forward(self) -> Any:
            return torch.stack([image() for image in self.learnable_images])

    with optional_viewer_server(
        sweep_root,
        host=args.viewer_host,
        port=args.viewer_port,
        enabled=args.serve_viewer,
        open_viewer=args.open_viewer,
    ):
        progress_interval = max(1, args.progress_interval)
        write_live_status(
            live_dir,
            phase="starting",
            message="Preparing the local face sweep.",
            selected_views=[],
            run_root=None,
            extra={"view_counts": view_counts},
        )

        for view_count in view_counts:
            output_root, run_root = make_run_dirs(view_count, sweep_root=sweep_root, runs_root=runs_root)
            output_root.mkdir(parents=True, exist_ok=True)
            run_root.mkdir(parents=True, exist_ok=True)

            selected_views = view_growth_order[:view_count]
            selected_view_names = [f"{arrangement}:{face}" for arrangement, face in selected_views]
            train_views = build_train_views(
                selected_views,
                solved_prompt=args.solved_prompt,
                scrambled_prompt=args.scrambled_prompt,
                negative_prompt=args.negative_prompt,
                negative_label_cls=NegativeLabel,
            )

            print("\n" + "=" * 80)
            print(f"Starting sweep run for {view_count} views:", selected_view_names)
            append_history_entry(
                live_dir,
                {
                    "entry_type": "run_start",
                    "title": f"Starting {view_count}-view run",
                    "message": ", ".join(selected_view_names),
                    "selected_views": selected_view_names,
                    "current_view_count": view_count,
                    "updated_at_utc": utc_timestamp(),
                },
            )

            write_live_status(
                live_dir,
                phase="running",
                message=f"Starting {view_count}-view run.",
                selected_views=selected_view_names,
                run_root=run_root,
                current_view_count=view_count,
                total_iterations=view_count * args.iterations_per_view,
            )

            try:
                learnable_faces = RubiksLearnableSourceFacesFourier(face_order, args.learnable_size).to(device)
                optimizer = torch.optim.SGD(learnable_faces.parameters(), lr=args.learning_rate)

                def get_current_state() -> tuple[Any, dict[str, dict[str, Any]]]:
                    current_source_batch = learnable_faces()
                    current_rendered = render_all_arrangements_torch(spec, current_source_batch, face_to_index)
                    return current_source_batch, current_rendered

                num_iter = view_count * args.iterations_per_view
                start_time = time.time()
                last_sampled_names: list[str] = []

                _, initial_rendered = get_current_state()
                initial_rendered_cpu = clone_rendered_to_cpu(initial_rendered)
                preview_paths = write_preview_images(
                    live_dir=live_dir,
                    run_root=run_root,
                    current_iteration=0,
                    current_view_count=view_count,
                    train_views=train_views,
                    rendered_cpu=initial_rendered_cpu,
                    tensor_to_pil=tensor_to_pil,
                )
                write_live_status(
                    live_dir,
                    phase="running",
                    message=f"Initial preview ready for {view_count}-view run.",
                    selected_views=selected_view_names,
                    run_root=run_root,
                    current_view_count=view_count,
                    current_iteration=0,
                    total_iterations=num_iter,
                    training_preview=preview_paths["training_preview"],
                )
                append_history_entry(
                    live_dir,
                    {
                        "entry_type": "preview",
                        "title": f"{view_count} views · initial preview",
                        "message": f"Initial preview for the {view_count}-view run.",
                        "selected_views": selected_view_names,
                        "current_view_count": view_count,
                        "current_iteration": 0,
                        "total_iterations": num_iter,
                        "updated_at_utc": utc_timestamp(),
                        "training_preview": preview_paths["history_training_preview"],
                        "last_sampled_views": [],
                    },
                )

                for iter_num in range(num_iter):
                    optimizer.zero_grad(set_to_none=True)
                    _, current_rendered = get_current_state()

                    sampled_views = list(rp.random_batch(train_views, batch_size=1))
                    last_sampled_names = [view["name"] for view in sampled_views]
                    for view in sampled_views:
                        current_view = current_rendered[view["arrangement"]][view["face"]][None]
                        stable_diffusion.train_step(
                            view["label"].embedding,
                            current_view,
                            noise_coef=args.noise_coef * view["weight"],
                            guidance_scale=args.guidance_scale,
                        )

                    optimizer.step()

                    current_iteration = iter_num + 1
                    if current_iteration == 1 or current_iteration % progress_interval == 0 or current_iteration == num_iter:
                        update_progress_line(view_count, current_iteration, num_iter, last_sampled_names)

                    if current_iteration % args.display_interval == 0 or iter_num == 0:
                        clear_progress_line()
                        print(f"Saved preview at iteration {current_iteration}/{num_iter} | sampled={last_sampled_names}")
                        _, preview_rendered = get_current_state()
                        preview_rendered_cpu = clone_rendered_to_cpu(preview_rendered)
                        preview_paths = write_preview_images(
                            live_dir=live_dir,
                            run_root=run_root,
                            current_iteration=current_iteration,
                            current_view_count=view_count,
                            train_views=train_views,
                            rendered_cpu=preview_rendered_cpu,
                            tensor_to_pil=tensor_to_pil,
                        )
                        write_live_status(
                            live_dir,
                            phase="running",
                            message=f"{view_count}-view run preview at iteration {iter_num + 1}.",
                            selected_views=selected_view_names,
                            run_root=run_root,
                            current_view_count=view_count,
                            current_iteration=current_iteration,
                            total_iterations=num_iter,
                            extra={"last_sampled_views": last_sampled_names},
                            training_preview=preview_paths["training_preview"],
                        )
                        append_history_entry(
                            live_dir,
                            {
                                "entry_type": "preview",
                                "title": f"{view_count} views · iter {current_iteration}",
                                "message": f"Preview at iteration {current_iteration}.",
                                "selected_views": selected_view_names,
                                "current_view_count": view_count,
                                "current_iteration": current_iteration,
                                "total_iterations": num_iter,
                                "updated_at_utc": utc_timestamp(),
                                "training_preview": preview_paths["history_training_preview"],
                                "last_sampled_views": last_sampled_names,
                            },
                        )
                        update_progress_line(view_count, current_iteration, num_iter, last_sampled_names)

                final_source_batch, final_rendered = get_current_state()
                clear_progress_line()
                final_source_faces = batch_to_pil_face_dict(final_source_batch.detach().cpu(), face_order)
                final_rendered_cpu = clone_rendered_to_cpu(final_rendered)
                preview_paths = write_preview_images(
                    live_dir=live_dir,
                    run_root=run_root,
                    current_iteration=num_iter,
                    current_view_count=view_count,
                    train_views=train_views,
                    rendered_cpu=final_rendered_cpu,
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
                    REPO_ROOT / "notebooks" / "archive" / "rubiks_colab_face_sweep.ipynb",
                    run_root / "notebook-source.ipynb",
                )
                shutil.copy2(Path(__file__).resolve(), run_root / "script-source.py")

                metadata = {
                    "status": "success",
                    "timestamp_utc": utc_timestamp(),
                    "view_count": view_count,
                    "selected_views": selected_view_names,
                    "parameterization_mode": "official_fourier_128",
                    "solved_prompt": args.solved_prompt,
                    "scrambled_prompt": args.scrambled_prompt,
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
                        "iterations_per_view": args.iterations_per_view,
                        "num_iter": num_iter,
                        "display_interval": args.display_interval,
                        "learnable_size": args.learnable_size,
                        "fourier_hidden_dim": args.fourier_hidden_dim,
                        "fourier_num_features": args.fourier_num_features,
                        "fourier_scale": args.fourier_scale,
                        "learning_rate": args.learning_rate,
                        "optimizer_name": "SGD",
                        "guidance_scale": args.guidance_scale,
                        "noise_coef": args.noise_coef,
                        "min_step": stable_diffusion.min_step,
                        "max_step": stable_diffusion.max_step,
                    },
                    "elapsed_seconds": round(time.time() - start_time, 2),
                    "last_sampled_views": last_sampled_names,
                    "saved_paths": {
                        "source_output_dir": str(source_output_dir),
                        "render_output_dir": str(render_output_dir),
                        "run_root": str(run_root),
                        "metadata_path": str(run_root / "metadata.json"),
                        "preview_dir": str(run_root / "previews"),
                    },
                }
                write_json(run_root / "metadata.json", metadata)
                sweep_results.append(metadata)
                write_json(sweep_summary_path, {"results": sweep_results})

                print(f"Completed {view_count}-view run in {metadata['elapsed_seconds']:.1f}s")
                print("Saved run root:", run_root)

                write_live_status(
                    live_dir,
                    phase="running",
                    message=f"Completed {view_count}-view run in {metadata['elapsed_seconds']:.1f}s.",
                    selected_views=selected_view_names,
                    run_root=run_root,
                    current_view_count=view_count,
                    current_iteration=num_iter,
                    total_iterations=num_iter,
                    extra={"last_sampled_views": last_sampled_names},
                    training_preview=preview_paths["training_preview"],
                )
                append_history_entry(
                    live_dir,
                    {
                        "entry_type": "run_complete",
                        "title": f"Completed {view_count}-view run",
                        "message": f"Finished in {metadata['elapsed_seconds']:.1f}s.",
                        "selected_views": selected_view_names,
                        "current_view_count": view_count,
                        "updated_at_utc": utc_timestamp(),
                    },
                )
            except Exception as error:
                clear_progress_line()
                result = {
                    "status": "failed",
                    "timestamp_utc": utc_timestamp(),
                    "view_count": view_count,
                    "selected_views": selected_view_names,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "traceback": traceback.format_exc(),
                }
                sweep_results.append(result)
                write_json(sweep_summary_path, {"results": sweep_results})
                write_live_status(
                    live_dir,
                    phase="failed",
                    message=f"Run failed for {view_count} views: {type(error).__name__}: {error}",
                    selected_views=selected_view_names,
                    run_root=run_root,
                    current_view_count=view_count,
                    extra={"error_type": type(error).__name__, "error_message": str(error)},
                )
                append_history_entry(
                    live_dir,
                    {
                        "entry_type": "run_failed",
                        "title": f"Failed {view_count}-view run",
                        "message": f"{type(error).__name__}: {error}",
                        "selected_views": selected_view_names,
                        "current_view_count": view_count,
                        "updated_at_utc": utc_timestamp(),
                    },
                )
                print(f"Run failed for {view_count} views: {type(error).__name__}: {error}")
                if not args.continue_after_failure:
                    cleanup_after_run(torch)
                    break

            cleanup_after_run(torch)

    print("\nSweep finished. Summary saved to:", sweep_summary_path)
    for result in sweep_results:
        line = f"{result['view_count']} views -> {result['status']}"
        if result["status"] == "success":
            line += f" ({result['elapsed_seconds']}s)"
        else:
            line += f" ({result['error_type']})"
        print(line)

    final_phase = "completed" if sweep_results and all(result["status"] == "success" for result in sweep_results) else "completed-with-errors"
    write_live_status(
        live_dir,
        phase=final_phase,
        message=f"Sweep finished. Summary saved to {sweep_summary_path}",
        selected_views=[],
        run_root=None,
        extra={"summary_path": relative_to_root(sweep_summary_path, sweep_root)},
    )
    append_history_entry(
        live_dir,
        {
            "entry_type": "sweep_complete",
            "title": "Sweep finished",
            "message": f"Summary saved to {sweep_summary_path}",
            "updated_at_utc": utc_timestamp(),
        },
    )


def serve_existing_viewer(args: argparse.Namespace) -> None:
    sweep_root = Path(args.sweep_root).resolve()
    write_live_viewer(sweep_root / VIEWER_DIR_NAME / "index.html")
    history_path = sweep_root / LIVE_DIR_NAME / "history.json"
    if not history_path.exists():
        write_json(history_path, {"entries": []})
    with optional_viewer_server(
        sweep_root,
        host=args.host,
        port=args.port,
        enabled=True,
        open_viewer=args.open_viewer,
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
