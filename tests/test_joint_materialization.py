from __future__ import annotations

import ast
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy import materialization


def test_expected_milestone_8b_constants_capture_materialization_transition():
    expected = materialization.EXPECTED_MILESTONE_8B

    assert expected["pre_skeleton_is_none"] is True
    assert expected["pre_jointdof_to_mjcfjoint_length"] == 0
    assert expected["pre_jointdof_to_neutralangle_length"] == 0
    assert expected["materialization_gate_used"] is True
    assert expected["materialized_joint_count"] == 204
    assert expected["post_skeleton_is_none"] is False
    assert expected["post_jointdof_to_mjcfjoint_length"] == 204
    assert expected["post_jointdof_to_neutralangle_length"] == 204
    assert expected["post_mjcf_root_joint_count"] == 204
    assert expected["post_actuator_mapping_total_length"] == 0


def test_add_joints_is_called_only_inside_explicit_materialization_gate():
    add_joints_calls = []
    forbidden_calls = {
        "add_actuators",
        "add_joint_sites",
        "add_leg_adhesion",
    }
    forbidden_violations = []

    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = CallVisitor(path)
        visitor.visit(tree)
        add_joints_calls.extend(visitor.add_joints_calls)
        for call in visitor.forbidden_calls:
            if call["name"] in forbidden_calls:
                forbidden_violations.append(call)

    expected_path = (
        REPO_ROOT / "src" / "drosophila_pd" / "anatomy" / "materialization.py"
    )
    assert len(add_joints_calls) == 1
    assert add_joints_calls[0]["path"] == expected_path
    assert add_joints_calls[0]["function"] == materialization.MATERIALIZATION_GATE_NAME
    assert add_joints_calls[0]["name"] == "add_joints"
    assert isinstance(add_joints_calls[0]["line"], int)
    assert forbidden_violations == []


def test_repository_code_does_not_assign_skeleton_directly():
    violations = []
    for path in _python_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = getattr(node, "targets", None) or [node.target]
                for target in targets:
                    if isinstance(target, ast.Attribute) and target.attr == "skeleton":
                        violations.append(f"{path}:{node.lineno} assigns skeleton")

    assert violations == []


def test_materialization_gate_rejects_unsafe_pre_state():
    fly = SafetyOnlyFly()
    materialization.assert_materialization_pre_state(fly)

    fly.skeleton = object()
    with pytest.raises(materialization.MaterializationSafetyError):
        materialization.assert_materialization_pre_state(fly)


def test_compare_milestone_8b_passes_for_expected_flat_values():
    observed = _observed_from_expected(materialization.EXPECTED_MILESTONE_8B)

    checks = materialization.compare_milestone_8b(observed)

    assert checks
    assert all(check["pass"] for check in checks.values())


def test_milestone_8b_integration_with_real_flygym_if_available():
    _skip_unless_exact_colab_like_runtime()

    fly = materialization.instantiate_neuromechfly()
    report = materialization.build_milestone_8b_materialization_report(
        fly, repo_root=REPO_ROOT
    )

    assert report["overall_pass"]
    assert report["observed"]["transition"]["skeleton_none_to_materialized"]
    assert report["observed"]["post"]["jointdof_to_mjcfjoint_length"] == 204

    with pytest.raises(materialization.MaterializationSafetyError):
        materialization.materialize_joints_explicit_gate(fly, fly.skeleton)


class CallVisitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.function_stack = []
        self.add_joints_calls = []
        self.forbidden_calls = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.function_stack.append(node.name)
        self.generic_visit(node)
        self.function_stack.pop()

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
            record = {
                "path": self.path,
                "line": node.lineno,
                "function": self.function_stack[-1] if self.function_stack else None,
                "name": name,
            }
            if name == "add_joints":
                self.add_joints_calls.append(record)
            else:
                self.forbidden_calls.append(record)
        self.generic_visit(node)


class SafetyOnlyRoot:
    joints = []
    actuators = []


class SafetyOnlyFly:
    def __init__(self):
        self.skeleton = None
        self.jointdof_to_mjcfjoint = {}
        self.jointdof_to_neutralangle = {}
        self.jointdof_to_mjcfactuator_by_type = {"MOTOR": {}}
        self.jointdof_to_neutralaction_by_type = {"MOTOR": {}}
        self.mjcf_root = SafetyOnlyRoot()


def _observed_from_expected(expected: dict[str, object]) -> dict[str, object]:
    return {
        "python_major_minor": expected["python_major_minor"],
        "flygym_version": expected["flygym_version"],
        "mujoco_version": expected["mujoco_version"],
        "fly_type": expected["fly_type"],
        "pre": {
            "skeleton_after_is_none": expected["pre_skeleton_is_none"],
            "jointdof_to_mjcfjoint_length": expected[
                "pre_jointdof_to_mjcfjoint_length"
            ],
            "jointdof_to_neutralangle_length": expected[
                "pre_jointdof_to_neutralangle_length"
            ],
            "actuator_mapping_total_length": expected[
                "pre_actuator_mapping_total_length"
            ],
            "neutralaction_mapping_total_length": expected[
                "pre_neutralaction_mapping_total_length"
            ],
            "mjcf_root_joint_count": expected["pre_mjcf_root_joint_count"],
            "mjcf_root_actuator_count": expected["pre_mjcf_root_actuator_count"],
        },
        "source": {
            "source_facts": {
                "changes_self_skeleton": expected[
                    "source_add_joints_changes_self_skeleton"
                ],
                "creates_mjcf_joints": expected[
                    "source_add_joints_creates_mjcf_joints"
                ],
                "populates_joint_mappings": expected[
                    "source_add_joints_populates_joint_mappings"
                ],
                "populates_neutral_angle_mapping": expected[
                    "source_add_joints_populates_neutral_angle_mapping"
                ],
                "rebuilds_neutral_keyframes": expected[
                    "source_add_joints_rebuilds_neutral_keyframes"
                ],
            }
        },
        "materialization": {
            "created_joint_count": expected["materialized_joint_count"]
        },
        "post": {
            "skeleton_is_none": expected["post_skeleton_is_none"],
            "skeleton_is_materialized_skeleton": expected[
                "post_skeleton_is_materialized_skeleton"
            ],
            "skeleton_type": expected["post_skeleton_type"],
            "body_segment_count": expected["post_body_segment_count"],
            "anatomical_joint_count": expected["post_anatomical_joint_count"],
            "jointdof_count": expected["post_jointdof_count"],
            "axis_counts": expected["post_axis_counts"],
            "jointdof_unique_name_count": expected[
                "post_jointdof_unique_name_count"
            ],
            "bodyseg_to_mjcfbody_length": expected[
                "post_bodyseg_to_mjcfbody_length"
            ],
            "missing_parent_mjcf_body_count": expected[
                "post_missing_parent_mjcf_body_count"
            ],
            "missing_child_mjcf_body_count": expected[
                "post_missing_child_mjcf_body_count"
            ],
            "jointdof_to_mjcfjoint_length": expected[
                "post_jointdof_to_mjcfjoint_length"
            ],
            "jointdof_to_neutralangle_length": expected[
                "post_jointdof_to_neutralangle_length"
            ],
            "mjcf_root_joint_count": expected["post_mjcf_root_joint_count"],
            "joint_mapping_names_match_skeleton": expected[
                "post_joint_mapping_names_match_skeleton"
            ],
            "neutralangle_names_match_skeleton": expected[
                "post_neutralangle_names_match_skeleton"
            ],
            "created_joint_names_match_skeleton": expected[
                "post_created_joint_names_match_skeleton"
            ],
            "mjcf_joint_names_match_skeleton": expected[
                "post_mjcf_joint_names_match_skeleton"
            ],
            "all_neutral_angles_zero": expected["post_all_neutral_angles_zero"],
            "actuator_mapping_total_length": expected[
                "post_actuator_mapping_total_length"
            ],
            "neutralaction_mapping_total_length": expected[
                "post_neutralaction_mapping_total_length"
            ],
            "mjcf_root_actuator_count": expected["post_mjcf_root_actuator_count"],
        },
        "transition": {
            "materialization_gate_used": expected["materialization_gate_used"],
            "skeleton_none_to_materialized": expected[
                "transition_skeleton_none_to_materialized"
            ],
            "joint_mapping_delta": expected["transition_joint_mapping_delta"],
            "neutralangle_mapping_delta": expected[
                "transition_neutralangle_mapping_delta"
            ],
            "mjcf_root_joint_delta": expected["transition_mjcf_root_joint_delta"],
            "actuator_mapping_delta": expected["transition_actuator_mapping_delta"],
            "neutralaction_mapping_delta": expected[
                "transition_neutralaction_mapping_delta"
            ],
            "mjcf_root_actuator_delta": expected[
                "transition_mjcf_root_actuator_delta"
            ],
        },
    }


def _python_sources() -> list[Path]:
    return sorted((REPO_ROOT / "src").rglob("*.py")) + sorted(
        (REPO_ROOT / "scripts").rglob("*.py")
    )


def _skip_unless_exact_colab_like_runtime() -> None:
    try:
        flygym_version = version("flygym")
        mujoco_version = version("mujoco")
    except PackageNotFoundError:
        pytest.skip("FlyGym/MuJoCo integration is verified in Colab.")

    if sys.version_info[:2] != (3, 12):
        pytest.skip("Milestone 8B integration expects Python 3.12.")
    if flygym_version != "2.1.0" or mujoco_version != "3.9.0":
        pytest.skip("Milestone 8B integration expects FlyGym 2.1.0 and MuJoCo 3.9.0.")
