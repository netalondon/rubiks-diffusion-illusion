from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_bridge.rubiks_illusion_operator import load_source_faces, load_spec, render_all_arrangements, save_rendered_faces


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


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    spec = load_spec(spec_path)
    source_faces = load_source_faces(source_dir, spec["primeImages"])
    rendered = render_all_arrangements(spec, source_faces)

    save_rendered_faces(rendered["solved"], output_dir / "solved")
    save_rendered_faces(rendered["scrambled"], output_dir / "scrambled")

    print(f"Rendered solved faces to {output_dir / 'solved'}")
    print(f"Rendered scrambled faces to {output_dir / 'scrambled'}")


if __name__ == "__main__":
    main()
