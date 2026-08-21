/** Connects shared Workspace frames to the existing viewer implementations. */
export class ViewerBridge {
    constructor({ workspace, threeViewer, viewportRenderer }) {
        this.workspace = workspace;
        this.threeViewer = threeViewer;
        this.viewportRenderer = viewportRenderer;
    }

    setFrame(frame = this.workspace.currentFrame) {
        const currentFrame = Number.isFinite(Number(frame))
            ? Math.round(Number(frame))
            : this.workspace.currentFrame;
        if (this.threeViewer?.digitalFly3D || this.threeViewer?.poseDocument) {
            this.threeViewer.setFrame(currentFrame);
        }
        this.viewportRenderer?.render();
        return currentFrame;
    }

    reset() {
        if (this.threeViewer?.digitalFly3D || this.threeViewer?.poseDocument) this.threeViewer.resetView();
        else this.viewportRenderer?.resetView?.();
    }

    focusSelection() {
        if (this.threeViewer?.digitalFly3D || this.threeViewer?.poseDocument) this.threeViewer.focusBodyPart();
        else this.viewportRenderer?.focusSelectedNode?.();
    }

    status() {
        return {
            loaded: Boolean(this.threeViewer?.poseDocument || this.threeViewer?.digitalFly3D || this.workspace.data?.nodes?.length),
            frame: this.workspace.currentFrame,
            totalFrames: this.workspace.totalFrames,
            selectedNode: this.workspace.selectedNode,
        };
    }
}
