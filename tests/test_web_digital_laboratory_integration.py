"""Static contracts for the additive Digital Laboratory integration shell."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
DASHBOARD = WEB / "dashboard"


def test_dashboard_integration_modules_exist() -> None:
    for filename in (
        "integration.js",
        "state.js",
        "selection.js",
        "event_bus.js",
        "sync.js",
        "viewer_bridge.js",
        "analysis_bridge.js",
        "report_bridge.js",
        "assistant_bridge.js",
    ):
        text = (DASHBOARD / filename).read_text(encoding="utf-8")
        assert "export" in text


def test_dashboard_uses_existing_workspace_and_viewer_apis() -> None:
    integration = (DASHBOARD / "integration.js").read_text(encoding="utf-8")
    viewer_bridge = (DASHBOARD / "viewer_bridge.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")

    for tab in ("Home", "Datasets", "Viewer", "Analysis", "Validation", "Reports", "Publication", "Plugins", "Assistant"):
        assert tab in integration
    assert "new WorkspaceSync" in integration
    assert "new ViewerBridge" in integration
    assert "this.workspace.load({" in app
    assert "this.threeViewer.loadPose(rawData)" in app
    assert "setFrame" in viewer_bridge


def test_integration_does_not_add_simulation_or_scientific_runtime() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in DASHBOARD.glob("*.js"))
    for forbidden in ("mujoco", "runSimulation", "simulate"):
        assert forbidden not in source.lower()
