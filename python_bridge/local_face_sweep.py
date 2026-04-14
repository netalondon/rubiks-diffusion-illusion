from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from PIL import Image, ImageColor, ImageDraw, ImageFont

DEFAULT_VIEW_GROWTH_ORDER: list[tuple[str, str]] = [
    ("solved", "R"),
    ("scrambled", "U"),
    ("solved", "U"),
    ("scrambled", "R"),
    ("solved", "L"),
    ("scrambled", "L"),
    ("solved", "F"),
    ("scrambled", "F"),
    ("solved", "D"),
    ("scrambled", "D"),
    ("solved", "B"),
    ("scrambled", "B"),
]

DEFAULT_SOLVED_PROMPT = "a watercolor drawing of a cute cat"
DEFAULT_SCRAMBLED_PROMPT = "a watercolor drawing of a cute dog"
DEFAULT_NEGATIVE_PROMPT = (
    "blurry, noisy, muddy colors, text, watermark, low quality, collage, multiple animals, cropped face"
)

VIEWER_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Rubik Local Face Sweep</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f4efe8;
        --panel: rgba(255, 252, 247, 0.84);
        --ink: #1d1a17;
        --muted: #6b6258;
        --accent: #8d3b27;
        --border: rgba(61, 38, 24, 0.16);
        --shadow: 0 18px 40px rgba(74, 48, 30, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(191, 122, 72, 0.18), transparent 36%),
          radial-gradient(circle at top right, rgba(69, 122, 171, 0.14), transparent 28%),
          linear-gradient(180deg, #fbf7f1, var(--bg));
      }

      .shell {
        width: min(1200px, calc(100vw - 32px));
        margin: 32px auto 48px;
      }

      .hero {
        margin-bottom: 20px;
      }

      h1 {
        margin: 0 0 6px;
        font-size: clamp(2rem, 4vw, 3.4rem);
        line-height: 1;
      }

      .subtitle {
        margin: 0;
        color: var(--muted);
        font-size: 1.05rem;
      }

      .status {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
      }

      .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 18px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(8px);
      }

      .metric {
        padding: 16px 18px;
      }

      .metric-label {
        font-size: 0.82rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }

      .metric-value {
        margin-top: 8px;
        font-size: 1.15rem;
      }

      .message {
        padding: 18px;
        margin-bottom: 20px;
      }

      .views {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
      }

      .chip {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(141, 59, 39, 0.08);
        color: var(--accent);
        font-size: 0.92rem;
      }

      .gallery {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 18px;
      }

      .figure {
        padding: 14px;
      }

      .figure h2 {
        margin: 0 0 10px;
        font-size: 1.1rem;
      }

      .figure img {
        width: 100%;
        display: block;
        border-radius: 14px;
        border: 1px solid var(--border);
        background: #eee8de;
      }

      .small {
        margin-top: 10px;
        color: var(--muted);
        font-size: 0.92rem;
      }

      a {
        color: var(--accent);
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="hero">
        <h1>Rubik Local Face Sweep</h1>
        <p class="subtitle">This page auto-refreshes from the latest preview snapshots.</p>
      </div>

      <div class="status">
        <div class="panel metric">
          <div class="metric-label">Phase</div>
          <div class="metric-value" id="phase">Waiting for status.json</div>
        </div>
        <div class="panel metric">
          <div class="metric-label">View Count</div>
          <div class="metric-value" id="view-count">-</div>
        </div>
        <div class="panel metric">
          <div class="metric-label">Iteration</div>
          <div class="metric-value" id="iteration">-</div>
        </div>
        <div class="panel metric">
          <div class="metric-label">Updated</div>
          <div class="metric-value" id="updated-at">-</div>
        </div>
      </div>

      <div class="panel message">
        <div id="message">No live status yet.</div>
        <div class="views" id="selected-views"></div>
        <div class="small">
          Run root: <a id="run-root-link" href="../live/status.json">status.json</a>
        </div>
      </div>

      <div class="gallery">
        <div class="panel figure">
          <h2>Training Views</h2>
          <img id="training-preview" alt="Latest training view preview">
        </div>
        <div class="panel figure">
          <h2>Source Faces</h2>
          <img id="source-preview" alt="Latest source face preview">
        </div>
        <div class="panel figure">
          <h2>Solved Faces</h2>
          <img id="solved-preview" alt="Latest solved face preview">
        </div>
        <div class="panel figure">
          <h2>Scrambled Faces</h2>
          <img id="scrambled-preview" alt="Latest scrambled face preview">
        </div>
      </div>
    </div>

    <script>
      const statusUrl = "../live/status.json";
      const imageIds = {
        training_preview: "training-preview",
        source_preview: "source-preview",
        solved_preview: "solved-preview",
        scrambled_preview: "scrambled-preview",
      };

      function withBust(path) {
        return `../live/${path}?t=${Date.now()}`;
      }

      function setText(id, value) {
        document.getElementById(id).textContent = value ?? "-";
      }

      function setImage(statusKey, fallbackAlt) {
        const element = document.getElementById(imageIds[statusKey]);
        const relativePath = window.currentStatus?.[statusKey];
        if (!relativePath) {
          element.removeAttribute("src");
          element.alt = fallbackAlt;
          return;
        }
        element.src = withBust(relativePath);
      }

      async function refresh() {
        try {
          const response = await fetch(`${statusUrl}?t=${Date.now()}`, { cache: "no-store" });
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          const status = await response.json();
          window.currentStatus = status;

          setText("phase", status.phase || "unknown");
          setText("view-count", status.current_view_count ?? "-");
          const iteration = status.current_iteration && status.total_iterations
            ? `${status.current_iteration} / ${status.total_iterations}`
            : "-";
          setText("iteration", iteration);
          setText("updated-at", status.updated_at_utc || "-");
          setText("message", status.message || "No message provided.");

          const container = document.getElementById("selected-views");
          container.innerHTML = "";
          (status.selected_views || []).forEach((view) => {
            const chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = view;
            container.appendChild(chip);
          });

          const runRootLink = document.getElementById("run-root-link");
          runRootLink.textContent = status.run_root || "status.json";
          runRootLink.href = statusUrl;

          setImage("training_preview", "Training preview not available yet.");
          setImage("source_preview", "Source preview not available yet.");
          setImage("solved_preview", "Solved preview not available yet.");
          setImage("scrambled_preview", "Scrambled preview not available yet.");
        } catch (error) {
          setText("phase", "waiting");
          setText("message", `Waiting for live output: ${error}`);
        }
      }

      refresh();
      setInterval(refresh, 3000);
    </script>
  </body>
</html>
"""


def write_json(path: str | Path, payload: Mapping[str, object]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")


def write_live_viewer(viewer_path: str | Path) -> None:
    viewer_path = Path(viewer_path)
    viewer_path.parent.mkdir(parents=True, exist_ok=True)
    viewer_path.write_text(VIEWER_HTML, encoding="utf8")


def _load_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default()


def save_labeled_image_grid(
    items: Sequence[tuple[str, Image.Image]],
    output_path: str | Path,
    *,
    title: str,
    max_cols: int = 4,
    panel_color: str = "#f7f3ec",
    title_color: str = "#1d1a17",
    label_color: str = "#4f463d",
) -> Path:
    if not items:
        raise ValueError("Expected at least one image for the preview grid")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    prepared_items: list[tuple[str, Image.Image]] = []
    for label, image in items:
        prepared_items.append((label, image.convert("RGBA")))

    first_image = prepared_items[0][1]
    cell_width, cell_height = first_image.size
    cols = min(max_cols, max(1, len(prepared_items)))
    rows = (len(prepared_items) + cols - 1) // cols

    outer_margin = 28
    gutter = 20
    title_band = 56
    label_band = 34
    canvas_width = outer_margin * 2 + cols * cell_width + (cols - 1) * gutter
    canvas_height = (
        outer_margin * 2
        + title_band
        + rows * (cell_height + label_band)
        + (rows - 1) * gutter
    )

    background = Image.new("RGBA", (canvas_width, canvas_height), ImageColor.getrgb(panel_color) + (255,))
    draw = ImageDraw.Draw(background)
    title_font = _load_font(26)
    label_font = _load_font(18)

    draw.text((outer_margin, outer_margin), title, fill=title_color, font=title_font)

    grid_origin_y = outer_margin + title_band
    for index, (label, image) in enumerate(prepared_items):
        col = index % cols
        row = index // cols
        x = outer_margin + col * (cell_width + gutter)
        y = grid_origin_y + row * (cell_height + label_band + gutter)
        background.alpha_composite(image, (x, y))
        draw.text((x, y + cell_height + 8), label, fill=label_color, font=label_font)

    background.save(output_path)
    return output_path
