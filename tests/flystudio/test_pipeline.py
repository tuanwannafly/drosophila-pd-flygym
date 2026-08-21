from drosophila_pd.flystudio.integration.pipeline import FlyStudioPipeline
from drosophila_pd.flystudio.integration.pipeline_examples import PipelineExamples

def test_pipeline_create():
    pkg = FlyStudioPipeline.create_project("test")
    assert pkg.metadata.name == "test"
    assert pkg.scene_data is not None

def test_pipeline_export_import(tmp_path):
    pkg = FlyStudioPipeline.create_project("test_export")
    filepath = str(tmp_path / "test.flystudio")

    FlyStudioPipeline.export_project(pkg, filepath)

    loaded = FlyStudioPipeline.import_project(filepath)
    assert loaded.metadata.name == "test_export"
    assert loaded.scene_data == pkg.scene_data

def test_pipeline_verify():
    pkg = FlyStudioPipeline.create_project("verify_me")
    report = FlyStudioPipeline.verify_integrity(pkg)
    assert report.is_valid is True

def test_pipeline_verify_warning():
    pkg = FlyStudioPipeline.create_project("verify_warn")
    pkg.scene_data = {}
    report = FlyStudioPipeline.verify_integrity(pkg)
    assert report.is_valid is True
    assert len(report.warnings) > 0
    assert "Scene data is empty." in report.warnings

def test_pipeline_verify_error():
    pkg = FlyStudioPipeline.create_project("")
    report = FlyStudioPipeline.verify_integrity(pkg)
    assert report.is_valid is False
    assert len(report.errors) > 0

def test_pipeline_examples(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    h = PipelineExamples.build_healthy()
    c = PipelineExamples.build_candidate()
    comp = PipelineExamples.build_comparison()

    assert h == "healthy.flystudio"
    assert c == "candidate.flystudio"
    assert comp == "comparison.flystudio"
