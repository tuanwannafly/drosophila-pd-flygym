from drosophila_pd.flystudio.exchange import ProjectPackage, ProjectMetadata, Version, PackageBuilder, PackageLoader
from .pipeline_validator import PipelineValidator
from .pipeline_report import PipelineReport

class FlyStudioPipeline:
    @staticmethod
    def create_project(name: str) -> ProjectPackage:
        meta = ProjectMetadata(name=name, version=Version(1, 0, 0))
        pkg = ProjectPackage(metadata=meta)
        pkg.scene_data = {"nodes": [{"type": "root", "children": []}]}
        pkg.viewer_data = {"layout": "default"}
        pkg.playback_data = {"fps": 60, "frames": 0}
        pkg.assets["model_metadata.txt"] = b"Mock asset for integration"
        return pkg

    @staticmethod
    def export_project(pkg: ProjectPackage, filepath: str) -> None:
        data = PackageBuilder.build(pkg)
        with open(filepath, 'wb') as f:
            f.write(data)

    @staticmethod
    def import_project(filepath: str) -> ProjectPackage:
        with open(filepath, 'rb') as f:
            data = f.read()
        return PackageLoader.load(data)

    @staticmethod
    def verify_integrity(pkg: ProjectPackage) -> PipelineReport:
        return PipelineValidator.validate_package(pkg)
