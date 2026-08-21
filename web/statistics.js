export class Statistics {
    constructor() {
        this.fps = 0;
        this.frameCount = 0;
    }

    update(fps) {
        this.fps = fps;
        this.frameCount++;
    }

    getStats() {
        return {
            fps: this.fps,
            frames: this.frameCount
        };
    }
}
