from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy import orientation


def test_source_inspection_identifies_add_joints_materialization_boundary():
    source = """
    def add_joints(self, skeleton):
        self.skeleton = skeleton
        return_dict = {}
        for jointdof in skeleton.iter_jointdofs(self.root_segment):
            child_body = self.bodyseg_to_mjcfbody[jointdof.child]
            self.jointdof_to_neutralangle[jointdof] = 0.0
            return_dict[jointdof] = child_body.add_joint(name=jointdof.name)
        self.jointdof_to_mjcfjoint.update(return_dict)
        self._rebuild_neutral_keyframe()
        return return_dict
    """

    facts = orientation.inspect_add_joints_source_text(source)

    assert facts["parse_error"] is None
    assert facts["changes_self_skeleton"]
    assert facts["creates_mjcf_joints"]
    assert facts["populates_joint_mappings"]
    assert facts["populates_neutral_angle_mapping"]
    assert facts["rebuilds_neutral_keyframes"]


def test_mapping_container_summary_counts_nested_lengths():
    mapping = {
        "MOTOR": {},
        "POSITION": {"joint_a": object(), "joint_b": object()},
    }

    summary = orientation.mapping_container_summary(
        "jointdof_to_mjcfactuator_by_type", mapping
    )

    assert summary["length"] == 2
    assert summary["nested_lengths"] == {"MOTOR": 0, "POSITION": 2}
    assert summary["nested_total_length"] == 2


def test_orientation_safety_rejects_initialized_skeleton():
    class FlyLike:
        skeleton = object()

    with pytest.raises(orientation.OrientationSafetyError):
        orientation.assert_orientation_pre_materialized(FlyLike(), phase="test")


def test_collect_orientation_with_fake_fly_does_not_call_add_joints():
    fly = FakeNeuroMechFly()

    observed = orientation.collect_block_8_13_orientation(fly)

    assert not fly.add_joints_called
    assert fly.skeleton is None
    assert observed["skeleton_before_is_none"]
    assert observed["skeleton_after_is_none"]
    assert observed["add_joints_found"]
    assert observed["add_joints_changes_self_skeleton"]
    assert observed["add_joints_creates_mjcf_joints"]
    assert observed["add_joints_populates_joint_mappings"]
    assert observed["add_joints_populates_neutral_angle_mapping"]
    assert observed["add_joints_rebuilds_neutral_keyframes"]
    assert "mjcf_root" in observed["mjcf_root_object_names"]
    assert observed["mapping_containers"]["jointdof_to_mjcfjoint"]["length"] == 0


def test_compare_block_8_13_orientation_passes_for_expected_observations():
    observed = dict(orientation.EXPECTED_BLOCK_8_13_ORIENTATION)

    checks = orientation.compare_block_8_13_orientation(observed)

    assert checks
    assert all(check["pass"] for check in checks.values())


class FakeBaseFly:
    def __init__(self):
        self.skeleton = None
        self._mjcf_root = object()
        self.bodyseg_to_mjcfbody = {f"body_{i}": object() for i in range(69)}
        self.bodyseg_to_mjcfgeom = {}
        self.bodyseg_to_mjcfmesh = {}
        self.jointdof_to_mjcfjoint = {}
        self.jointdof_to_mjcfactuator_by_type = {"MOTOR": {}, "POSITION": {}}
        self.jointdof_to_neutralangle = {}
        self.jointdof_to_neutralaction_by_type = {"MOTOR": {}, "POSITION": {}}
        self.anatomicaljoint_to_mjcfsites = {}
        self.leg_to_adhesionactuator = {}
        self.sensorname_to_mjcfsensor = {}
        self.cameraname_to_mjcfcamera = {}
        self.eyecameraname_to_mjcfcamera = {}
        self.root_segment = "c_thorax"
        self.add_joints_called = False

    @property
    def mjcf_root(self):
        return self._mjcf_root

    def get_jointdofs_order(self):
        return list(self.jointdof_to_mjcfjoint)

    def add_joints(self, skeleton):
        self.add_joints_called = True
        self.skeleton = skeleton
        return_dict = {}
        for jointdof in skeleton.iter_jointdofs(self.root_segment):
            child_body = self.bodyseg_to_mjcfbody[jointdof.child]
            self.jointdof_to_neutralangle[jointdof] = 0.0
            return_dict[jointdof] = child_body.add_joint(name=jointdof.name)
        self.jointdof_to_mjcfjoint.update(return_dict)
        self._rebuild_neutral_keyframe()
        return return_dict

    def _rebuild_neutral_keyframe(self):
        pass


class FakeNeuroMechFly(FakeBaseFly):
    pass
