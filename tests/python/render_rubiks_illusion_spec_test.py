from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from python_bridge.rubiks_illusion_operator import load_source_faces, render_all_arrangements, render_arrangement


def make_test_tile_image(base_color: tuple[int, int, int, int], marker_color: tuple[int, int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (6, 6), base_color)
    image.putpixel((0, 0), marker_color)
    image.putpixel((1, 0), marker_color)
    image.putpixel((0, 1), marker_color)
    return image


class RenderRubiksIllusionSpecTest(unittest.TestCase):
    def test_render_arrangement_crops_and_rotates_tiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp) / "faces"
            source_dir.mkdir()

            for face_id, file_name in {
                "U": "up.png",
                "D": "down.png",
                "L": "left.png",
                "R": "right.png",
                "F": "front.png",
                "B": "back.png",
            }.items():
                image = Image.new("RGBA", (6, 6), (0, 0, 0, 255))

                for row in range(3):
                    for col in range(3):
                        base = (
                            20 * (row + 1),
                            40 * (col + 1),
                            15 * (row + col + 1),
                            255,
                        )
                        marker = (255, 255, 255, 255)
                        tile = make_test_tile_image(base, marker)
                        image.paste(tile, (col * 2, row * 2))

                image.save(source_dir / file_name)

            source_faces = load_source_faces(source_dir, ["U", "D", "L", "R", "F", "B"])
            arrangement = [
                {
                    "face": "F",
                    "grid": [
                        [
                            {
                                "sourceFace": "F",
                                "sourceRow": 0,
                                "sourceCol": 0,
                                "rotationQuarterTurns": 1,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 0,
                                "sourceCol": 1,
                                "rotationQuarterTurns": 0,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 0,
                                "sourceCol": 2,
                                "rotationQuarterTurns": 0,
                            },
                        ],
                        [
                            {
                                "sourceFace": "F",
                                "sourceRow": 1,
                                "sourceCol": 0,
                                "rotationQuarterTurns": 0,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 1,
                                "sourceCol": 1,
                                "rotationQuarterTurns": 0,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 1,
                                "sourceCol": 2,
                                "rotationQuarterTurns": 0,
                            },
                        ],
                        [
                            {
                                "sourceFace": "F",
                                "sourceRow": 2,
                                "sourceCol": 0,
                                "rotationQuarterTurns": 0,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 2,
                                "sourceCol": 1,
                                "rotationQuarterTurns": 0,
                            },
                            {
                                "sourceFace": "F",
                                "sourceRow": 2,
                                "sourceCol": 2,
                                "rotationQuarterTurns": 0,
                            },
                        ],
                    ],
                }
            ]

            rendered = render_arrangement(arrangement, source_faces, 3)
            face = rendered["F"]

            self.assertEqual(face.size, (6, 6))
            self.assertEqual(face.getpixel((1, 0)), (255, 255, 255, 255))

    def test_render_all_arrangements_accepts_in_memory_source_images(self) -> None:
        source_faces = {}

        for index, face_id in enumerate(["U", "D", "L", "R", "F", "B"]):
            image = Image.new("RGBA", (6, 6), (10 * index, 20 * index, 30 * index, 255))
            image.putpixel((0, 0), (255, 255, 255, 255))
            source_faces[face_id] = image

        spec = {
            "sourceGridSize": 3,
            "arrangements": {
                "solved": [
                    {
                        "face": "U",
                        "grid": [
                            [
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 0, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                            [
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 0, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                            [
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 0, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                        ],
                    }
                ],
                "scrambled": [
                    {
                        "face": "U",
                        "grid": [
                            [
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 0, "rotationQuarterTurns": 1},
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 0, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                            [
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 0, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 1, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                            [
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 0, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 1, "rotationQuarterTurns": 0},
                                {"sourceFace": "U", "sourceRow": 2, "sourceCol": 2, "rotationQuarterTurns": 0},
                            ],
                        ],
                    }
                ],
            },
        }

        rendered = render_all_arrangements(spec, source_faces)

        self.assertIn("solved", rendered)
        self.assertIn("scrambled", rendered)
        self.assertEqual(rendered["solved"]["U"].size, (6, 6))
        self.assertEqual(rendered["scrambled"]["U"].getpixel((1, 0)), (255, 255, 255, 255))


if __name__ == "__main__":
    unittest.main()
