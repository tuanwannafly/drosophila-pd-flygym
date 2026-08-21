export class ProjectLoader {
    constructor() {
        this.currentProject = null;
    }

    loadProject(projectId) {
        console.log("Loading project:", projectId);
        this.currentProject = projectId;
    }
}
