export class Viewer {
    constructor() {
        this.container = null;
        this.showSkeleton = true;
        this.showTrajectory = true;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div style="color: white; padding: 20px; font-family: monospace;">
                [Viewer Placeholder]<br>
                Skeleton: ${this.showSkeleton ? 'ON' : 'OFF'}<br>
                Trajectory: ${this.showTrajectory ? 'ON' : 'OFF'}
            </div>
        `;
    }

    toggleSkeleton() {
        this.showSkeleton = !this.showSkeleton;
        this.render();
    }

    toggleTrajectory() {
        this.showTrajectory = !this.showTrajectory;
        this.render();
    }
}
