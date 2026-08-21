from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.perturbations import (  # noqa: E402
    ActionPerturbationContext,
    CPGCouplingScalePerturbation,
    CompositePerturbation,
    ControllerPerturbationContext,
    GlobalActionScalePerturbation,
    IdentityPerturbation,
    load_perturbation_config,
    perturbation_from_mapping,
    perturbation_metadata_complete,
    summarize_action_transformation,
    summarize_controller_transformation,
)


@dataclass
class FakeAction:
    joint_angles: np.ndarray
    adhesion_onoff: np.ndarray | None = None


@dataclass
class FakeCPGNetwork:
    coupling_weights: np.ndarray


@dataclass
class FakeController:
    cpg_network: FakeCPGNetwork


def test_identity_config_parses_and_records_complete_metadata():
    perturbation = load_perturbation_config(
        REPO_ROOT / "configs" / "experiments" / "perturbations" / "identity.yaml"
    )

    assert isinstance(perturbation, IdentityPerturbation)
    assert perturbation.perturbation_type == "identity"
    assert perturbation_metadata_complete(perturbation.metadata())


def test_action_scale_config_parses_scale():
    perturbation = load_perturbation_config(
        REPO_ROOT
        / "configs"
        / "experiments"
        / "perturbations"
        / "action_scale_080.yaml"
    )

    assert isinstance(perturbation, GlobalActionScalePerturbation)
    assert perturbation.scale == 0.8
    assert perturbation.metadata()["intervention_target"] == (
        "controller_joint_angle_commands"
    )


def test_cpg_coupling_scale_transforms_controller_weights_only():
    controller = FakeController(
        cpg_network=FakeCPGNetwork(coupling_weights=np.array([[0.0, 10.0], [10.0, 0.0]]))
    )

    transformed = CPGCouplingScalePerturbation(scale=0.5).apply_to_controller(
        controller, _controller_context()
    )

    assert transformed is controller
    assert np.array_equal(
        transformed.cpg_network.coupling_weights,
        np.array([[0.0, 5.0], [5.0, 0.0]]),
    )


def test_cpg_coupling_scale_metadata_marks_coordination_target():
    perturbation = CPGCouplingScalePerturbation(scale=1.0)

    assert perturbation.metadata()["parameters"]["baseline_equivalent_scale"] == 1.0
    assert perturbation.metadata()["intervention_target"] == "cpg_network.coupling_weights"
    assert perturbation_metadata_complete(perturbation.metadata())


def test_identity_action_transformation_preserves_values():
    action = FakeAction(
        joint_angles=np.array([0.1, -0.2, 0.3]),
        adhesion_onoff=np.array([True, False, True, False, True, False]),
    )

    transformed = IdentityPerturbation().apply_to_action(
        action, _context(expected_joint_angle_count=3)
    )

    assert np.array_equal(transformed.joint_angles, action.joint_angles)
    assert np.array_equal(transformed.adhesion_onoff, action.adhesion_onoff)


def test_global_action_scale_scales_joint_angles_only():
    action = FakeAction(
        joint_angles=np.array([1.0, -2.0, 3.0]),
        adhesion_onoff=np.array([True, False, True, False, True, False]),
    )

    transformed = GlobalActionScalePerturbation(scale=0.8).apply_to_action(
        action, _context(expected_joint_angle_count=3)
    )

    assert np.allclose(transformed.joint_angles, np.array([0.8, -1.6, 2.4]))
    assert np.array_equal(transformed.adhesion_onoff, action.adhesion_onoff)


def test_global_action_scale_is_deterministic():
    action = FakeAction(
        joint_angles=np.linspace(-1.0, 1.0, 42),
        adhesion_onoff=np.array([True, False, True, False, True, False]),
    )
    perturbation = GlobalActionScalePerturbation(scale=0.8)

    first = perturbation.apply_to_action(action, _context())
    second = perturbation.apply_to_action(action, _context())

    assert np.array_equal(first.joint_angles, second.joint_angles)
    assert np.array_equal(first.adhesion_onoff, second.adhesion_onoff)


def test_invalid_scale_values_are_rejected():
    with pytest.raises(ValueError, match="finite and non-negative"):
        GlobalActionScalePerturbation(scale=-0.1)
    with pytest.raises(ValueError, match="finite and non-negative"):
        GlobalActionScalePerturbation(scale=float("nan"))
    with pytest.raises(ValueError, match="finite and non-negative"):
        CPGCouplingScalePerturbation(scale=-0.1)


def test_action_dimension_mismatch_is_rejected():
    action = FakeAction(joint_angles=np.zeros(41))

    with pytest.raises(ValueError, match="expected count"):
        GlobalActionScalePerturbation(scale=0.8).apply_to_action(action, _context())


def test_nested_perturbation_mapping_is_supported():
    perturbation = perturbation_from_mapping(
        {
            "experiment_id": "nested_config",
            "perturbation": {
                "type": "global_action_scale",
                "name": "nested_scale",
                "scale": 0.5,
            },
        }
    )

    assert isinstance(perturbation, GlobalActionScalePerturbation)
    assert perturbation.config_id == "nested_config"


def test_composite_perturbation_parses_and_preserves_component_metadata():
    perturbation = perturbation_from_mapping(
        {
            "experiment_id": "milestone_e2_unit",
            "type": "composite",
            "name": "combined_motor_080_coupling_075",
            "components": [
                {
                    "type": "cpg_coupling_scale",
                    "name": "coordination_proxy",
                    "scale": 0.75,
                },
                {
                    "type": "global_action_scale",
                    "name": "motor_vigor_proxy",
                    "scale": 0.8,
                },
            ],
        }
    )

    metadata = perturbation.metadata()

    assert isinstance(perturbation, CompositePerturbation)
    assert perturbation_metadata_complete(metadata)
    assert metadata["parameters"]["component_count"] == 2
    assert [item["type"] for item in metadata["components"]] == [
        "cpg_coupling_scale",
        "global_action_scale",
    ]
    assert [item["type"] for item in metadata["parameters"]["order"]] == [
        "cpg_coupling_scale",
        "global_action_scale",
    ]


def test_composite_independently_transforms_controller_and_action():
    perturbation = CompositePerturbation(
        components=(
            CPGCouplingScalePerturbation(scale=0.5, name="coordination_proxy"),
            GlobalActionScalePerturbation(scale=0.8, name="motor_vigor_proxy"),
        ),
        name="combined",
    )
    controller = FakeController(
        cpg_network=FakeCPGNetwork(coupling_weights=np.array([[0.0, 10.0], [2.0, 0.0]]))
    )
    action = FakeAction(
        joint_angles=np.array([1.0, -2.0, 3.0]),
        adhesion_onoff=np.array([True, False, True, False, True, False]),
    )

    transformed_controller = perturbation.apply_to_controller(
        controller, _controller_context()
    )
    transformed_action = perturbation.apply_to_action(
        action, _context(expected_joint_angle_count=3)
    )

    assert transformed_controller is controller
    assert np.allclose(
        controller.cpg_network.coupling_weights,
        np.array([[0.0, 5.0], [1.0, 0.0]]),
    )
    assert np.allclose(transformed_action.joint_angles, np.array([0.8, -1.6, 2.4]))
    assert np.array_equal(transformed_action.adhesion_onoff, action.adhesion_onoff)


def test_composite_applies_components_in_declared_order():
    log: list[str] = []
    perturbation = CompositePerturbation(
        components=(
            RecordingPerturbation("first", log, increment=1.0),
            RecordingPerturbation("second", log, increment=10.0),
        )
    )
    action = FakeAction(joint_angles=np.array([0.0]), adhesion_onoff=None)

    transformed = perturbation.apply_to_action(
        action, _context(expected_joint_angle_count=1)
    )

    assert log == ["first:action", "second:action"]
    assert np.array_equal(transformed.joint_angles, np.array([11.0]))


def test_composite_transformation_summaries_report_independent_scales():
    perturbation = CompositePerturbation(
        components=(
            CPGCouplingScalePerturbation(scale=0.75, name="coordination_proxy"),
            GlobalActionScalePerturbation(scale=0.8, name="motor_vigor_proxy"),
        )
    )
    metadata = perturbation.metadata()

    action_summary = summarize_action_transformation(
        controller_joint_angle_actions=np.array([[1.0, -2.0]]),
        applied_joint_angle_actions=np.array([[0.8, -1.6]]),
        controller_adhesion_onoff=np.array([[True, False, True, False, True, False]]),
        applied_adhesion_onoff=np.array([[True, False, True, False, True, False]]),
        expected_joint_angle_count=2,
        perturbation_metadata=metadata,
    )
    controller_summary = summarize_controller_transformation(
        pre_controller_state={
            "cpg_coupling_weights": np.array([[0.0, 4.0], [2.0, 0.0]])
        },
        post_controller_state={
            "cpg_coupling_weights": np.array([[0.0, 3.0], [1.5, 0.0]])
        },
        perturbation_metadata=metadata,
    )

    assert action_summary["expected_transform"] == "composite_global_action_scale"
    assert action_summary["effective_joint_angle_scale"] == 0.8
    assert action_summary["structural_checks"]["joint_angle_transform_matches_expected"][
        "pass"
    ]
    assert controller_summary["expected_transform"] == "composite_cpg_coupling_scale"
    assert controller_summary["effective_cpg_coupling_scale"] == 0.75
    assert controller_summary["structural_checks"][
        "cpg_coupling_transform_matches_expected"
    ]["pass"]


@dataclass
class RecordingPerturbation:
    name: str
    log: list[str]
    increment: float

    @property
    def perturbation_type(self) -> str:
        return "recording"

    def apply_to_config(self, config):
        self.log.append(f"{self.name}:config")
        return config

    def apply_to_controller(self, controller, context):
        self.log.append(f"{self.name}:controller")
        return controller

    def apply_to_action(self, action, context):
        self.log.append(f"{self.name}:action")
        return FakeAction(
            joint_angles=action.joint_angles + self.increment,
            adhesion_onoff=action.adhesion_onoff,
        )

    def metadata(self):
        return {
            "type": self.perturbation_type,
            "name": self.name,
            "parameters": {"increment": self.increment},
            "intervention_target": "unit_test_action",
            "intervention_stage": "unit_test",
            "deterministic": True,
        }


def _context(expected_joint_angle_count: int = 42) -> ActionPerturbationContext:
    return ActionPerturbationContext(
        condition_id="test",
        step_index=0,
        time_s=0.0,
        timestep_s=0.0001,
        random_seed=0,
        expected_joint_angle_count=expected_joint_angle_count,
    )


def _controller_context() -> ControllerPerturbationContext:
    return ControllerPerturbationContext(
        condition_id="test",
        timestep_s=0.0001,
        random_seed=0,
        expected_joint_angle_count=42,
    )
