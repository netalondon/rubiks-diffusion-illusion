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
    if error.name != "torch":
        raise
    _TORCH_IMPORT_ERROR = error

__all__ = [
    "FACE_FILE_NAMES",
    "load_source_faces",
    "load_spec",
    "render_all_arrangements",
    "render_arrangement",
    "render_face_grid",
    "save_contact_sheet",
    "save_rendered_faces",
]

if _TORCH_IMPORT_ERROR is None:
    __all__.extend(_TORCH_EXPORTS)


def __getattr__(name: str) -> object:
    if name in _TORCH_EXPORTS and _TORCH_IMPORT_ERROR is not None:
        raise ModuleNotFoundError(
            "The torch-backed python_bridge helpers require PyTorch to be installed. "
            "Install a machine-appropriate torch build first, then retry."
        ) from _TORCH_IMPORT_ERROR
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
