from drosophila_pd.flystudio.camera_panel import CameraPanel, CameraPreset

def test_camera_panel():
    panel = CameraPanel()
    preset = CameraPreset(name="front", target="head", zoom=2.0)

    panel.apply_preset(preset)
    assert panel.current_preset.name == "front"
    assert panel.current_preset.target == "head"
    assert panel.current_preset.zoom == 2.0
