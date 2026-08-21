"""Visualization metadata helpers for the Three.js viewer mesh layer.

The repository does not currently contain an anatomical GLTF/GLB fly mesh.
These helpers therefore describe the viewer's explicitly labeled presentation
mesh and any real rollout channels available to it. No anatomical coordinates,
mesh vertices, or scientific body measurements are synthesized here.
"""

from __future__ import annotations

from typing import Any, Iterable


DEFAULT_VIEWER_BODY_PARTS = (
    "head",
    "thorax",
    "abdomen",
    "eyes",
    "antenna",
    "wings",
    "legs",
)

DEFAULT_BODY_HIERARCHY = (
    {"id": "fly", "parent": None, "children": ("thorax",), "role": "display_root"},
    {
        "id": "thorax",
        "parent": "fly",
        "children": (
            "head",
            "abdomen",
            "wing_L",
            "wing_R",
            "leg_FL",
            "leg_ML",
            "leg_HL",
            "leg_FR",
            "leg_MR",
            "leg_HR",
        ),
        "role": "display_body_segment",
    },
    {"id": "head", "parent": "thorax", "children": ("eye_L", "eye_R", "antenna_L", "antenna_R"), "role": "display_body_segment"},
    {"id": "abdomen", "parent": "thorax", "children": (), "role": "display_body_segment"},
    {"id": "wing_L", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "wing_R", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_FL", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_ML", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_HL", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_FR", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_MR", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "leg_HR", "parent": "thorax", "children": (), "role": "display_appendage"},
    {"id": "eye_L", "parent": "head", "children": (), "role": "display_detail"},
    {"id": "eye_R", "parent": "head", "children": (), "role": "display_detail"},
    {"id": "antenna_L", "parent": "head", "children": (), "role": "display_detail"},
    {"id": "antenna_R", "parent": "head", "children": (), "role": "display_detail"},
)

DEFAULT_DISPLAY_SEGMENTS = (
    {"id": "thorax", "label": "Thorax", "primitive": "ellipsoid", "material": "thorax"},
    {"id": "abdomen", "label": "Abdomen", "primitive": "ellipsoid", "material": "abdomen"},
    {"id": "head", "label": "Head", "primitive": "ellipsoid", "material": "head"},
    {"id": "wing_L", "label": "Left wing", "primitive": "transparent_wing", "material": "wing"},
    {"id": "wing_R", "label": "Right wing", "primitive": "transparent_wing", "material": "wing"},
    {"id": "leg_FL", "label": "Front left leg", "primitive": "segmented_cylinder", "material": "leg"},
    {"id": "leg_ML", "label": "Middle left leg", "primitive": "segmented_cylinder", "material": "leg"},
    {"id": "leg_HL", "label": "Hind left leg", "primitive": "segmented_cylinder", "material": "leg"},
    {"id": "leg_FR", "label": "Front right leg", "primitive": "segmented_cylinder", "material": "leg"},
    {"id": "leg_MR", "label": "Middle right leg", "primitive": "segmented_cylinder", "material": "leg"},
    {"id": "leg_HR", "label": "Hind right leg", "primitive": "segmented_cylinder", "material": "leg"},
)

DEFAULT_DISPLAY_MATERIALS = {
    "thorax": {"color": "#d08a53", "roughness": 0.82, "metalness": 0.02},
    "abdomen": {"color": "#7c5039", "roughness": 0.88, "metalness": 0.02},
    "head": {"color": "#c98c5f", "roughness": 0.8, "metalness": 0.02},
    "eye": {"color": "#23130f", "roughness": 0.45, "metalness": 0.0},
    "wing": {"color": "#bfe6f5", "roughness": 0.35, "metalness": 0.0, "opacity": 0.42},
    "leg": {"color": "#3d2c24", "roughness": 0.9, "metalness": 0.0},
    "antenna": {"color": "#4a2f25", "roughness": 0.86, "metalness": 0.0},
}


def build_visibility(
    *,
    has_joint_data: bool,
    has_com_data: bool,
    has_trajectory_data: bool = True,
) -> dict[str, bool]:
    """Describe renderable overlays based only on available source channels."""

    return {
        "mesh": True,
        "skeleton": bool(has_joint_data),
        "COM": bool(has_com_data),
        "trajectory": bool(has_trajectory_data),
    }


def build_mesh_metadata(
    *,
    joint_names: Iterable[str],
    visibility: dict[str, bool],
    body_segment_names: Iterable[str] = (),
) -> dict[str, Any]:
    """Return non-scientific display metadata for a viewer pose document."""

    body_segments = [str(name) for name in body_segment_names]
    return {
        "renderer": "web/viewer/digital_fly_mesh.js",
        "render_mode": "procedural_fallback",
        "scientific_mesh": False,
        "asset": None,
        "asset_status": "not_in_repository",
        "fallback_reason": (
            "No anatomical fly mesh asset is present in the repository. "
            "The viewer uses a presentation mesh driven by real rollout pose data."
        ),
        "body_parts": list(DEFAULT_VIEWER_BODY_PARTS),
        "body_segment_names": body_segments,
        "body_hierarchy": _json_ready(DEFAULT_BODY_HIERARCHY),
        "segments": _json_ready(DEFAULT_DISPLAY_SEGMENTS),
        "mesh_instances": [
            {
                "id": f"{segment['id']}_mesh",
                "segment": segment["id"],
                "source": "procedural_fallback",
                "scientific_mesh": False,
            }
            for segment in DEFAULT_DISPLAY_SEGMENTS
        ],
        "bones": [
            {"id": item["id"], "parent": item["parent"], "source": "display_hierarchy"}
            for item in DEFAULT_BODY_HIERARCHY
            if item["parent"] is not None
        ],
        "materials": _json_ready(DEFAULT_DISPLAY_MATERIALS),
        "joint_names": [str(name) for name in joint_names],
        "visibility": dict(visibility),
        "scientific_scope": (
            "Display metadata only. This is not an anatomical mesh export and "
            "does not add biological measurements."
        ),
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = ["DEFAULT_VIEWER_BODY_PARTS", "build_mesh_metadata", "build_visibility"]
