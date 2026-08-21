"""Controller helpers for the unperturbed locomotion baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CPGControllerConfig:
    """Configuration for FlyGym's official tripod CPG walking controller."""

    controller_type: str = "official_flygym_cpg_tripod"
    intrinsic_frequency_hz: float = 12.0
    intrinsic_amplitude: float = 1.0
    coupling_strength: float = 10.0
    convergence_coef: float = 20.0

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "CPGControllerConfig":
        values = dict(data or {})
        config = cls(
            controller_type=str(values.get("type", cls.controller_type)),
            intrinsic_frequency_hz=float(
                values.get("intrinsic_frequency_hz", cls.intrinsic_frequency_hz)
            ),
            intrinsic_amplitude=float(
                values.get("intrinsic_amplitude", cls.intrinsic_amplitude)
            ),
            coupling_strength=float(
                values.get("coupling_strength", cls.coupling_strength)
            ),
            convergence_coef=float(values.get("convergence_coef", cls.convergence_coef)),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.controller_type != "official_flygym_cpg_tripod":
            raise ValueError(
                "Only the official FlyGym tripod CPG controller is supported for "
                "Milestone C."
            )
        _require_positive("intrinsic_frequency_hz", self.intrinsic_frequency_hz)
        _require_positive("intrinsic_amplitude", self.intrinsic_amplitude)
        _require_positive("coupling_strength", self.coupling_strength)
        _require_positive("convergence_coef", self.convergence_coef)

    def to_report(self) -> dict[str, Any]:
        return {
            "type": self.controller_type,
            "official_source": "flygym_demo.complex_terrain.CPGController",
            "preprogrammed_steps_source": (
                "flygym_demo.complex_terrain.PreprogrammedSteps"
            ),
            "gait": "tripod",
            "intrinsic_frequency_hz": self.intrinsic_frequency_hz,
            "intrinsic_amplitude": self.intrinsic_amplitude,
            "coupling_strength": self.coupling_strength,
            "convergence_coef": self.convergence_coef,
        }


def build_official_cpg_controller(
    *,
    timestep: float,
    random_seed: int,
    output_dof_order: list[Any],
    config: CPGControllerConfig,
) -> tuple[Any, Any]:
    """Instantiate FlyGym's official CPG controller and preprogrammed steps."""

    from flygym_demo.complex_terrain import (  # noqa: PLC0415
        CPGController,
        PreprogrammedSteps,
        make_tripod_cpg_network,
    )

    preprogrammed_steps = PreprogrammedSteps()
    cpg_network = make_tripod_cpg_network(
        timestep=timestep,
        intrinsic_frequency=config.intrinsic_frequency_hz,
        intrinsic_amplitude=config.intrinsic_amplitude,
        coupling_strength=config.coupling_strength,
        convergence_coef=config.convergence_coef,
        seed=random_seed,
    )
    controller = CPGController(
        cpg_network=cpg_network,
        preprogrammed_steps=preprogrammed_steps,
        output_dof_order=output_dof_order,
    )
    return controller, preprogrammed_steps


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


__all__ = [
    "CPGControllerConfig",
    "build_official_cpg_controller",
]
