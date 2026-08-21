"""Explicit perturbation interfaces for paired simulation experiments."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import yaml


@dataclass(frozen=True)
class ControllerPerturbationContext:
    """Context available before a controller is used for a rollout."""

    condition_id: str
    timestep_s: float
    random_seed: int
    expected_joint_angle_count: int


@dataclass(frozen=True)
class ActionPerturbationContext:
    """Context available when transforming one controller action."""

    condition_id: str
    step_index: int
    time_s: float
    timestep_s: float
    random_seed: int
    expected_joint_angle_count: int


class Perturbation(Protocol):
    """Small protocol implemented by deterministic perturbations."""

    @property
    def perturbation_type(self) -> str:
        """Stable machine-readable perturbation type."""

    @property
    def name(self) -> str:
        """Stable run/config name."""

    def apply_to_config(self, config: Any) -> Any:
        """Return the config used for the perturbed condition."""

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        """Return the controller used for the perturbed condition."""

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        """Return the action sent to the simulation."""

    def metadata(self) -> dict[str, Any]:
        """Return JSON-serializable perturbation metadata."""


@dataclass(frozen=True)
class IdentityPerturbation:
    """A perturbation that deliberately changes no simulation command."""

    name: str = "identity"
    config_id: str | None = None

    @property
    def perturbation_type(self) -> str:
        return "identity"

    def apply_to_config(self, config: Any) -> Any:
        return config

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        return controller

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        _validate_joint_angles(action.joint_angles, context.expected_joint_angle_count)
        return _copy_action(action)

    def metadata(self) -> dict[str, Any]:
        return {
            "type": self.perturbation_type,
            "name": self.name,
            "config_id": self.config_id,
            "parameters": {},
            "intervention_target": "none",
            "intervention_stage": "none",
            "deterministic": True,
            "description": (
                "Identity validation perturbation. It must not change controller "
                "commands, adhesion commands, configuration, or controller state."
            ),
        }


NoOpPerturbation = IdentityPerturbation


@dataclass(frozen=True)
class GlobalActionScalePerturbation:
    """Scale only joint-angle commands after controller output."""

    scale: float = 0.8
    name: str = "action_scale_080"
    config_id: str | None = None

    def __post_init__(self) -> None:
        scale = float(self.scale)
        if not np.isfinite(scale) or scale < 0:
            raise ValueError("global_action_scale.scale must be finite and non-negative.")
        object.__setattr__(self, "scale", scale)

    @property
    def perturbation_type(self) -> str:
        return "global_action_scale"

    def apply_to_config(self, config: Any) -> Any:
        return config

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        return controller

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        joint_angles = _validate_joint_angles(
            action.joint_angles, context.expected_joint_angle_count
        )
        return _copy_action(action, joint_angles=joint_angles * self.scale)

    def metadata(self) -> dict[str, Any]:
        return {
            "type": self.perturbation_type,
            "name": self.name,
            "config_id": self.config_id,
            "parameters": {"scale": self.scale},
            "intervention_target": "controller_joint_angle_commands",
            "intervention_stage": "post_controller_pre_simulation_action",
            "deterministic": True,
            "description": (
                "Generic motor-command perturbation that scales the joint-angle "
                "portion of each controller action. Adhesion commands are not scaled."
            ),
        }


@dataclass(frozen=True)
class CPGCouplingScalePerturbation:
    """Scale CPG inter-leg coupling weights before rollout."""

    scale: float = 1.0
    name: str = "cpg_coupling_scale_100"
    config_id: str | None = None

    def __post_init__(self) -> None:
        scale = float(self.scale)
        if not np.isfinite(scale) or scale < 0:
            raise ValueError("cpg_coupling_scale.scale must be finite and non-negative.")
        object.__setattr__(self, "scale", scale)

    @property
    def perturbation_type(self) -> str:
        return "cpg_coupling_scale"

    def apply_to_config(self, config: Any) -> Any:
        return config

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        cpg_network = getattr(controller, "cpg_network", None)
        if cpg_network is None or not hasattr(cpg_network, "coupling_weights"):
            raise ValueError("Controller does not expose cpg_network.coupling_weights.")
        coupling_weights = np.asarray(cpg_network.coupling_weights, dtype=float)
        if coupling_weights.ndim != 2 or coupling_weights.shape[0] != coupling_weights.shape[1]:
            raise ValueError("CPG coupling_weights must be a square matrix.")
        cpg_network.coupling_weights = coupling_weights.copy() * self.scale
        return controller

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        _validate_joint_angles(action.joint_angles, context.expected_joint_angle_count)
        return _copy_action(action)

    def metadata(self) -> dict[str, Any]:
        return {
            "type": self.perturbation_type,
            "name": self.name,
            "config_id": self.config_id,
            "parameters": {
                "scale": self.scale,
                "baseline_equivalent_scale": 1.0,
            },
            "intervention_target": "cpg_network.coupling_weights",
            "intervention_stage": "post_controller_construction_pre_rollout",
            "deterministic": True,
            "description": (
                "Generic coordination proxy that scales FlyGym CPG inter-leg "
                "coupling weights. It does not change intrinsic frequency, "
                "intrinsic amplitude, action scaling, actuator gains, or adhesion."
            ),
        }


@dataclass(frozen=True)
class CompositePerturbation:
    """Apply multiple perturbations in a declared, ordered sequence."""

    components: tuple[Perturbation, ...]
    name: str = "composite"
    config_id: str | None = None

    def __post_init__(self) -> None:
        components = tuple(self.components)
        if not components:
            raise ValueError("CompositePerturbation requires at least one component.")
        object.__setattr__(self, "components", components)

    @property
    def perturbation_type(self) -> str:
        return "composite"

    def apply_to_config(self, config: Any) -> Any:
        transformed = config
        for component in self.components:
            transformed = component.apply_to_config(transformed)
        return transformed

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        transformed = controller
        for component in self.components:
            transformed = component.apply_to_controller(transformed, context)
        return transformed

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        transformed = action
        for component in self.components:
            transformed = component.apply_to_action(transformed, context)
        return transformed

    def metadata(self) -> dict[str, Any]:
        component_metadata = [component.metadata() for component in self.components]
        return {
            "type": self.perturbation_type,
            "name": self.name,
            "config_id": self.config_id,
            "parameters": {
                "component_count": len(component_metadata),
                "order": [
                    {
                        "index": index,
                        "type": metadata["type"],
                        "name": metadata["name"],
                        "intervention_stage": metadata["intervention_stage"],
                        "intervention_target": metadata["intervention_target"],
                    }
                    for index, metadata in enumerate(component_metadata)
                ],
            },
            "components": component_metadata,
            "intervention_target": "ordered_composite",
            "intervention_stage": "ordered_config_controller_action_pipeline",
            "deterministic": all(
                metadata.get("deterministic") is True
                for metadata in component_metadata
            ),
            "description": (
                "Ordered composition of deterministic perturbations. Component "
                "metadata is preserved separately so controller-stage and "
                "action-stage transformations remain independently auditable."
            ),
        }


def load_perturbation_config(path: str | Path) -> Perturbation:
    """Load a perturbation from a YAML config file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Perturbation configuration root must be a mapping.")
    return perturbation_from_mapping(loaded)


def perturbation_from_mapping(data: dict[str, Any]) -> Perturbation:
    """Build a supported perturbation from a mapping."""

    values = _normalise_perturbation_mapping(data)
    perturbation_type = str(values.get("type", "identity")).strip().lower()
    name = str(values.get("name", perturbation_type)).strip()
    if not name:
        raise ValueError("Perturbation name must be a non-empty string.")
    config_id = values.get("experiment_id") or values.get("config_id")
    config_id = str(config_id) if config_id is not None else None

    if perturbation_type in {"identity", "noop", "no_op"}:
        return IdentityPerturbation(name=name, config_id=config_id)
    if perturbation_type == "global_action_scale":
        if "scale" not in values:
            raise ValueError("global_action_scale perturbation requires scale.")
        return GlobalActionScalePerturbation(
            scale=float(values["scale"]),
            name=name,
            config_id=config_id,
        )
    if perturbation_type == "cpg_coupling_scale":
        if "scale" not in values:
            raise ValueError("cpg_coupling_scale perturbation requires scale.")
        return CPGCouplingScalePerturbation(
            scale=float(values["scale"]),
            name=name,
            config_id=config_id,
        )
    if perturbation_type == "composite":
        raw_components = values.get("components")
        if not isinstance(raw_components, list) or not raw_components:
            raise ValueError("composite perturbation requires non-empty components.")
        components = tuple(
            perturbation_from_mapping(component)
            for component in raw_components
            if isinstance(component, dict)
        )
        if len(components) != len(raw_components):
            raise ValueError("composite perturbation components must be mappings.")
        return CompositePerturbation(
            components=components,
            name=name,
            config_id=config_id,
        )
    if perturbation_type == "brain_driven":
        from .brain_driven import BrainDrivenPerturbation

        motor_scale = float(values.get("motor_scale", 1.0))
        coupling_scale = float(values.get("coupling_scale", 1.0))
        scales_json_path = values.get("scales_json_path")
        model = str(values.get("model", "unknown"))
        if scales_json_path:
            return BrainDrivenPerturbation.from_json(
                scales_json_path,
                name=name,
                config_id=config_id,
            )
        return BrainDrivenPerturbation(
            motor_scale=motor_scale,
            coupling_scale=coupling_scale,
            scales_json_path=None,
            name=name,
            config_id=config_id,
            model=model,
        )
    raise ValueError(f"Unsupported perturbation type: {perturbation_type}")


def perturbation_metadata_complete(metadata: dict[str, Any]) -> bool:
    """Return whether required metadata fields are present and usable."""

    required = (
        "type",
        "name",
        "parameters",
        "intervention_target",
        "intervention_stage",
        "deterministic",
    )
    if any(key not in metadata for key in required):
        return False
    base_complete = (
        isinstance(metadata["type"], str)
        and bool(metadata["type"].strip())
        and isinstance(metadata["name"], str)
        and bool(metadata["name"].strip())
        and isinstance(metadata["parameters"], dict)
        and isinstance(metadata["intervention_target"], str)
        and bool(metadata["intervention_target"].strip())
        and isinstance(metadata["intervention_stage"], str)
        and bool(metadata["intervention_stage"].strip())
        and metadata["deterministic"] is True
    )
    if not base_complete:
        return False
    if metadata["type"] != "composite":
        return True
    components = metadata.get("components")
    return (
        isinstance(components, list)
        and bool(components)
        and all(
            isinstance(component, dict) and perturbation_metadata_complete(component)
            for component in components
        )
    )


def _normalise_perturbation_mapping(data: dict[str, Any]) -> dict[str, Any]:
    root = dict(data)
    if isinstance(root.get("perturbation"), dict):
        nested = dict(root["perturbation"])
        for key in ("experiment_id", "config_id", "name"):
            if key in root and key not in nested:
                nested[key] = root[key]
        return nested
    return root


def _validate_joint_angles(values: Any, expected_count: int) -> np.ndarray:
    joint_angles = np.asarray(values, dtype=float)
    if joint_angles.ndim != 1:
        raise ValueError("Locomotion joint-angle commands must be one-dimensional.")
    if int(expected_count) > 0 and joint_angles.shape[0] != int(expected_count):
        raise ValueError(
            "Locomotion joint-angle command count does not match expected count."
        )
    if not np.isfinite(joint_angles).all():
        raise ValueError("Locomotion joint-angle commands must be finite.")
    return joint_angles


_UNCHANGED = object()


def _copy_action(
    action: Any,
    *,
    joint_angles: Any | None = None,
    adhesion_onoff: Any = _UNCHANGED,
) -> Any:
    action_type = type(action)
    copied_joint_angles = (
        np.asarray(action.joint_angles, dtype=float).copy()
        if joint_angles is None
        else np.asarray(joint_angles, dtype=float).copy()
    )
    if adhesion_onoff is _UNCHANGED:
        source_adhesion = action.adhesion_onoff
    else:
        source_adhesion = adhesion_onoff
    copied_adhesion = (
        None
        if source_adhesion is None
        else np.asarray(source_adhesion, dtype=bool).copy()
    )
    return action_type(
        joint_angles=copied_joint_angles,
        adhesion_onoff=copied_adhesion,
    )


__all__ = [
    "ActionPerturbationContext",
    "CPGCouplingScalePerturbation",
    "CompositePerturbation",
    "ControllerPerturbationContext",
    "GlobalActionScalePerturbation",
    "IdentityPerturbation",
    "NoOpPerturbation",
    "Perturbation",
    "load_perturbation_config",
    "perturbation_from_mapping",
    "perturbation_metadata_complete",
]
