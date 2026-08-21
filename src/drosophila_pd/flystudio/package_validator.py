from .project_package import ProjectPackage

class PackageValidator:
    @staticmethod
    def validate(pkg: ProjectPackage) -> list[str]:
        errors = []
        if not pkg.metadata.name:
            errors.append("Missing project name")
        if not pkg.scene_data and not pkg.viewer_data and not pkg.playback_data:
            errors.append("Package contains no active data payload")
        return errors
