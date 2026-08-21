from __future__ import annotations

from pathlib import Path
import sys
from zipfile import ZipFile

import pytest


pytest.importorskip("docx")
pytest.importorskip("reportlab")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_final_report import (  # noqa: E402
    DOCX_NAME,
    EXPECTED_FIGURES,
    PDF_NAME,
    REPO_ROOT,
    SOURCE_COMMIT,
    build,
    validate_source,
)


def test_final_report_source_and_assets_are_valid() -> None:
    title, blocks = validate_source(REPO_ROOT / "docs" / "report" / "final_report.md")
    assert title.startswith("Reproducible Computational Drosophila")
    assert blocks
    assert all((REPO_ROOT / path).exists() for path in EXPECTED_FIGURES)


def test_final_report_builds_both_provenance_tagged_outputs(tmp_path: Path) -> None:
    docx_path, pdf_path = build(output_dir=tmp_path)
    assert docx_path.name == DOCX_NAME
    assert pdf_path.name == PDF_NAME
    assert docx_path.stat().st_size > 0
    assert pdf_path.stat().st_size > 0
    with ZipFile(docx_path) as archive:
        assert SOURCE_COMMIT.encode() in archive.read("word/document.xml")
        assert SOURCE_COMMIT.encode() in archive.read("docProps/core.xml")
    assert SOURCE_COMMIT.encode() in pdf_path.read_bytes()
