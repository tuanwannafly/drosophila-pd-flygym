/** Selection bridge. Workspace remains the only selection source of truth. */
export class SelectionBridge {
    constructor(workspace, eventBus) {
        this.workspace = workspace;
        this.eventBus = eventBus;
    }

    selectNode(node) {
        const selected = this.workspace.selectNode(node);
        this.emit('node', selected);
        return selected;
    }

    syncFromWorkspace() {
        this.emit('node', this.workspace.selectedNode);
        this.emit('keyframe', this.workspace.selectedKeyframe);
    }

    selectKeyframe(keyframe, frame, sourceIndex = null) {
        const selected = this.workspace.selectKeyframe(keyframe, frame, sourceIndex);
        this.emit('keyframe', selected);
        return selected;
    }

    clear() {
        this.workspace.clearKeyframeSelection();
        this.emit('keyframe', null);
    }

    emit(kind, value) {
        this.eventBus.emit(`selection:${kind}`, {
            value,
            workspace: this.workspace,
        });
    }
}
