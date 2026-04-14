from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

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
        --panel: rgba(255, 252, 247, 0.88);
        --panel-strong: rgba(255, 250, 244, 0.96);
        --ink: #1d1a17;
        --muted: #6b6258;
        --accent: #8d3b27;
        --accent-soft: rgba(141, 59, 39, 0.08);
        --border: rgba(61, 38, 24, 0.16);
        --shadow: 0 18px 40px rgba(74, 48, 30, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      html {
        scroll-behavior: smooth;
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
        width: min(1300px, calc(100vw - 28px));
        margin: 24px auto 56px;
      }

      .hero {
        margin-bottom: 18px;
      }

      h1 {
        margin: 0 0 8px;
        font-size: clamp(2.1rem, 4vw, 3.5rem);
        line-height: 1;
      }

      .subtitle {
        margin: 0;
        color: var(--muted);
        font-size: 1.05rem;
      }

      .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 20px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(8px);
      }

      .status {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 14px;
      }

      .metric {
        padding: 16px 18px;
      }

      .metric-label {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--muted);
      }

      .metric-value {
        margin-top: 8px;
        font-size: 1.12rem;
      }

      .message {
        padding: 18px;
        margin-bottom: 14px;
      }

      .helper {
        color: var(--muted);
        font-size: 0.95rem;
        line-height: 1.45;
      }

      .views, .sampled {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 10px;
      }

      .chip {
        padding: 6px 10px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.92rem;
      }

      .section-head {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 14px;
        margin: 24px 0 12px;
      }

      h2 {
        margin: 0;
        font-size: 1.45rem;
      }

      .timeline {
        display: grid;
        gap: 12px;
      }

      .event, .snapshot {
        padding: 16px;
      }

      .event {
        border-left: 5px solid rgba(141, 59, 39, 0.35);
      }

      .snapshot {
        background: var(--panel-strong);
      }

      .row-head {
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: start;
        margin-bottom: 10px;
      }

      .row-title {
        font-size: 1.08rem;
      }

      .row-meta {
        color: var(--muted);
        font-size: 0.92rem;
        white-space: nowrap;
      }

      .row-note {
        color: var(--muted);
        font-size: 0.94rem;
        line-height: 1.45;
        margin-bottom: 10px;
      }

      figure {
        margin: 0;
      }

      figure img {
        width: 100%;
        display: block;
        border-radius: 14px;
        border: 1px solid var(--border);
        background: #eee8de;
      }

      .single-preview {
        margin-top: 12px;
      }

      figcaption {
        margin-top: 8px;
        color: var(--muted);
        font-size: 0.92rem;
      }

      .empty {
        padding: 28px 20px;
        text-align: center;
        color: var(--muted);
      }

      .footer-note {
        margin-top: 16px;
        color: var(--muted);
        font-size: 0.92rem;
      }

      a {
        color: var(--accent);
      }

      @media (max-width: 920px) {
        .row-head {
          flex-direction: column;
        }

        .row-meta {
          white-space: normal;
        }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="hero">
        <h1>Rubik Local Face Sweep</h1>
        <p class="subtitle">Live status on top, notebook-style preview history below.</p>
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
        <div class="sampled" id="sampled-views"></div>
        <div class="footer-note">
          The timeline focuses on the training-view preview only, so each snapshot can stay larger and easier to compare.
          Live status file: <a id="status-link" href="../live/status.json">status.json</a>
        </div>
      </div>

      <div class="section-head">
        <h2>Preview Timeline</h2>
        <div class="helper">Each preview row is appended below the previous one, like the notebook.</div>
      </div>

      <div class="timeline" id="timeline">
        <div class="panel empty">Waiting for the first preview snapshot.</div>
      </div>
    </div>

    <script>
      const statusUrl = "../live/status.json";
      const historyUrl = "../live/history.json";
      let renderedEntryCount = 0;

      function withBust(path) {
        return `../live/${path}?t=${Date.now()}`;
      }

      function setText(id, value) {
        document.getElementById(id).textContent = value ?? "-";
      }

      function renderChips(containerId, values, emptyText) {
        const container = document.getElementById(containerId);
        container.innerHTML = "";
        if (!values || values.length === 0) {
          if (emptyText) {
            const chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = emptyText;
            container.appendChild(chip);
          }
          return;
        }
        values.forEach((value) => {
          const chip = document.createElement("span");
          chip.className = "chip";
          chip.textContent = value;
          container.appendChild(chip);
        });
      }

      function renderTimeline(entries) {
        const timeline = document.getElementById("timeline");
        if (!entries || entries.length === 0) {
          timeline.innerHTML = '<div class="panel empty">Waiting for the first preview snapshot.</div>';
          renderedEntryCount = 0;
          return;
        }

        const wasNearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 140;
        timeline.innerHTML = entries.map((entry) => {
          if (entry.entry_type !== "preview") {
            return `
              <article class="panel event">
                <div class="row-head">
                  <div class="row-title">${entry.title || entry.message || "Run event"}</div>
                  <div class="row-meta">${entry.updated_at_utc || "-"}</div>
                </div>
                <div class="row-note">${entry.message || ""}</div>
              </article>
            `;
          }

          const iterationLabel = entry.total_iterations
            ? `${entry.current_iteration} / ${entry.total_iterations}`
            : `${entry.current_iteration ?? "-"}`;

          const sampled = entry.last_sampled_views && entry.last_sampled_views.length
            ? `Sampled: ${entry.last_sampled_views.join(", ")}`
            : "Initial preview";

          return `
            <article class="panel snapshot">
              <div class="row-head">
                <div class="row-title">${entry.title || "Preview"}</div>
                <div class="row-meta">${entry.updated_at_utc || "-"} · iter ${iterationLabel}</div>
              </div>
              <div class="row-note">${sampled}</div>
              <div class="views">
                ${(entry.selected_views || []).map((view) => `<span class="chip">${view}</span>`).join("")}
              </div>
              <figure class="single-preview">
                <img src="${withBust(entry.training_preview)}" alt="Training views preview">
                <figcaption>Training views</figcaption>
              </figure>
            </article>
          `;
        }).join("");

        if (entries.length > renderedEntryCount && wasNearBottom) {
          window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }
        renderedEntryCount = entries.length;
      }

      async function refresh() {
        try {
          const statusResponse = await fetch(`${statusUrl}?t=${Date.now()}`, { cache: "no-store" });

          if (!statusResponse.ok) {
            throw new Error(`status HTTP ${statusResponse.status}`);
          }

          const status = await statusResponse.json();
          let history = { entries: [] };
          try {
            const historyResponse = await fetch(`${historyUrl}?t=${Date.now()}`, { cache: "no-store" });
            if (historyResponse.ok) {
              history = await historyResponse.json();
            }
          } catch (error) {
            history = { entries: [] };
          }

          setText("phase", status.phase || "unknown");
          setText("view-count", status.current_view_count ?? "-");
          const iteration = status.current_iteration && status.total_iterations
            ? `${status.current_iteration} / ${status.total_iterations}`
            : (status.current_iteration ?? "-");
          setText("iteration", iteration);
          setText("updated-at", status.updated_at_utc || "-");
          setText("message", status.message || "No message provided.");
          renderChips("selected-views", status.selected_views || [], "No selected views yet");
          renderChips("sampled-views", status.last_sampled_views || [], "");

          const statusLink = document.getElementById("status-link");
          statusLink.textContent = status.run_root || "status.json";
          statusLink.href = statusUrl;

          renderTimeline(history.entries || []);
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


def write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf8")


def read_json(path: str | Path, *, default: Mapping[str, Any] | None = None) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return dict(default or {})
    return json.loads(path.read_text(encoding="utf8"))


def write_live_viewer(viewer_path: str | Path) -> None:
    viewer_path = Path(viewer_path)
    viewer_path.parent.mkdir(parents=True, exist_ok=True)
    viewer_path.write_text(VIEWER_HTML, encoding="utf8")


def reset_live_history(live_dir: str | Path) -> None:
    live_dir = Path(live_dir)
    history_dir = live_dir / "history"
    if history_dir.exists():
        shutil.rmtree(history_dir)
    write_json(live_dir / "history.json", {"entries": []})


def append_history_entry(live_dir: str | Path, entry: Mapping[str, Any]) -> None:
    live_dir = Path(live_dir)
    history_path = live_dir / "history.json"
    payload = read_json(history_path, default={"entries": []})
    entries = list(payload.get("entries", []))
    entries.append(dict(entry))
    payload["entries"] = entries
    write_json(history_path, payload)


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
