from __future__ import annotations

from python_bridge.live_preview import (
    append_history_entry,
    read_json,
    reset_live_history,
    save_labeled_image_grid,
    write_json,
    write_live_viewer,
)

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
