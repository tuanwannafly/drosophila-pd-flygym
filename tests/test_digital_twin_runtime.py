"""Contract tests for the additive Digital Twin runtime module."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "web" / "digital_twin_runtime.js"
DOCS = ROOT / "docs" / "vi"


def test_digital_twin_runtime_contract_is_stream_and_input_driven() -> None:
    text = RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "export class DigitalTwinRuntime",
        "append_frame",
        "update(frame",
        "seek(frame",
        "reset()",
        "historyLimit",
        "frameCache",
        "trajectoryCache",
        "predictionBuffer",
        "predict_next_frame",
        "estimate_state",
        "interpolateFrame",
        "slerp",
        "setSpeed",
        "setLoop",
        "setReverse",
        "onChange",
    ):
        assert marker in text


def test_runtime_does_not_import_viewer_or_simulation_layers() -> None:
    text = RUNTIME.read_text(encoding="utf-8").lower()
    assert "flygym" not in text
    assert "three.js" not in text
    assert "from './viewer" not in text
    assert "import './dashboard" not in text


def test_digital_twin_runtime_documentation_exists() -> None:
    for name in (
        "100_Digital_Twin_Runtime.md",
        "101_Runtime_State.md",
        "102_Frame_Stream.md",
        "103_Runtime_API.md",
        "104_Future_AI.md",
    ):
        assert (DOCS / name).is_file()
