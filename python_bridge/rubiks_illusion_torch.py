from __future__ import annotations

from typing import Dict, Iterable, Mapping

import numpy as np
import torch
from PIL import Image


def pil_to_tensor(image: Image.Image, *, device: torch.device | str | None = None) -> torch.Tensor:
    array = np.asarray(image.convert("RGB")).astype(np.float32) / 255.0
    tensor = torch.from_numpy(array).permute(2, 0, 1)
    if device is not None:
        tensor = tensor.to(device)
    return tensor


def tensor_to_pil(image: torch.Tensor) -> Image.Image:
    array = (image.detach().cpu().clamp(0.0, 1.0).permute(1, 2, 0).numpy() * 255.0).round().astype(np.uint8)
    return Image.fromarray(array)


def stack_source_face_tensors(
    source_faces: Mapping[str, Image.Image], face_order: Iterable[str], *, device: torch.device | str | None = None
) -> torch.Tensor:
    tensors = [pil_to_tensor(source_faces[face_id], device=device) for face_id in face_order]
    return torch.stack(tensors, dim=0)


def batch_to_pil_face_dict(batch: torch.Tensor, face_order: Iterable[str]) -> Dict[str, Image.Image]:
    return {face_id: tensor_to_pil(batch[index]) for index, face_id in enumerate(face_order)}


def clone_rendered_to_cpu(rendered: Mapping[str, Mapping[str, torch.Tensor]]) -> Dict[str, Dict[str, torch.Tensor]]:
    return {
        arrangement_name: {
            face_id: image.detach().cpu().clone()
            for face_id, image in face_images.items()
        }
        for arrangement_name, face_images in rendered.items()
    }


def rotate_tile_tensor(tile: torch.Tensor, quarter_turns: int) -> torch.Tensor:
    if quarter_turns not in {0, 1, 2, 3}:
        raise ValueError(f"Unsupported quarter turn count: {quarter_turns}")

    if quarter_turns == 0:
        return tile

    return torch.rot90(tile, k=(-quarter_turns) % 4, dims=(1, 2))


def render_face_grid_torch(
    grid: list[object],
    source_batch: torch.Tensor,
    face_to_index: Mapping[str, int],
    source_grid_size: int,
) -> torch.Tensor:
    _batch, _channels, image_height, image_width = source_batch.shape
    tile_height = image_height // source_grid_size
    tile_width = image_width // source_grid_size
    rows = []

    for row in grid:
        if not isinstance(row, list) or len(row) != source_grid_size:
            raise ValueError("Unexpected row shape in grid")

        tiles = []
        for cell in row:
            if not isinstance(cell, dict):
                raise ValueError("Unexpected cell type in grid")

            face_index = face_to_index[str(cell["sourceFace"])]
            top = int(cell["sourceRow"]) * tile_height
            left = int(cell["sourceCol"]) * tile_width
            tile = source_batch[face_index, :, top : top + tile_height, left : left + tile_width]
            tiles.append(rotate_tile_tensor(tile, int(cell["rotationQuarterTurns"])))

        rows.append(torch.cat(tiles, dim=2))

    return torch.cat(rows, dim=1)


def render_arrangement_torch(
    arrangement: Iterable[Mapping[str, object]],
    source_batch: torch.Tensor,
    face_to_index: Mapping[str, int],
    source_grid_size: int,
) -> Dict[str, torch.Tensor]:
    return {
        str(face_spec["face"]): render_face_grid_torch(
            face_spec["grid"],
            source_batch,
            face_to_index,
            source_grid_size,
        )
        for face_spec in arrangement
    }


def render_all_arrangements_torch(
    spec: Mapping[str, object],
    source_batch: torch.Tensor,
    face_to_index: Mapping[str, int],
) -> Dict[str, Dict[str, torch.Tensor]]:
    arrangements = spec["arrangements"]
    if not isinstance(arrangements, Mapping):
        raise ValueError("Spec arrangements must be a mapping")

    return {
        arrangement_name: render_arrangement_torch(
            arrangement,
            source_batch,
            face_to_index,
            int(spec["sourceGridSize"]),
        )
        for arrangement_name, arrangement in arrangements.items()
    }
