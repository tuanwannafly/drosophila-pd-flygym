"""Run the complete FlyGym rollout-to-static-viewer workflow."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
SCRIPT_ROOT = REPOSITORY_ROOT / "scripts"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

for _stream in (sys.stdout, sys.stderr):
    if _stream is not None and hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from build_viewer_bundle import ViewerBundleError, build_bundle  # noqa: E402
from drosophila_pd.viewer_export.discovery import (  # noqa: E402
    find_latest_bundle,
    find_latest_rollout,
    find_latest_viewer_pose,
)


DEFAULT_DATASET_DIR = REPOSITORY_ROOT / "datasets" / "healthy" / "Healthy_001"
DEFAULT_DIST_DIR = REPOSITORY_ROOT / "dist"
DEFAULT_CONFIG = REPOSITORY_ROOT / "configs" / "v2" / "flygym" / "healthy.yaml"


class DemoError(RuntimeError):
    """Raised when the end-to-end demo cannot complete."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rollout_payload(path: Path) -> tuple[dict[str, Any], list[Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DemoError(f"Unable to read rollout JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise DemoError(f"Rollout JSON must contain an object: {path}")
    data = payload.get("rollout") if isinstance(payload.get("rollout"), dict) else payload
    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        raise DemoError(f"Rollout JSON contains no frames: {path}")
    return data, frames


def _has_npz(dataset_dir: Path) -> Path | None:
    for name in ("rollout.npz", "rollout_arrays.npz"):
        path = dataset_dir / name
        if path.is_file():
            return path
    return None


def _ensure_legacy_npz_alias(dataset_dir: Path) -> Path:
    canonical = dataset_dir / "rollout.npz"
    if canonical.is_file():
        return canonical
    legacy = dataset_dir / "rollout_arrays.npz"
    if legacy.is_file():
        shutil.copy2(legacy, canonical)
        return canonical
    raise DemoError(f"No rollout NPZ found under {dataset_dir}")


def _write_metadata_and_manifest(dataset_dir: Path, data: dict[str, Any], frames: list[Any]) -> None:
    metadata_path = dataset_dir / "metadata.json"
    if not metadata_path.is_file():
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.is_file():
        return
    files = {}
    for path in sorted(dataset_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            files[path.name] = {
                "path": path.name,
                "byte_size": path.stat().st_size,
                "sha256": _sha256(path),
            }
    manifest = {
        "schema_version": data.get("schema_version", "flygym-rollout-1"),
        "created_at": datetime.now(UTC).isoformat(),
        "frame_count": len(frames),
        "files": files,
        "metadata": data.get("metadata", {}),
        "scientific_scope": (
            "Recorded FlyGym observations and software provenance only; "
            "not biological validation."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _missing_simulation_modules() -> list[str]:
    return [
        name
        for name in ("flygym", "mujoco", "flygym_demo")
        if importlib.util.find_spec(name) is None
    ]


def _install_simulation_dependencies() -> None:
    print("Simulation dependencies are missing; installing .[simulation] ...", flush=True)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-e",
                ".[simulation]",
            ],
            cwd=REPOSITORY_ROOT,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise DemoError(
            "Installing the simulation dependencies timed out. "
            "Use the documented Python 3.12 environment and install .[simulation] first."
        ) from exc
    if result.returncode != 0:
        raise DemoError(
            "Unable to install the pinned simulation dependencies. "
            "Use Python 3.12 and run `python -m pip install -e .[simulation]`."
        )


def _ensure_simulation_dependencies(*, allow_install: bool) -> None:
    missing = _missing_simulation_modules()
    if missing and allow_install:
        if sys.version_info[:2] != (3, 12):
            names = ", ".join(missing)
            raise DemoError(
                f"FlyGym simulation dependencies are unavailable: {names}. "
                "Automatic installation is restricted to the project's Python 3.12 runtime; "
                "run this workflow in Python 3.12."
            )
        _install_simulation_dependencies()
        missing = _missing_simulation_modules()
    if missing:
        names = ", ".join(missing)
        raise DemoError(
            f"FlyGym simulation dependencies are unavailable: {names}. "
            "Run this workflow in the documented Python 3.12 simulation environment."
        )


def _run_simulation(dataset_dir: Path, steps: int) -> None:
    from drosophila_pd.flygym_adapter import (
        FlyGymAdapter,
        FlyGymConfig,
        FlyGymRuntime,
        RolloutRecorder,
        export_rollout,
    )

    if not DEFAULT_CONFIG.is_file():
        raise DemoError(f"Healthy FlyGym configuration was not found: {DEFAULT_CONFIG}")
    config = FlyGymConfig.from_yaml(DEFAULT_CONFIG)
    adapter = FlyGymAdapter()
    simulation = None
    try:
        fly = adapter.create_fly(config.fly)
        world = adapter.create_world(config.world)
        adapter.attach_fly(
            world,
            fly,
            position=config.world.spawn_position,
            orientation=config.world.spawn_orientation,
            add_ground_contact_sensors=config.world.add_ground_contact_sensors,
        )
        simulation = adapter.create_simulation(world, config.simulation)
        simulation.reset()
        timestep = float(getattr(simulation, "timestep", config.simulation.timestep or 0.0))
        recorder = RolloutRecorder(
            simulation,
            fly.name,
            fly=fly,
            timestep=timestep,
            simulation_metadata={
                "dataset_id": "Healthy_001",
                "timestep_s": timestep,
                "source": "scripts/run_demo.py",
                "configuration": config.to_mapping(),
            },
        )
        runtime = FlyGymRuntime(simulation, recorder=recorder, max_steps=steps)
        rollout = runtime.run()
        if rollout is None or rollout.frame_count <= 0:
            raise DemoError("Simulation completed without recorded rollout frames.")
        export_rollout(rollout, dataset_dir)
    except Exception as exc:
        if isinstance(exc, DemoError):
            raise
        raise DemoError(f"FlyGym simulation failed: {exc}") from exc
    finally:
        close = getattr(simulation, "close", None)
        if callable(close):
            close()


def _ensure_rollout(dataset_dir: Path, *, steps: int, allow_install: bool) -> bool:
    rollout_json = dataset_dir / "rollout.json"
    npz = _has_npz(dataset_dir)
    if rollout_json.is_file() and npz is not None:
        data, frames = _rollout_payload(rollout_json)
        _ensure_legacy_npz_alias(dataset_dir)
        _write_metadata_and_manifest(dataset_dir, data, frames)
        return False

    _ensure_simulation_dependencies(allow_install=allow_install)
    _run_simulation(dataset_dir, steps)
    data, frames = _rollout_payload(rollout_json)
    _ensure_legacy_npz_alias(dataset_dir)
    _write_metadata_and_manifest(dataset_dir, data, frames)
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=100, help="Simulation steps for a new rollout.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--dist-dir", type=Path, default=DEFAULT_DIST_DIR)
    parser.add_argument(
        "--no-install-simulation",
        action="store_true",
        help="Do not attempt to install missing FlyGym/MuJoCo dependencies.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.steps < 0:
        print("Demo error: --steps must be non-negative.", file=sys.stderr)
        return 2
    dataset_dir = args.dataset_dir.expanduser().resolve()
    dist_dir = args.dist_dir.expanduser().resolve()
    web_root = REPOSITORY_ROOT / "web"
    try:
        if not web_root.is_dir():
            raise DemoError(f"Web viewer directory was not found: {web_root}")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dist_dir.mkdir(parents=True, exist_ok=True)
        generated = _ensure_rollout(
            dataset_dir,
            steps=args.steps,
            allow_install=not args.no_install_simulation,
        )
        print("✓ Simulation completed" + ("" if generated else " (existing rollout reused)"))

        rollout_json = dataset_dir / "rollout.json"
        rollout_npz = _ensure_legacy_npz_alias(dataset_dir)
        manifest = dataset_dir / "manifest.json"
        metadata = dataset_dir / "metadata.json"
        if not all(path.is_file() for path in (rollout_json, rollout_npz, manifest, metadata)):
            raise DemoError("Rollout package is incomplete after export.")
        print("✓ Rollout exported")

        from drosophila_pd.viewer_export import export_viewer_pose, validate_pose_document

        pose_path = dataset_dir / "viewer_pose.json"
        pose_result = export_viewer_pose(dataset_dir, pose_path)
        if not pose_result.validation.overall_pass:
            raise DemoError(str(pose_result.validation.as_dict()))
        validate_pose_document(pose_result.document)
        print("✓ Viewer pose exported")

        bundle_archive = dist_dir / "viewer_bundle.zip"
        bundle_dir, bundle_archive, _ = build_bundle(
            pose_path,
            output=bundle_archive,
            web_root=web_root,
        )
        if not bundle_dir.is_dir() or not bundle_archive.is_file():
            raise DemoError("Viewer bundle was not created.")
        print("✓ Viewer bundle built")

        required = (rollout_json, rollout_npz, pose_path, manifest, bundle_archive)
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise DemoError("Required artifacts are missing: " + ", ".join(missing))
        latest_pose = find_latest_viewer_pose(dataset_dir) or find_latest_viewer_pose(REPOSITORY_ROOT)
        latest_rollout = find_latest_rollout(dataset_dir) or find_latest_rollout(REPOSITORY_ROOT)
        latest_bundle = find_latest_bundle(dist_dir) or find_latest_bundle(REPOSITORY_ROOT)
        if latest_pose is None or latest_rollout is None or latest_bundle is None:
            raise DemoError("Artifact discovery could not find the completed outputs.")
        print("✓ Ready to deploy")
        print(f"Rollout: {rollout_json}")
        print(f"Viewer pose: {pose_path}")
        print(f"Viewer bundle: {bundle_archive}")
        return 0
    except (DemoError, ViewerBundleError, FileNotFoundError, OSError, TypeError, ValueError) as exc:
        print(f"Demo error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
