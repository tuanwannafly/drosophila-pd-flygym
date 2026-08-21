"""Read-only observation recorder for FlyGym 2.1.0 simulations."""

from __future__ import annotations

from typing import Any, Callable

import numpy as np

from .types import ObservationFrame, RolloutData


class RolloutRecorder:
    """Capture observations through FlyGym's public Simulation getters.

    The recorder never creates observations or mutates the simulation. COM is
    read from MuJoCo's subtree COM when the supplied fly and MuJoCo mapping are
    available; callers may provide an explicit ``com_provider`` for a supported
    model-specific source.
    """

    def __init__(
        self,
        simulation: Any,
        fly_name: str,
        *,
        fly: Any | None = None,
        timestep: float | None = None,
        camera_metadata: dict[str, Any] | None = None,
        simulation_metadata: dict[str, Any] | None = None,
        com_provider: Callable[[Any, Any | None], Any] | None = None,
    ) -> None:
        self._previous_orientation: np.ndarray | None = None
        self.simulation = simulation
        self.fly_name = fly_name
        self.fly = fly
        self.timestep = float(timestep or self._simulation_timestep())
        self.camera_metadata = dict(camera_metadata or {})
        self.simulation_metadata = dict(simulation_metadata or {})
        self.com_provider = com_provider
        self.rollout = RolloutData(
            metadata={
                "fly_name": fly_name,
                "timestep_s": self.timestep,
                "camera": self.camera_metadata,
                "simulation": self.simulation_metadata,
                "quaternion_order": "wxyz",
                "body_segment_names": self._body_segment_names(),
            }
        )
        self._previous_joint_velocity: np.ndarray | None = None

    def _simulation_timestep(self) -> float:
        return float(getattr(getattr(getattr(self.simulation, "mj_model", None), "opt", None), "timestep", 0.0))

    def reset(self) -> None:
        self.rollout.frames.clear()
        self._previous_joint_velocity = None
        self._previous_orientation = None

    def record(self) -> ObservationFrame:
        """Capture one frame from the current simulation state."""

        body_positions = self._copy_getter("get_body_positions")
        body_orientations = self._copy_getter("get_body_rotations")
        joint_positions = self._copy_getter("get_joint_angles")
        joint_velocity = self._copy_getter("get_joint_velocities")
        joint_acceleration = None
        if joint_velocity is not None:
            if self._previous_joint_velocity is not None:
                joint_acceleration = (joint_velocity - self._previous_joint_velocity) / self.timestep
            else:
                joint_acceleration = np.zeros_like(joint_velocity)
            self._previous_joint_velocity = joint_velocity.copy()

        orientation = self._thorax_orientation(body_orientations)
        orientation = self._sanitize_orientation(orientation)

        frame = ObservationFrame(
            timestamp_s=self._timestamp(),
            step=len(self.rollout.frames),
            thorax=self._thorax(body_positions),
            com=self._com(),
            orientation=orientation,
            body_positions=body_positions,
            body_orientations=body_orientations,
            joint_positions=joint_positions,
            joint_velocity=joint_velocity,
            joint_acceleration=joint_acceleration,
            contact=self._contact(),
            actuator=self._actuator(),
        )
        self.rollout.frames.append(frame)
        return frame

    def _timestamp(self) -> float:
        data = getattr(self.simulation, "mj_data", None)
        return float(getattr(data, "time", len(self.rollout.frames) * self.timestep))

    def _copy_getter(self, name: str) -> np.ndarray | None:
        getter = getattr(self.simulation, name, None)
        if getter is None:
            return None
        try:
            return np.asarray(getter(self.fly_name), dtype=float).copy()
        except (KeyError, IndexError, TypeError, ValueError):
            return None

    def _thorax(self, positions: np.ndarray | None) -> np.ndarray | None:
        if positions is None or len(positions) == 0:
            return None
        index = self._body_index("c_thorax")
        return positions[index if index is not None else 0].copy()

    def _thorax_orientation(self, orientations: np.ndarray | None) -> np.ndarray | None:
        if orientations is None or len(orientations) == 0:
            return None
        index = self._body_index("c_thorax")
        return orientations[index if index is not None else 0].copy()

    def _sanitize_orientation(self, orientation: np.ndarray | None) -> np.ndarray | None:
        if orientation is None:
            return None

        candidate = np.asarray(orientation, dtype=float)
        norm = float(np.linalg.norm(candidate)) if candidate.shape == (4,) else 0.0
        valid = (
            candidate.shape == (4,)
            and np.isfinite(candidate).all()
            and np.isfinite(norm)
            and norm > 0.0
        )
        if not valid:
            candidate = (
                self._previous_orientation.copy()
                if self._previous_orientation is not None
                else np.array([1.0, 0.0, 0.0, 0.0], dtype=float)
            )
        else:
            candidate = candidate / norm

        self._previous_orientation = candidate.copy()
        return candidate

    def _body_index(self, name: str) -> int | None:
        if self.fly is None or not hasattr(self.fly, "get_bodysegs_order"):
            return None
        for index, segment in enumerate(self.fly.get_bodysegs_order()):
            if getattr(segment, "name", str(segment)) == name or str(segment) == name:
                return index
        return None

    def _body_segment_names(self) -> list[str]:
        if self.fly is None or not hasattr(self.fly, "get_bodysegs_order"):
            return []
        return [
            str(getattr(segment, "name", str(segment)))
            for segment in self.fly.get_bodysegs_order()
        ]

    def _com(self) -> np.ndarray | None:
        if self.com_provider is not None:
            value = self.com_provider(self.simulation, self.fly)
            return None if value is None else np.asarray(value, dtype=float).copy()
        data = getattr(self.simulation, "mj_data", None)
        if data is None or not hasattr(data, "subtree_com") or self.fly is None:
            return None
        try:
            import mujoco

            body_element = next(
                element
                for segment, element in self.fly.bodyseg_to_mjcfbody.items()
                if getattr(segment, "name", str(segment)) == "c_thorax"
            )
            body_id = mujoco.mj_name2id(
                self.simulation.mj_model,
                mujoco.mjtObj.mjOBJ_BODY,
                body_element.name,
            )
            return np.asarray(data.subtree_com[body_id], dtype=float).copy()
        except (ImportError, AttributeError, KeyError, StopIteration, TypeError, ValueError):
            return None

    def _contact(self) -> dict[str, Any] | None:
        getter = getattr(self.simulation, "get_ground_contact_info", None)
        if getter is None:
            return None
        try:
            found, forces, torques, positions, normals, tangents = getter(self.fly_name)
        except (KeyError, IndexError, TypeError, ValueError):
            return None
        return {
            "found": np.asarray(found, dtype=float).copy(),
            "forces": np.asarray(forces, dtype=float).copy(),
            "torques": np.asarray(torques, dtype=float).copy(),
            "positions": np.asarray(positions, dtype=float).copy(),
            "normals": np.asarray(normals, dtype=float).copy(),
            "tangents": np.asarray(tangents, dtype=float).copy(),
        }

    def _actuator(self) -> dict[str, Any]:
        getter = getattr(self.simulation, "get_actuator_forces", None)
        if getter is None:
            return {}
        try:
            from flygym.compose import ActuatorType
        except ModuleNotFoundError:
            return {}
        values: dict[str, Any] = {}
        for actuator_type in (ActuatorType.POSITION, ActuatorType.ADHESION):
            try:
                values[actuator_type.value] = np.asarray(
                    getter(self.fly_name, actuator_type), dtype=float
                ).copy()
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        return values


__all__ = ["RolloutRecorder"]
