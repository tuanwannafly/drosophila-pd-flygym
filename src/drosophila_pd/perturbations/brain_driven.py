"""Brain-driven perturbation: DN spike rates -> CPG scale -> NeuroMechFly action.

Gap 3 bridge consumer. Reads a bridge_scales.json produced by
fly-brain/code/brain_body_bridge.py and applies two sub-perturbations:

- GlobalActionScalePerturbation(motor_scale) on joint-angle commands
- CPGCouplingScalePerturbation(coupling_scale) on CPG coupling weights

This composes the brain-side output (forward/turn DN rate ratios) into the
body-side perturbation framework. It is a computational bridge, not a
biological mapping.

Usage:
    perturbation = BrainDrivenPerturbation(
        scales_json_path=Path("bridge_scales.json"),
    )
    run_locomotion(config, perturbation=perturbation)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .base import (
    ActionPerturbationContext,
    CPGCouplingScalePerturbation,
    ControllerPerturbationContext,
    GlobalActionScalePerturbation,
    Perturbation,
    _copy_action,
    _validate_joint_angles,
)


@dataclass(frozen=True)
class BrainDrivenPerturbation:
    """Composite perturbation driven by brain-side DN spike rate ratios.

    Reads motor_scale and coupling_scale from a bridge_scales.json file.
    Internally delegates to GlobalActionScalePerturbation (action stage) and
    CPGCouplingScalePerturbation (controller stage).
    """

    motor_scale: float = 1.0
    coupling_scale: float = 1.0
    scales_json_path: Path | None = None
    name: str = "brain_driven"
    config_id: str | None = None
    model: str = "unknown"

    def __post_init__(self) -> None:
        motor_scale = float(self.motor_scale)
        coupling_scale = float(self.coupling_scale)
        if motor_scale < 0 or coupling_scale < 0:
            raise ValueError("motor_scale and coupling_scale must be non-negative.")
        object.__setattr__(self, "motor_scale", motor_scale)
        object.__setattr__(self, "coupling_scale", coupling_scale)
        if self.scales_json_path is not None:
            object.__setattr__(
                self, "scales_json_path", Path(self.scales_json_path)
            )

    @classmethod
    def from_json(cls, scales_json_path: str | Path, **kwargs: Any) -> "BrainDrivenPerturbation":
        """Load scales from a bridge_scales.json file."""
        path = Path(scales_json_path)
        if not path.is_file():
            raise FileNotFoundError(f"Bridge scales JSON not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            motor_scale=float(data.get("motor_scale", 1.0)),
            coupling_scale=float(data.get("coupling_scale", 1.0)),
            scales_json_path=path,
            model=str(data.get("model", "unknown")),
            name=kwargs.pop("name", f"brain_driven_{data.get('model', 'unknown')}"),
            config_id=kwargs.pop("config_id", None),
            **kwargs,
        )

    @property
    def perturbation_type(self) -> str:
        return "brain_driven"

    @property
    def _action_perturbation(self) -> GlobalActionScalePerturbation:
        return GlobalActionScalePerturbation(
            scale=self.motor_scale,
            name=f"{self.name}_motor",
            config_id=self.config_id,
        )

    @property
    def _controller_perturbation(self) -> CPGCouplingScalePerturbation:
        return CPGCouplingScalePerturbation(
            scale=self.coupling_scale,
            name=f"{self.name}_coupling",
            config_id=self.config_id,
        )

    def apply_to_config(self, config: Any) -> Any:
        return config

    def apply_to_controller(
        self, controller: Any, context: ControllerPerturbationContext
    ) -> Any:
        return self._controller_perturbation.apply_to_controller(controller, context)

    def apply_to_action(self, action: Any, context: ActionPerturbationContext) -> Any:
        return self._action_perturbation.apply_to_action(action, context)

    def metadata(self) -> dict[str, Any]:
        return {
            "type": "composite",
            "name": self.name,
            "config_id": self.config_id,
            "parameters": {
                "motor_scale": self.motor_scale,
                "coupling_scale": self.coupling_scale,
                "model": self.model,
                "scales_json_path": str(self.scales_json_path) if self.scales_json_path else None,
            },
            "intervention_target": "brain_driven_motor_and_coordination",
            "intervention_stage": "controller_and_action_composite",
            "deterministic": True,
            "description": (
                "Brain-driven composite perturbation. motor_scale scales joint-angle "
                "commands (from forward DN rate ratio); coupling_scale scales CPG "
                "inter-leg coupling weights (from turn DN rate ratio). Scales are "
                "derived from brain-side LIF simulation DN spike rates, not from "
                "biological dopamine or neuron-loss measurements."
            ),
            "source": "bridge_scales.json from fly-brain brain_body_bridge.py",
            "components": [
                {
                    "type": "global_action_scale",
                    "name": f"{self.name}_motor",
                    "parameters": {"scale": self.motor_scale},
                    "intervention_target": "joint_angle_amplitude",
                    "intervention_stage": "action",
                    "deterministic": True,
                    "description": "Scales joint-angle commands by motor_scale (forward DN rate ratio).",
                },
                {
                    "type": "cpg_coupling_scale",
                    "name": f"{self.name}_coupling",
                    "parameters": {"scale": self.coupling_scale},
                    "intervention_target": "cpg_inter_leg_coupling",
                    "intervention_stage": "controller",
                    "deterministic": True,
                    "description": "Scales CPG inter-leg coupling weights by coupling_scale (turn DN rate ratio).",
                },
            ],
        }


__all__ = ["BrainDrivenPerturbation"]
