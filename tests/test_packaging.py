"""Packaging contract tests; no scientific module is exercised here."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

import drosophila_pd


def test_top_level_import_and_module_entry_point():
    assert drosophila_pd.__version__
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-m", "drosophila_pd"],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "drosophila-pd-flygym" in result.stdout
    assert drosophila_pd.__version__ in result.stdout


def test_editable_install_metadata_is_available():
    package = distribution("drosophila-pd-flygym")
    assert package.version == drosophila_pd.__version__
    direct_url = package.read_text("direct_url.json")
    assert direct_url is not None
    assert json.loads(direct_url)["dir_info"]["editable"] is True
