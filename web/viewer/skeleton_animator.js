/** Select imported frames for a viewer without changing the source document. */

export class SkeletonAnimator {
    constructor(poseDocument = null) {
        this.poseDocument = null;
        this.currentFrame = 0;
        if (poseDocument) this.setPoseDocument(poseDocument);
    }

    setPoseDocument(poseDocument) {
        this.poseDocument = poseDocument;
        this.currentFrame = 0;
        return this;
    }

    get frameCount() {
        return this.poseDocument?.frame_count ?? 0;
    }

    frameAt(frame = this.currentFrame) {
        if (!this.poseDocument?.frames?.length) return null;
        const index = Math.max(0, Math.min(this.frameCount - 1, Math.trunc(frame)));
        this.currentFrame = index;
        return this.poseDocument.frames[index];
    }

    clear() {
        this.poseDocument = null;
        this.currentFrame = 0;
    }
}
