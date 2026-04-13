from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, Mapping

from PIL import Image

FACE_FILE_NAMES: Dict[str, str] = {
    "U": "up.png",
    "D": "down.png",
    "L": "left.png",
    "R": "right.png",
    "F": "front.png",
    "B": "back.png",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render solved and scrambled Rubik's cube faces from a rubiks-illusion-spec JSON file."
    )
    parser.add_argument(
        "--spec",
        default="public/generated/rubiks-illusion-spec.json",
        help="Path to the exported Rubik's illusion spec JSON.",
    )
    parser.add_argument(
        "--source-dir",
        default="src/assets/face-art",
        help="Directory containing face images named up.png/down.png/left.png/right.png/front.png/back.png.",
    )
    parser.add_argument(
        "--output-dir",
        default="output/python/rubiks-illusion-render",
        help="Directory where rendered solved/scrambled faces will be written.",
    )
    return parser.parse_args()


def load_spec(spec_path: Path) -> dict:
    with spec_path.open("r", encoding="utf8") as handle:
        return json.load(handle)


def load_source_faces(source_dir: Path, prime_images: Iterable[str]) -> Dict[str, Image.Image]:
    faces: Dict[str, Image.Image] = {}

    for face in prime_images:
        if face not in FACE_FILE_NAMES:
            raise ValueError(f"Unsupported face id in spec: {face}")

        image_path = source_dir / FACE_FILE_NAMES[face]
        if not image_path.exists():
            raise FileNotFoundError(f"Missing source face image: {image_path}")

        with Image.open(image_path) as image:
            faces[face] = image.convert("RGBA")

    return faces


def render_arrangement(
    arrangement: Iterable[Mapping[str, object]],
    source_faces: Mapping[str, Image.Image],
    source_grid_size: int,
) -> Dict[str, Image.Image]:
    rendered_faces: Dict[str, Image.Image] = {}

    for face_spec in arrangement:
        face_id = str(face_spec["face"])
        grid = face_spec["grid"]
        if not isinstance(grid, list) or len(grid) != source_grid_size:
            raise ValueError(f"Unexpected grid for face {face_id}")

        face_image = render_face_grid(grid, source_faces, source_grid_size)
        rendered_faces[face_id] = face_image

    return rendered_faces


def render_face_grid(
    grid: list[object], source_faces: Mapping[str, Image.Image], source_grid_size: int
) -> Image.Image:
    reference_face = next(iter(source_faces.values()))
    tile_width = reference_face.width // source_grid_size
    tile_height = reference_face.height // source_grid_size
    output = Image.new("RGBA", (tile_width * source_grid_size, tile_height * source_grid_size))

    for row_index, row in enumerate(grid):
        if not isinstance(row, list) or len(row) != source_grid_size:
            raise ValueError(f"Unexpected row shape at row {row_index}")

        for col_index, cell in enumerate(row):
            if not isinstance(cell, dict):
                raise ValueError(f"Unexpected cell at row {row_index}, col {col_index}")

            tile = extract_tile(
                source_face=source_faces[str(cell["sourceFace"])],
                source_row=int(cell["sourceRow"]),
                source_col=int(cell["sourceCol"]),
                source_grid_size=source_grid_size,
            )
            rotated_tile = rotate_tile(tile, int(cell["rotationQuarterTurns"]))
            output.paste(rotated_tile, (col_index * tile_width, row_index * tile_height))

    return output


def extract_tile(source_face: Image.Image, source_row: int, source_col: int, source_grid_size: int) -> Image.Image:
    tile_width = source_face.width // source_grid_size
    tile_height = source_face.height // source_grid_size
    left = source_col * tile_width
    top = source_row * tile_height
    return source_face.crop((left, top, left + tile_width, top + tile_height))


def rotate_tile(tile: Image.Image, quarter_turns: int) -> Image.Image:
    if quarter_turns not in {0, 1, 2, 3}:
        raise ValueError(f"Unsupported quarter turn count: {quarter_turns}")

    if quarter_turns == 0:
        return tile

    return tile.rotate(-90 * quarter_turns, expand=False)


def save_rendered_faces(rendered_faces: Mapping[str, Image.Image], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for face_id, image in rendered_faces.items():
        image.save(output_dir / f"{face_id}.png")

    save_contact_sheet(rendered_faces, output_dir / "contact-sheet.png")


def save_contact_sheet(rendered_faces: Mapping[str, Image.Image], output_path: Path) -> None:
    face_order = ["U", "D", "L", "R", "F", "B"]
    sample = next(iter(rendered_faces.values()))
    margin = 24
    label_band = 44
    cols = 3
    rows = 2
    canvas = Image.new(
        "RGBA",
        (
            cols * sample.width + (cols + 1) * margin,
            rows * (sample.height + label_band) + (rows + 1) * margin,
        ),
        (247, 243, 236, 255),
    )

    for index, face_id in enumerate(face_order):
        image = rendered_faces[face_id]
        col = index % cols
        row = index // cols
        x = margin + col * (sample.width + margin)
        y = margin + row * (sample.height + label_band + margin)
        canvas.paste(image, (x, y))

    canvas.save(output_path)


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    spec = load_spec(spec_path)
    source_faces = load_source_faces(source_dir, spec["primeImages"])
    source_grid_size = int(spec["sourceGridSize"])

    solved = render_arrangement(spec["arrangements"]["solved"], source_faces, source_grid_size)
    scrambled = render_arrangement(spec["arrangements"]["scrambled"], source_faces, source_grid_size)

    save_rendered_faces(solved, output_dir / "solved")
    save_rendered_faces(scrambled, output_dir / "scrambled")

    print(f"Rendered solved faces to {output_dir / 'solved'}")
    print(f"Rendered scrambled faces to {output_dir / 'scrambled'}")


if __name__ == "__main__":
    main()
