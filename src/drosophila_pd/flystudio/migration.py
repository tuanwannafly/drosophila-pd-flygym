from .project_package import ProjectPackage

class Migration:
    @staticmethod
    def migrate(pkg: ProjectPackage) -> None:
        """Forward-compatibility migration layer."""
        if pkg.metadata.version.major < 2:
            pkg.metadata.custom_data["migrated_from_v1"] = True
