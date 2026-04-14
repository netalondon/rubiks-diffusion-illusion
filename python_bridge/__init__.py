from __future__ import annotations

_BASE_EXPORTS = [
    "FACE_FILE_NAMES",
    "load_source_faces",
    "load_spec",
    "render_all_arrangements",
    "render_arrangement",
    "render_face_grid",
    "save_contact_sheet",
    "save_rendered_faces",
]
_BASE_IMPORT_ERROR: ModuleNotFoundError | None = None

try:
    from .rubiks_illusion_operator import (
        FACE_FILE_NAMES,
        load_source_faces,
        load_spec,
        render_all_arrangements,
        render_arrangement,
        render_face_grid,
        save_contact_sheet,
        save_rendered_faces,
    )
except ModuleNotFoundError as error:
    _BASE_IMPORT_ERROR = error

_TORCH_EXPORTS = [
    "batch_to_pil_face_dict",
    "clone_rendered_to_cpu",
    "pil_to_tensor",
    "render_all_arrangements_torch",
    "render_arrangement_torch",
    "render_face_grid_torch",
    "rotate_tile_tensor",
    "stack_source_face_tensors",
    "tensor_to_pil",
]
_TORCH_IMPORT_ERROR: ModuleNotFoundError | None = None

try:
    from .rubiks_illusion_torch import (
        batch_to_pil_face_dict,
        clone_rendered_to_cpu,
        pil_to_tensor,
        render_all_arrangements_torch,
        render_arrangement_torch,
        render_face_grid_torch,
        rotate_tile_tensor,
        stack_source_face_tensors,
        tensor_to_pil,
    )
except ModuleNotFoundError as error:
    _TORCH_IMPORT_ERROR = error

__all__ = []
if _BASE_IMPORT_ERROR is None:
    __all__.extend(_BASE_EXPORTS)
if _TORCH_IMPORT_ERROR is None:
    __all__.extend(_TORCH_EXPORTS)


def __getattr__(name: str) -> object:
    if name in _BASE_EXPORTS and _BASE_IMPORT_ERROR is not None:
        raise ModuleNotFoundError(
            "The PIL-backed python_bridge helpers need their image dependencies installed. "
            "Install the project requirements first, then retry."
        ) from _BASE_IMPORT_ERROR
    if name in _TORCH_EXPORTS and _TORCH_IMPORT_ERROR is not None:
        raise ModuleNotFoundError(
            "The torch-backed python_bridge helpers need their numerical dependencies installed. "
            "Install the project requirements plus a machine-appropriate torch build first, then retry."
        ) from _TORCH_IMPORT_ERROR
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
