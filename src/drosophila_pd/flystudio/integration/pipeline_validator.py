from drosophila_pd.flystudio.exchange import ProjectPackage, PackageValidator
from .pipeline_report import PipelineReport

class PipelineValidator:
    @staticmethod
    def validate_package(pkg: ProjectPackage) -> PipelineReport:
        report = PipelineReport(project_name=pkg.metadata.name, is_valid=True)
        errors = PackageValidator.validate(pkg)
        for err in errors:
            report.log_error(err)

        if not pkg.scene_data:
            report.log_warning("Scene data is empty.")

        return report
