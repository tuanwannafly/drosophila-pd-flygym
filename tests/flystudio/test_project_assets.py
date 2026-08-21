from drosophila_pd.flystudio.project_assets import ProjectAssets

def test_project_assets():
    proj = ProjectAssets(project_name="TestProject")
    assert proj.project_name == "TestProject"
    assert proj.database is not None
    assert len(proj.root_directories) == 0
