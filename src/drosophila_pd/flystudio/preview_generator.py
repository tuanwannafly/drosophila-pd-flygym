from .project_package import ProjectPackage
from .thumbnail_generator import ThumbnailGenerator

class PreviewGenerator:
    @staticmethod
    def generate(pkg: ProjectPackage) -> None:
        if pkg.preview_image is None:
            pkg.preview_image = ThumbnailGenerator.generate_placeholder()
