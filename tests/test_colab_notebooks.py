"""Static contract tests for the Google Colab research workspace."""

from __future__ import annotations

import json
import re
from pathlib import Path


COLAB_DIR = Path(__file__).parents[1] / "notebooks" / "colab"
NOTEBOOK_NAMES = [
    "00_Environment_Setup.ipynb",
    "01_FlyGym_API_Explorer.ipynb",
    "02_Create_First_Fly.ipynb",
    "03_Run_First_Simulation.ipynb",
    "04_Record_Rollout.ipynb",
    "05_Generate_Healthy_001.ipynb",
    "06_Inspect_Dataset.ipynb",
    "07_Run_Project_Pipeline.ipynb",
    "08_Visualization.ipynb",
    "09_Validation.ipynb",
    "10_End_to_End.ipynb",
]
REQUIRED_MARKDOWN = (
    "Objective",
    "Prerequisites",
    "Expected Output",
    "Troubleshooting",
    "Validation",
    "Next notebook",
)
LOCAL_PATH = re.compile(r"(?:(?<![A-Za-z0-9_-])[A-Za-z]:[\\/]|/home/runner|/Users/)")
FORBIDDEN_MAGIC = re.compile(r"(?m)^\s*(?:%%|%(?:cd|pip|conda)\b|#\s*vscode)")


def _load_notebook(name: str) -> dict:
    path = COLAB_DIR / name
    assert path.is_file(), f"Missing Colab notebook: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_colab_workspace_contains_expected_notebooks() -> None:
    assert sorted(path.name for path in COLAB_DIR.glob("*.ipynb")) == sorted(NOTEBOOK_NAMES)


def test_colab_notebooks_have_valid_structure_and_metadata() -> None:
    for name in NOTEBOOK_NAMES:
        notebook = _load_notebook(name)
        assert notebook["nbformat"] == 4
        assert isinstance(notebook["cells"], list)
        assert notebook["metadata"]["kernelspec"]["name"] == "python3"
        assert "colab" in notebook["metadata"]
        assert notebook["metadata"]["colab"]["name"] == name
        for cell in notebook["cells"]:
            assert cell["cell_type"] in {"markdown", "code"}
            assert isinstance(cell["source"], list)


def test_colab_notebooks_document_run_all_contract() -> None:
    for name in NOTEBOOK_NAMES:
        notebook = _load_notebook(name)
        markdown = "\n".join(
            "".join(cell["source"])
            for cell in notebook["cells"]
            if cell["cell_type"] == "markdown"
        )
        for heading in REQUIRED_MARKDOWN:
            assert heading in markdown, f"{name} lacks {heading!r}"


def test_colab_notebooks_are_portable() -> None:
    for name in NOTEBOOK_NAMES:
        notebook = _load_notebook(name)
        source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
        assert not LOCAL_PATH.search(source), f"{name} contains a local absolute path"
        assert not FORBIDDEN_MAGIC.search(source), f"{name} contains unsupported notebook magic"


def test_end_to_end_bundle_step_is_cwd_independent() -> None:
    notebook = _load_notebook("10_End_to_End.ipynb")
    source = "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert "str(repo / \"scripts\" / \"build_viewer_bundle.py\")" in source
    assert "cwd=str(repo)" in source
    assert "str(repo / \"web\")" in source
    assert "capture_output=True" in source
    assert "start = Path.cwd().resolve()" in source
    assert "start.parents" in source
    assert "def is_repo_root(path):" in source
    assert "def _bundle_repo_candidates(seed):" in source
    assert "globals().get(\"viewer_pose_path\")" in source
    assert "bundle_repo = None" in source
