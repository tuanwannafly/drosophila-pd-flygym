from .pipeline import FlyStudioPipeline

class PipelineExamples:
    @staticmethod
    def build_healthy() -> str:
        pkg = FlyStudioPipeline.create_project("healthy")
        filepath = "healthy.flystudio"
        FlyStudioPipeline.export_project(pkg, filepath)
        return filepath

    @staticmethod
    def build_candidate() -> str:
        pkg = FlyStudioPipeline.create_project("candidate")
        filepath = "candidate.flystudio"
        FlyStudioPipeline.export_project(pkg, filepath)
        return filepath

    @staticmethod
    def build_comparison() -> str:
        pkg = FlyStudioPipeline.create_project("comparison")
        filepath = "comparison.flystudio"
        FlyStudioPipeline.export_project(pkg, filepath)
        return filepath
